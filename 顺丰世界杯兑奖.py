# 当前脚本来自于 http://script.345yun.cn 脚本库下载！
# 当前脚本来自于 http://2.345yun.cn 脚本库下载！
# 当前脚本来自于 http://2.345yun.cc 脚本库下载！
# 脚本库官方QQ群1群: 429274456
# 脚本库官方QQ群2群: 1077801222
# 脚本库官方QQ群3群: 433030897
# 脚本库中的所有脚本文件均来自热心网友上传和互联网收集。
# 脚本库仅提供文件上传和下载服务，不提供脚本文件的审核。
# 您在使用脚本库下载的脚本时自行检查判断风险。
# 所涉及到的 账号安全、数据泄露、设备故障、软件违规封禁、财产损失等问题及法律风险，与脚本库无关！均由开发者、上传者、使用者自行承担。

"""

====================================================================
 顺丰2026世界杯 - 金豆兑奖脚本（独立脚本）
====================================================================

【功能】
  1. 登录账号（cookie方式）
  2. 查询奖池，获取所有可兑换奖品及库存状态
  3. 按选择的奖品逐个兑换（prizeDraw 接口）
  4. 实物奖品（productType=SFM）→ 自动查地址簿并填写收货地址
  5. 虚拟券（productType=SFC）→ 直接提示兑换成功

【环境变量】
  sfsyUrl          账号cookie，多个账号用 & 分隔（必填）
  SF_PROXY_API_URL 代理API地址（可选，不配则直连）
  SFBF             并发数量（可选，默认1，最大20）

【基本用法】
  python3 顺丰世界杯兑奖.py

  启动后会显示兑换项列表，交互选择：
    - 输入序号选择（如 1,3,5 选第1、3、5项）
    - 输入 a      兑换所有券类（5元/12元/23元寄件券）
    - 输入 all    兑换全部（含实物）
    - 直接回车    用配置表 EXCHANGE_ITEMS 里 enabled=True 的项
    - 输入 q      退出

【配置说明】（脚本开头）

  1. EXCHANGE_ITEMS —— 兑换项配置表
     每项有 enabled 字段：
       True  = 兑换（按 limitLotteryNum 次数循环兑换）
       False = 跳过
     可直接修改 enabled 开关，不交互直接跑就用这些配置。

  2. EXCLUDE_PHONES —— 排除手机号
     在此集合中的手机号不参与兑奖（跳过整个账号）。
     例: EXCLUDE_PHONES = {'18036367171'}

  3. PHONE_OVERRIDE —— 单独指定某账号兑换哪些项
     为特定手机号单独指定兑换项，覆盖全局选择。
     例: PHONE_OVERRIDE = {
         '17606197000': {'5元寄件券', '12元寄件券'},
     }

  4. EXCHANGE_ADDRESS_INDEX —— 地址簿选择
     实物奖品填写地址时，使用地址簿中第几个地址（0=第一个）。

【按账号控制兑换的三种方式】

  方式一：排除某些账号
    EXCLUDE_PHONES = {'18036367171'}
    → 该手机号登录后直接跳过，不兑换任何东西

  方式二：给特定账号单独配置
    PHONE_OVERRIDE = {
        '17606197000': {'5元寄件券'},        # 只兑5元券
        '16651383977': {'12元寄件券', '23元免单券'},  # 只兑12元和23元
    }
    → 全局选择对这几个手机号无效，用各自指定的项

  方式三：全局交互选择
    运行时输入序号，所有未被排除、未在 PHONE_OVERRIDE 中的账号
    都按此选择兑换

  优先级：PHONE_OVERRIDE > 交互选择 > EXCHANGE_ITEMS.enabled

【兑换项完整参数表】（从抓包提取）

  序号  奖品             金豆  类型  限兑   ruleCode
  1    大疆云台相机      4000  实物  1次   RC2071521968535695360
  2    黄金足球金币      3000  实物  1次   RC2070401398901387264
  3    世界杯吉祥物ZAYU  1500  实物  1次   RC2071545327583535104
  4    顺丰定制雨伞      1000  实物  1次   RC2071522391409635328
  5    顺丰定制环保袋     800  实物  1次   RC2071523194698530816
  6    顺丰黄金金贴       800  实物  1次   RC2071524307690606592
  7    23元免单券         800  券    2次   RC2070398330633777152
  8    12元寄件券         400  券    5次   RC2070399299203448832
  9    5元寄件券          200  券   12次   RC2071525126427197440

【接口流程】
  1. prizePool        → 获取奖池（查库存/已兑次数）
  2. prizeDraw        → 兑换下单（传 ruleType/shouldNum/ruleCode/giftPoolCode）
  3. queryAddressBook → 查地址簿（仅实物需要）
  4. fillReceiveInfo  → 填写收货地址（仅实物需要）

====================================================================

"""

import hashlib
import os
import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

PROXY_TIMEOUT = 15
MAX_PROXY_RETRIES = 5
REQUEST_RETRY_COUNT = 3
CONCURRENT_NUM = int(os.getenv('SFBF', '1'))
if CONCURRENT_NUM > 20:
    CONCURRENT_NUM = 20
elif CONCURRENT_NUM < 1:
    CONCURRENT_NUM = 1

print_lock = Lock()

TOKEN = 'wwesldfs29aniversaryvdld29'
SYS_CODE = 'MCS-MIMP-CORE'
CHANNEL = '26sjbapp'
PLATFORM = 'SFAPP'

# 使用地址簿中第几个地址（0=第一个）
EXCHANGE_ADDRESS_INDEX = 0

# ===== 兑换项配置（从抓包提取，完整参数）=====
# 设为 True = 兑换该项；设为 False = 跳过
# shouldNum = 消耗金豆数；limitLotteryNum = 每人限兑次数
EXCHANGE_ITEMS = {
    # ── 实物类（productType=SFM，需填地址）──
    '大疆云台相机': {
        'enabled': False,        # 4000金豆，限兑1次
        'shouldNum': 4000,
        'ruleCode': 'RC2071521968535695360',
        'giftPoolCode': 'RGP2071522071354847232',
        'giftBagCode': 'GB2072258393963130880',
        'limitLotteryNum': 1,
    },
    '黄金足球金币': {
        'enabled': False,        # 3000金豆，限兑1次
        'shouldNum': 3000,
        'ruleCode': 'RC2070401398901387264',
        'giftPoolCode': 'RGP2070401639801192448',
        'giftBagCode': 'GB2070345977872318464',
        'limitLotteryNum': 1,
    },
    '世界杯吉祥物ZAYU': {
        'enabled': False,        # 1500金豆，限兑1次
        'shouldNum': 1500,
        'ruleCode': 'RC2071545327583535104',
        'giftPoolCode': 'RGP2071545403261366272',
        'giftBagCode': 'GB2070342899488038912',
        'limitLotteryNum': 1,
    },
    '顺丰定制雨伞': {
        'enabled': False,        # 1000金豆，限兑1次
        'shouldNum': 1000,
        'ruleCode': 'RC2071522391409635328',
        'giftPoolCode': 'RGP2071522423131078656',
        'giftBagCode': 'GB2072281755598860288',
        'limitLotteryNum': 1,
    },
    '顺丰定制环保袋': {
        'enabled': False,        # 800金豆，限兑1次
        'shouldNum': 800,
        'ruleCode': 'RC2071523194698530816',
        'giftPoolCode': 'RGP2071523233667821568',
        'giftBagCode': 'GB2070342191682482176',
        'limitLotteryNum': 1,
    },
    '顺丰黄金金贴': {
        'enabled': False,        # 800金豆，限兑1次
        'shouldNum': 800,
        'ruleCode': 'RC2071524307690606592',
        'giftPoolCode': 'RGP2071524350397050880',
        'giftBagCode': 'GB2072277419896434688',
        'limitLotteryNum': 1,
    },
    # ── 虚拟券类（productType=SFC，无需地址）──
    '23元免单券': {
        'enabled': True,         # 800金豆，限兑2次 ← 已开启
        'shouldNum': 800,
        'ruleCode': 'RC2070398330633777152',
        'giftPoolCode': 'RGP2070398549895229440',
        'giftBagCode': 'GB2000483494626267136',
        'limitLotteryNum': 2,
    },
    '12元寄件券': {
        'enabled': True,         # 400金豆，限兑5次 ← 已开启
        'shouldNum': 400,
        'ruleCode': 'RC2070399299203448832',
        'giftPoolCode': 'RGP2070399485015261184',
        'giftBagCode': 'GB2070346620188012544',
        'limitLotteryNum': 5,
    },
    '5元寄件券': {
        'enabled': True,         # 200金豆，限兑12次 ← 已开启
        'shouldNum': 200,
        'ruleCode': 'RC2071525126427197440',
        'giftPoolCode': 'RGP2071525224414441472',
        'giftBagCode': 'GB2062025763973922816',
        'limitLotteryNum': 12,
    },
}

# ===== 账号控制 =====
# 这些手机号不参与兑奖（跳过整个账号）
EXCLUDE_PHONES = set()

# 单独指定某手机号兑换哪些项（覆盖全局选择）
# 格式: '手机号': {'5元寄件券', '12元寄件券'}
# 留空 {} = 所有非排除账号都用全局选择
PHONE_OVERRIDE = {
    # '17606197000': {'5元寄件券', '12元寄件券'},
}


class Logger:
    def __init__(self):
        self.messages: List[str] = []

    def _log(self, icon: str, msg: str):
        line = f"{icon} {msg}"
        with print_lock:
            print(line)

    def info(self, msg): self._log('📝', msg)
    def success(self, msg): self._log('✅', msg)
    def warning(self, msg): self._log('⚠️', msg)
    def error(self, msg): self._log('❌', msg)
    def task(self, msg): self._log('🎯', msg)


class ProxyManager:
    def __init__(self, api_url: str):
        self.api_url = api_url

    def get_proxy(self) -> Optional[Dict[str, str]]:
        try:
            if not self.api_url:
                return None
            response = requests.get(self.api_url, timeout=10)
            if response.status_code == 200:
                proxy_text = response.text.strip()
                if ':' in proxy_text:
                    proxy = proxy_text if proxy_text.startswith('http') else f'http://{proxy_text}'
                    return {'http': proxy, 'https': proxy}
            return None
        except Exception:
            return None


class SFHttpClient:
    def __init__(self, proxy_manager: ProxyManager):
        self.proxy_manager = proxy_manager
        self.session = requests.Session()
        self.session.verify = False

        proxy = self.proxy_manager.get_proxy()
        if proxy:
            self.session.proxies = proxy

        self.headers = {
            'Host': 'mcs-mimp-web.sf-express.com',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 mediaCode=SFEXPRESSAPP-iOS-ML',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'channel': CHANNEL,
            'platform': PLATFORM,
            'accept-language': 'zh-CN,zh;q=0.9',
        }

    def _generate_sign(self) -> Dict[str, str]:
        timestamp = str(int(round(time.time() * 1000)))
        data = f'token={TOKEN}&timestamp={timestamp}&sysCode={SYS_CODE}'
        signature = hashlib.md5(data.encode()).hexdigest()
        return {
            'sysCode': SYS_CODE,
            'timestamp': timestamp,
            'signature': signature,
        }

    def request(self, url: str, data: Optional[Dict] = None, method: str = 'POST') -> Optional[Dict]:
        retry_count = 0
        proxy_retry_count = 0

        while proxy_retry_count < MAX_PROXY_RETRIES:
            sign_data = self._generate_sign()
            headers = {**self.headers, **sign_data}

            try:
                if method == 'POST':
                    resp = self.session.post(url, headers=headers, json=data or {}, timeout=PROXY_TIMEOUT)
                else:
                    resp = self.session.get(url, headers=headers, timeout=PROXY_TIMEOUT)
                resp.raise_for_status()

                try:
                    result = resp.json()
                    if result is None:
                        retry_count += 1
                        if retry_count < REQUEST_RETRY_COUNT:
                            time.sleep(2)
                            continue
                        return None
                    return result
                except (ValueError, requests.exceptions.JSONDecodeError):
                    retry_count += 1
                    if retry_count < REQUEST_RETRY_COUNT:
                        time.sleep(2)
                        continue
                    return None

            except requests.exceptions.RequestException as e:
                retry_count += 1
                error_str = str(e)

                if 'ProxyError' in error_str or 'SSLError' in error_str or 'ConnectionError' in error_str:
                    proxy_retry_count += 1
                    if proxy_retry_count < MAX_PROXY_RETRIES:
                        new_proxy = self.proxy_manager.get_proxy()
                        if new_proxy:
                            self.session.proxies = new_proxy
                        retry_count = 0
                    time.sleep(2)
                    continue

                if retry_count < REQUEST_RETRY_COUNT:
                    time.sleep(2)
                    continue
                return None

            except Exception:
                return None

        return None

    def login(self, url: str) -> tuple:
        try:
            decoded_input = unquote(url)
            if decoded_input.startswith('sessionId=') or '_login_mobile_=' in decoded_input:
                cookie_dict = {}
                for item in decoded_input.split(';'):
                    item = item.strip()
                    if '=' in item:
                        k, v = item.split('=', 1)
                        cookie_dict[k] = v
                for k, v in cookie_dict.items():
                    self.session.cookies.set(k, v, domain='mcs-mimp-web.sf-express.com')
                user_id = cookie_dict.get('_login_user_id_', '')
                phone = cookie_dict.get('_login_mobile_', '')
                return (True, user_id, phone) if phone else (False, '', '')
            else:
                self.session.get(unquote(url), headers=self.headers, timeout=PROXY_TIMEOUT)
                cookies = self.session.cookies.get_dict()
                user_id = cookies.get('_login_user_id_', '')
                phone = cookies.get('_login_mobile_', '')
                return (True, user_id, phone) if phone else (False, '', '')
        except Exception as e:
            print(f'登录异常: {str(e)}')
            return False, '', ''


class ExchangeExecutor:
    BASE_URL = 'https://mcs-mimp-web.sf-express.com/mcs-mimp'

    def __init__(self, http: SFHttpClient, logger: Logger, phone: str, selected_items: Optional[set] = None):
        self.http = http
        self.logger = logger
        self.phone = phone
        # selected_items: 要兑换的奖品名称集合；None=用配置表里 enabled=True 的
        self.selected_items = selected_items

    def _post(self, path: str, data: Optional[Dict] = None) -> Optional[Dict]:
        url = f'{self.BASE_URL}{path}'
        return self.http.request(url, data=data or {})

    # ===== 接口 =====

    def get_prize_pool(self) -> Optional[List[Dict]]:
        """获取奖池（含抽奖 LOTTERY 和兑换 EXCHANGE）"""
        resp = self._post('/commonPost/~memberNonactivity~worldCupLotteryService~prizePool')
        if resp and resp.get('success'):
            return resp.get('obj', [])
        return None

    def prize_draw(self, rule_type: str, should_num: int, rule_code: str, gift_pool_code: str) -> Optional[Dict]:
        """兑换/抽奖下单"""
        data = {
            "ruleType": rule_type,
            "shouldNum": should_num,
            "ruleCode": rule_code,
            "giftPoolCode": gift_pool_code,
        }
        resp = self._post('/commonPost/~memberNonactivity~worldCupLotteryService~prizeDraw', data)
        if resp and resp.get('success'):
            return resp.get('obj', {})
        err = resp.get('errorMessage', '未知错误') if resp else '请求失败'
        self.logger.warning(f'兑换失败: {err}')
        return None

    def query_address_book(self) -> Optional[List[Dict]]:
        """查询地址簿"""
        resp = self._post('/commonPost/~memberActivity~addressBookService~queryAddressBook')
        if resp and resp.get('success'):
            obj = resp.get('obj', {})
            return obj.get('result', [])
        return None

    def fill_receive_info(self, order_no: str, addr: Dict) -> bool:
        """填写实物收货地址"""
        data = {
            "orderNo": order_no,
            "receiver": addr.get("contactName", ""),
            "receiverMobile": addr.get("contactTel", "") or addr.get("contactPhone", ""),
            "addrDetail": addr.get("address", ""),
            "provinceCode": addr.get("provinceCode", ""),
            "provinceName": addr.get("province", ""),
            "cityCode": addr.get("cityCode", ""),
            "cityName": addr.get("city", ""),
            "countyCode": addr.get("countyCode", ""),
            "countyName": addr.get("county", ""),
        }
        resp = self._post('/commonPost/~activityCore~deliverOrderService~fillReceiveInfo', data)
        return bool(resp and resp.get('success'))

    # ===== 主流程 =====

    def run(self) -> Dict[str, Any]:
        result = {'exchange_items': [], 'failed_items': []}

        # 先查一次奖池，获取已兑次数（lotteryNum）和库存状态
        self.logger.info('查询兑奖奖池...')
        pool = self.get_prize_pool()
        if pool is None:
            self.logger.error('获取奖池失败')
            return result

        # 从奖池中提取每项的已兑次数和售罄状态
        pool_map = {}  # ruleCode -> {lotteryNum, soldOut, soldOutToday}
        for item in pool:
            if item.get('ruleType') == 'EXCHANGE':
                pool_map[item.get('ruleCode', '')] = {
                    'lotteryNum': item.get('lotteryNum', 0),
                    'soldOut': item.get('soldOut', False),
                    'soldOutToday': item.get('soldOutToday', False),
                }

        # 遍历配置表，根据 selected_items 或 enabled 决定兑换项
        for name, cfg in EXCHANGE_ITEMS.items():
            # 如果指定了 selected_items，用它判断；否则用配置表的 enabled
            if self.selected_items is not None:
                if name not in self.selected_items:
                    continue
            else:
                if not cfg.get('enabled'):
                    continue

            rule_code = cfg['ruleCode']
            should_num = cfg['shouldNum']
            gift_pool_code = cfg['giftPoolCode']
            limit = cfg.get('limitLotteryNum', 1)

            # 检查奖池状态
            pool_info = pool_map.get(rule_code, {})
            already = pool_info.get('lotteryNum', 0)
            sold_out = pool_info.get('soldOut', False)
            sold_today = pool_info.get('soldOutToday', False)

            if sold_out or sold_today:
                self.logger.info(f'[{name}] 已售罄，跳过')
                continue

            remaining = limit - already
            if remaining <= 0:
                self.logger.info(f'[{name}] 已兑 {already}/{limit} 次，跳过')
                continue

            self.logger.task(f'[{name}] 兑换（{should_num}金豆/次，剩余 {remaining}/{limit} 次）')

            # 按剩余次数循环兑换
            for i in range(remaining):
                draw_result = self.prize_draw('EXCHANGE', should_num, rule_code, gift_pool_code)
                if draw_result is None:
                    result['failed_items'].append({'name': name, 'reason': f'第{i+1}次兑换失败'})
                    break

                # 检查产品类型：SFM=实物, SFC=优惠券
                product_list = draw_result.get('productDTOList', [])
                order_no = ''
                is_physical = False
                product_names = []

                for p in product_list:
                    p_type = p.get('productType', '')
                    p_name = p.get('productName', '?')
                    product_names.append(p_name)
                    if p_type == 'SFM':
                        is_physical = True
                        order_no = p.get('orderNo', '')

                product_str = ', '.join(product_names) if product_names else name
                self.logger.success(f'[{name}] 第{i+1}/{remaining}次 兑换成功: {product_str}')

                if is_physical and order_no:
                    # 实物 → 查地址簿并填地址
                    self.logger.task(f'实物奖品，填写收货地址（订单 {order_no}）...')
                    time.sleep(1)
                    addr_book = self.query_address_book()
                    if addr_book:
                        idx = min(EXCHANGE_ADDRESS_INDEX, len(addr_book) - 1)
                        addr = addr_book[idx]
                        addr_str = f'{addr.get("contactName", "")} {addr.get("contactTel", "") or addr.get("contactPhone", "")} {addr.get("address", "")}'
                        self.logger.info(f'使用地址: {addr_str}')
                        if self.fill_receive_info(order_no, addr):
                            self.logger.success('地址填写成功')
                        else:
                            self.logger.warning('地址填写失败，需手动填写')
                    else:
                        self.logger.warning(f'未获取到地址簿，需手动填写地址（订单 {order_no}）')
                else:
                    # 虚拟券
                    self.logger.info('虚拟奖品（优惠券），无需填写地址')

                result['exchange_items'].append({
                    'name': product_str,
                    'cost': should_num,
                    'is_physical': is_physical,
                    'order_no': order_no,
                })

                time.sleep(2)

        return result


def run_account(account_url: str, index: int, selected_items: Optional[set] = None) -> Dict[str, Any]:
    logger = Logger()
    proxy_url = os.getenv('SF_PROXY_API_URL', '')
    proxy_manager = ProxyManager(proxy_url)

    http = SFHttpClient(proxy_manager)
    retry_count = 0
    login_success = False
    phone = ''

    while retry_count < MAX_PROXY_RETRIES and not login_success:
        try:
            if retry_count > 0:
                http = SFHttpClient(proxy_manager)
            success, user_id, phone = http.login(account_url)
            if success:
                login_success = True
                break
        except Exception:
            pass
        retry_count += 1
        if retry_count < MAX_PROXY_RETRIES:
            time.sleep(2)

    if not login_success:
        logger.error(f'账号{index + 1} 登录失败')
        return {'success': False, 'phone': '', 'index': index, 'exchange_items': [], 'failed_items': []}

    logger.success(f'账号{index + 1}: 【{phone}】登录成功')

    # 排除名单：这些手机号不兑奖
    if phone in EXCLUDE_PHONES:
        logger.info(f'【{phone}】在排除名单，跳过兑奖')
        return {'success': True, 'phone': phone, 'index': index, 'exchange_items': [], 'failed_items': [], 'skipped': True}

    # 单独指定：PHONE_OVERRIDE 里有这个手机号就用它指定的项
    items_for_this_phone = selected_items
    if phone in PHONE_OVERRIDE:
        items_for_this_phone = PHONE_OVERRIDE[phone]
        logger.info(f'【{phone}】使用单独配置: {items_for_this_phone}')

    time.sleep(random.uniform(1, 3))

    executor = ExchangeExecutor(http, logger, phone, items_for_this_phone)
    result = executor.run()

    return {
        'success': True,
        'phone': phone,
        'index': index,
        **result,
    }


def interactive_select() -> set:
    """交互式选择要兑换的奖品"""
    print('\n' + '=' * 60)
    print('🎁 兑换项列表')
    print('=' * 60)
    print(f'{"序号":<5} {"状态":<6} {"奖品名称":<20} {"金豆":<8} {"类型":<6} {"限兑":<6}')
    print('-' * 60)

    names = list(EXCHANGE_ITEMS.keys())
    for i, name in enumerate(names):
        cfg = EXCHANGE_ITEMS[name]
        enabled = '✅' if cfg.get('enabled') else '❌'
        cost = cfg['shouldNum']
        limit = cfg.get('limitLotteryNum', 1)
        # 判断实物/券：实物类在配置表注释中标注
        is_physical = cfg['shouldNum'] >= 800 and limit <= 1
        ptype = '实物' if is_physical else '券'
        print(f"{i+1:<5} {enabled:<6} {name:<20} {cost:<8} {ptype:<6} {limit}次")

    print('-' * 60)
    print('\n输入要兑换的序号（多个用逗号/空格分隔）')
    print('输入 a = 兑换所有券类（5元/12元/23元）')
    print('输入 all = 兑换全部（含实物）')
    print('直接回车 = 用配置表里 enabled=True 的项')
    print('输入 q = 退出')

    user_input = input('> ').strip()

    if not user_input:
        return set()  # 空集表示用配置表默认

    if user_input.lower() == 'q':
        print('已退出')
        sys.exit(0)

    if user_input.lower() == 'all':
        selected = set(names)
        print(f'\n✅ 已选择全部 {len(selected)} 项')
        return selected

    if user_input.lower() == 'a':
        coupon_names = {'5元寄件券', '12元寄件券', '23元免单券'}
        selected = coupon_names & set(names)
        print(f'\n✅ 已选择券类: {selected}')
        return selected

    # 解析序号
    indices = set()
    for part in user_input.replace(',', ' ').split():
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(names):
                indices.add(idx)

    selected = {names[i] for i in sorted(indices)}
    if selected:
        print(f'\n✅ 已选择: {selected}')
    else:
        print('未选择任何项，将使用配置表默认')

    return selected


def main():
    env_name = 'sfsyUrl'
    env_value = os.getenv(env_name)
    if not env_value:
        print(f"❌ 未找到环境变量 {env_name}，请检查配置")
        return

    account_urls = [url.strip() for url in env_value.split('&') if url.strip()]
    if not account_urls:
        print(f"❌ 环境变量 {env_name} 为空或格式错误")
        return

    # 交互选择兑换项（非交互模式用配置表默认）
    selected_items = interactive_select()

    # 空集=用配置表 enabled 默认；非空=用选择的
    use_selected = len(selected_items) > 0

    print("=" * 60)
    print(f"🎁 顺丰2026世界杯 - 金豆兑奖")
    print(f"📱 共获取到 {len(account_urls)} 个账号")
    print(f"⚙️ 并发数量: {CONCURRENT_NUM}")
    if use_selected:
        print(f"🎯 兑换项（手动选择）: {selected_items}")
    else:
        enabled_list = [k for k, v in EXCHANGE_ITEMS.items() if v.get('enabled')]
        print(f"🎯 兑换项（配置默认）: {enabled_list}")
    if EXCLUDE_PHONES:
        print(f"🚫 排除手机号: {EXCLUDE_PHONES}")
    if PHONE_OVERRIDE:
        print(f"🔧 单独配置: {list(PHONE_OVERRIDE.keys())}")
    print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 传给 run_account 的是 None（用默认）或 set（用选择的）
    items_to_pass = selected_items if use_selected else None

    all_results = []

    if CONCURRENT_NUM <= 1:
        for idx, url in enumerate(account_urls):
            result = run_account(url, idx, items_to_pass)
            all_results.append(result)
            if idx < len(account_urls) - 1:
                print("-" * 60)
                time.sleep(2)
    else:
        with ThreadPoolExecutor(max_workers=CONCURRENT_NUM) as pool:
            futures = {pool.submit(run_account, url, idx, items_to_pass): idx for idx, url in enumerate(account_urls)}
            for future in as_completed(futures):
                all_results.append(future.result())

    all_results.sort(key=lambda x: x['index'])

    # 汇总
    print(f"\n{'=' * 80}")
    print(f"📊 兑奖汇总")
    print(f"{'=' * 80}")
    print(f"{'序号':<5} {'手机号':<15} {'兑换数':<8} {'失败数':<8} {'明细'}")
    print("-" * 80)

    total_success = 0
    total_failed = 0

    for r in all_results:
        idx = r['index'] + 1
        phone = r.get('phone', '未登录')
        items = r.get('exchange_items', [])
        failed = r.get('failed_items', [])
        total_success += len(items)
        total_failed += len(failed)

        detail_parts = []
        for item in items:
            tag = '实物' if item.get('is_physical') else '券'
            detail_parts.append(f"{item['name']}({tag})")
        for item in failed:
            detail_parts.append(f"{item['name']}(失败)")
        detail = ', '.join(detail_parts) if detail_parts else '-'

        print(f"{idx:<5} {phone:<15} {len(items):<8} {len(failed):<8} {detail}")

    print("-" * 80)
    print(f"{'汇总':<5} {'账号: ' + str(len(all_results)):<15} 成功兑换: {total_success} 件 | 失败: {total_failed} 件")
    print("=" * 80)
    print("\n🎊 兑奖完成!")


if __name__ == '__main__':
    main()


# 当前脚本来自于 http://script.345yun.cn 脚本库下载！
# 当前脚本来自于 http://2.345yun.cn 脚本库下载！
# 当前脚本来自于 http://2.345yun.cc 脚本库下载！
# 脚本库官方QQ群1群: 429274456
# 脚本库官方QQ群2群: 1077801222
# 脚本库官方QQ群3群: 433030897
# 脚本库中的所有脚本文件均来自热心网友上传和互联网收集。
# 脚本库仅提供文件上传和下载服务，不提供脚本文件的审核。
# 您在使用脚本库下载的脚本时自行检查判断风险。
# 所涉及到的 账号安全、数据泄露、设备故障、软件违规封禁、财产损失等问题及法律风险，与脚本库无关！均由开发者、上传者、使用者自行承担。