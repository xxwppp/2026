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

#仅供学习交流，禁止倒卖
#替换接口直接使用，有能力自己二改


import sys
import os
import re
import json
import time
import copy
import random
import base64
import hashlib
import logging
import asyncio
import warnings
import requests
import aiohttp
from typing import Optional, Dict, List, Tuple, Any
from urllib.parse import quote, urlencode
from aiohttp_socks import ProxyConnector

# 全局配置
WORK_DIR = os.getcwd()
# 签名服务配置（直连上游，无需卡密）
SIGN_BASE_URL = os.getenv('SIGN_BASE_URL', '接口地址')#接口尾部不用带/
TIMESTAMP_API_URL = 'http://vv.video.qq.com/checktime?otype=json'
DEFAULT_SALT='382700b563f4'
MAX_CONCURRENCY_DEFAULT = int(os.getenv('MAX_CONCURRENCY', '666'))
DEV_MODE=int(os.getenv('DEV_MODE',0))
COIN_LIMIT=int(os.getenv('KS_COIN_LIMIT','0'))
if not COIN_LIMIT:
    COIN_LIMIT=int(os.getenv('COIN_LIMIT','300000'))
MAX_ROUNDS=int(os.getenv('ROUNDS','30'))
LOW_REWARD_THRESHOLD=int(os.getenv('LOW_REWARD_THRESHOLD','10'))
SUCCESS_AD_NUM=int(os.getenv('SUCCESS_AD_NUM','0'))
LOW_REWARD_LIMIT=int(os.getenv('LOW_REWARD_LIMIT','3'))
TASK_NUM_ROUND=int(os.getenv('TASK_NUM_ROUND','3'))
WAIT_TIME=os.getenv('WAIT_TIME','[3000,5000]')
ROUNDS_WAIT_TIME=os.getenv('ROUNDS_WAIT_TIME','[5000,10000]')
PLAY_WAIT_TIME=os.getenv('PLAY_WAIT_TIME','[40000,60000]')
DANGER_COIN=os.getenv('DANGER_COIN','[1,2,3,4,5,6]')
CHANGE_DID_RANGE=os.getenv('CHANGE_DID_RANGE','[10,100]')
CHANGE_DID_TIMES=int(os.getenv('CHANGE_DID_TIMES','2'))
MODE_CHANGE=int(os.getenv('MODE_CHANGE','0'))
SLEEP_TIME=int(os.getenv('SLEEP_TIME','10'))
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    datefmt='%H:%M:%S'
)
logger=logging.getLogger(__name__)
def get_tencent_timestamp():
    '获取腾讯时间戳'
    try:
        response=requests.get(TIMESTAMP_API_URL,headers={'User-Agent':'Mozilla/5.0'},timeout=10)
        if response.text:
            import re
            match=re.search(r'QZOutputJson=({.*?});',response.text)
            if match:
                data=json.loads(match.group(1))
                if data and data.get('t'):
                    return int(data['t'])
    except Exception as e:
        logger.debug(f"获取腾讯时间戳失败: {e}")
    return int(time.time())
def generate_dynamic_api_key():
    '生成动态API密钥'
    timestamp=get_tencent_timestamp()
    key_string=f"{timestamp}12345"
    key=hashlib.md5(key_string.encode()).hexdigest()
    return{'key':key,'timestamp':timestamp}
def parse_task_config()->List[str]:
    '解析任务配置'
    task_env=os.getenv('k_task10','').strip()
    if not task_env:
        task_env=os.getenv('k_task','').strip()
    if not task_env:
        return['box']
    task_list=[task.strip().lower()for task in task_env.split(',')if task.strip()]
    valid_tasks=['food','box','look','search','play','see','cn','test']
    filtered_tasks=[task for task in task_list if task in valid_tasks]
    if not filtered_tasks:
        return['box']
    return filtered_tasks
def parse_account_config(config_string:str)->Optional[Dict]:
    """解析账号配置字符串
    支持多种格式：
    1. 备注#cookie#salt#代理ip (4部分，使用备注作为nickname)
    2. 备注#cookie#salt (3部分，第3部分不是代理，使用备注作为nickname)
    3. cookie#salt#代理ip (3部分，第3部分是代理，使用API获取的nickname)
    4. cookie#salt (2部分，使用API获取的nickname)
    
    """
    parts=config_string.strip().split('#')
    if len(parts)<2:
        return None
    config={}
    proxy_url=None
    def is_proxy_format(part:str)->bool:
        '判断字符串是否是代理格式'
        if not part:
            return False
        part=part.strip()
        return '|' in part or part.lower().startswith('socks5://')
    if len(parts)>=4:
        config['nickname']=parts[0].strip()
        config['cookie']=parts[1].strip()
        config['salt']=parts[2].strip()
        proxy_part=parts[3].strip()
        has_remark=True
    elif len(parts)==3:
        if is_proxy_format(parts[2]):
            config['cookie']=parts[0].strip()
            config['salt']=parts[1].strip()
            proxy_part=parts[2].strip()
            has_remark=False
        else:
            config['nickname']=parts[0].strip()
            config['cookie']=parts[1].strip()
            config['salt']=parts[2].strip()
            proxy_part=None
            has_remark=True
    else:
        config['cookie']=parts[0].strip()
        config['salt']=parts[1].strip()
        proxy_part=None
        has_remark=False
    if proxy_part:
        if '|' in proxy_part:
            logger.info(f"开始解析代理格式: {proxy_part}")
            proxy_parts=proxy_part.split('|')
            if len(proxy_parts)>=4:
                host,port,username,password=proxy_parts[:4]
                proxy_url=f"socks5://{username}:{password}@{host}:{port}"
        elif proxy_part.lower().startswith('socks5://'):
            proxy_url=proxy_part
        else:
            logger.warning(f"⚠️ 代理字段不是 socks5:// URL，忽略：{proxy_part}")
    config['proxy_url']=proxy_url
    config['has_remark']=has_remark
    return config
def load_account_configs()->List[Dict]:
    '加载所有账号配置'
    accounts=[]
    seen_configs=set()
    account_index=0
    ksck_value=''
    config_file=os.getenv('CONFIG_FILE','')
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file,'r',encoding='utf-8')as f:
                file_config=json.load(f)
            ksck_value=str(file_config.get('k_ksck','')).strip()
            if ksck_value:
                logger.info(f"从临时配置文件加载账号: {os.path.basename(config_file)}")
        except Exception as e:
            logger.warning(f"读取临时配置文件失败: {e}")
    if not ksck_value:
        ksck_value=os.getenv('k_ksck10','').strip()
    if not ksck_value:
        ksck_value=os.getenv('k_ksck','').strip()
    if ksck_value:
        config_list=[config.strip()for config in ksck_value.split('&')if config.strip()]
        for config_string in config_list:
            if config_string not in seen_configs:
                parsed_config=parse_account_config(config_string)
                if parsed_config:
                    account_index+=1
                    parsed_config['index']=account_index
                    parsed_config['source']='k_ksck10'
                    accounts.append(parsed_config)
                    seen_configs.add(config_string)
                else:
                    logger.warning(f"⚠️ k_ksck10 配置格式错误，忽略: {config_string}")
            else:
                logger.warning(f"⚠️ k_ksck10 配置重复，忽略: {config_string}")
    if not accounts:
        logger.error(f"❌ 未找到任何有效的账号配置（检查 k_ksck10）")
    else:
        pass
    return accounts
def generate_device_id()->str:
    '低奖励时生成设备ID'
    try:
        hex_chars='0123456789abcdef'
        random_hex=''.join(random.choice(hex_chars)for _ in range(16))
        return f"ANDROID_{random_hex}"
    except Exception as e:
        logger.error(f"生成did失败: {e}")
        timestamp_hex=hex(int(time.time()))[2:].upper()[:16]
        return f"ANDROID_{timestamp_hex}"
def generate_egid()->str:
    '低奖励时生成egid'
    try:
        hex_chars='0123456789ABCDEF'
        random_hex=''.join(random.choice(hex_chars)for _ in range(61))
        return f"DFP{random_hex}"
    except Exception as e:
        logger.error(f"生成egid失败: {e}")
        timestamp_hex=hex(int(time.time()))[2:].upper()
        timestamp_hex=timestamp_hex.ljust(61,'0')
        return f"DFP{timestamp_hex}"
async def make_http_request(session:aiohttp.ClientSession,
                            method:str,url:str,
                            proxy_url:Optional[str]=None,
                            headers:Optional[Dict]=None,
                            data:Optional[Dict]=None,
                            json_data:Optional[Dict]=None,
                            timeout:int=12,
                            request_name:str='Unknown Request')->Optional[Dict]:
    '发送HTTP请求'
    connector=None
    if proxy_url:
        try:
            from aiohttp_socks import ProxyConnector
            connector=ProxyConnector.from_url(proxy_url)
            if DEV_MODE:
                logger.debug(f"[调试] {request_name} 使用代理: {proxy_url}")
        except Exception as e:
            logger.error(f"[错误] {request_name} 代理URL无效({e})，尝试直连模式")
            if DEV_MODE:
                logger.debug('[调试] 代理无效，自动切换到直连模式')
    else:
        if DEV_MODE:
            logger.debug('[调试] 未配置代理，使用直连模式')
    if DEV_MODE:
        logger.debug(f"[调试] {request_name} -> {method} {url}")
    try:
        timeout_obj=aiohttp.ClientTimeout(total=timeout)
        if connector:
            async with aiohttp.ClientSession(connector=connector,timeout=timeout_obj)as proxy_session:
                async with proxy_session.request(method,url,headers=headers,data=data,json=json_data)as response:
                    if hasattr(response.connection,'transport'):
                        transport=response.connection.transport
                        if hasattr(transport,'get_extra_info'):
                            proxy_addr=transport.get_extra_info('peername')
                    if DEV_MODE:
                        logger.debug(f'[调试] {request_name} 响应状态: {response.status}')
                    if response.status==200:
                        try:
                            return await response.json()
                        except:
                            return await response.text()
                    else:
                        logger.debug(f"[调试] {request_name} HTTP状态码异常: {response.status}")
                        return await response.json()
        else:
            async with session.request(method,url,headers=headers,data=data,json=json_data)as response:
                if response.status==200:
                    try:
                        return await response.json()
                    except:
                        return await response.text()
                else:
                    logger.debug(f"[调试] {request_name} HTTP状态码异常: {response.status}")
                    return await response.json()
    except Exception as e:
        if hasattr(e,'errors')and isinstance(e.errors,list):
            logger.debug(f"[调试] {request_name} 请求错误: AggregateError")
            for i,error in enumerate(e.errors):
                logger.debug(f"  [{i}] {getattr(error, 'message', str(error))}")
        else:
            logger.debug(f"[调试] {request_name} 请求错误: {e}")
        return None
async def test_proxy_connection(proxy_url:Optional[str],
                                request_name:str='代理连通性检测')->Dict:
    '测试代理连接'
    if not proxy_url:
        return{
            'ok':True,
            'msg':'✅ 未配置代理（直连模式）',
            'ip':'localhost'
}
    ip_check_urls=[
        'http://myip.ipip.net',# 国内 ipip.net
        'http://ip-api.com/json',# 国内可访问
        'https://ipinfo.io/json',# 海外服务备用
]
    async with aiohttp.ClientSession()as session:
        for url in ip_check_urls:
            response=await make_http_request(
                session,'GET',url,
                proxy_url=proxy_url,
                headers={'User-Agent':'ProxyTester/1.0'},
                timeout=10,
                request_name=f"{request_name} → {url.split('/')[2]}"
)
            if response:
                ip_address=''
                if isinstance(response,dict):
                    ip_address=response.get('ip',response.get('ip_address',''))or response.get(
                        'query')or response.get('origin','')
                elif isinstance(response,str):
                    import re
                    ip_match=re.search('(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',response)
                    if ip_match:
                        ip_address=ip_match.group(1)
                    else:
                        ip_address=response.strip()[:50]# 截取前50字符
                if ip_address:
                    return{
                        'ok':True,
                        'msg':f'✅ SOCKS5代理正常，IP地址: {ip_address or "未知"}',
                        'ip':ip_address or '未知'
}
        return{
            'ok':False,
            'msg':'❌ 无法连通代理ip，请检查',
            'ip':''
}
async def get_account_basic_info(cookie:str,proxy_url:Optional[str],
                                 account_index:int)->Optional[Dict]:
    '获取账号基本信息'
    url='https://encourage.kuaishou.com/rest/wd/encourage/account/withdraw/info?source=normal&imei=&oaid=&idfa='
    headers={
        'Host':'encourage.kuaishou.com',
        'User-Agent':'kwai-android aegon/3.56.0',
        'Cookie':cookie,
        'Content-Type':'application/x-www-form-urlencoded'
}
    async with aiohttp.ClientSession()as session:
        response=await make_http_request(
            session,'GET',url,
            proxy_url=proxy_url,
            headers=headers,
            timeout=12,
            request_name=f"账号[{account_index}] 获取基本信息"
)
        if response and response.get('result')==1 and response.get('data'):
            return{
                'nickname':response['data'].get('nickname'),
                'total_coin':response['data'].get('account').get('coinAmount'),
                'all_cash':response['data'].get('account').get('cashAmountDisplay')
}
        return None
def get_search_value():
    """
    从环境变量SC_KEY读取搜索关键词
    默认:小说
    """
    SC_KEY=os.getenv('SC_KEY','').strip()
    if SC_KEY:
        return SC_KEY
    return '小说'  # 默认短剧小说
def center_text(text:str,width:int)->str:
    '文本居中对齐'
    text=str(text)
    if len(text)>=width:
        return text[:width]
    padding=width-len(text)
    left_padding=padding//2
    right_padding=padding-left_padding
    return ' '*left_padding+text+' '*right_padding
class KuaishouTaskWorker:
    '快手任务工作器'
    def __init__(self,account_config:Dict,tasks_to_execute:List[str]):
        self.index=account_config['index']
        self.salt=account_config['salt']
        self.cookie=account_config['cookie']
        self.nickname=account_config.get('nickname',f"账号{self.index}")
        self.proxy_url=account_config.get('proxy_url')
        self.count=0
        self.coin_limit=COIN_LIMIT
        self.low_reward_threshold=LOW_REWARD_THRESHOLD
        self.low_reward_limit=LOW_REWARD_LIMIT
        self.coin_exceeded=False
        self.tasks_to_execute=tasks_to_execute
        self.extract_cookie_info()
        self.headers={
            'Host':'nebula.kuaishou.com',
            'Connection':'keep-alive',
            'User-Agent':'Mozilla/5.0 (Linux; Android 10; MI 8 Lite Build/QKQ1.190910.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/87.0.4280.101 Mobile Safari/537.36',
            'Cookie':self.cookie,
            'content-type':'application/json'
}
        self.task_report_path='/rest/r/ad/task/report'
        self.query_params=f"mod=Xiaomi%28M2011K2C%29&appver={self.app_version}&egid={self.egid}&did={self.device_id}"
        self.task_configs={
            'box':{
                'name':'宝箱广告',
                'business_id':604,
                'pos_id':20345,
                'page_id':100011251,
                'sub_page_id':100024063,
                'request_scene_type':7,
                'task_type':1
},
            'look':{#看广告得金币奖励
                'name':'看币广告',
                'business_id':671,
                'pos_id':24068,
                'page_id':100011251,
                'sub_page_id':100026368,
                'request_scene_type':7,
                'task_type':1
},
            'food':{
                'name':'饭补广告',
                'business_id':921,
                'pos_id':29742,
                'page_id':100011251,
                'sub_page_id':100029908,
                'request_scene_type':7,
                'task_type':2
},
            'search':{#搜索看广告金币奖励
                'name':'搜索广告',
                'business_id':7039,
                'pos_id':95652,
                'sub_page_id':100074571,
                'page_id':100011251,
                'request_scene_type':7,
                'task_type':2,
                'linkUrl':'eyJwYWdlSWQiOjExMTAxLCJzdWJQYWdlSWQiOjEwMDA3NDU4NCwicG9zSWQiOjk2MTM0LCJidXNpbmVzc0lkIjo3MDM4LCJleHRQYXJhbXMiOiI0YmJiMWI1OTBiZDViMGEwNzZlNTMxNjg5MThjMGQ5NWNjM2I5NjY1NmViMGVmNmJiNGY5Yjg4MGQ3OTNjZThmOWMwMDUwOWFlYjcxZGUwZTdjZmQ2YWM2Y2MwMjE3MjU0N2U1ZTEzNGZmYWNjOGU0OWQ5M2JhYjM4ZTdiYzRiN2IyZTBmNjIwMDE5Yzc1ODdmMmQzYzM4YWVhYmQ2MzJkN2JjZjA3YzU2Y2I4MDU5NjQ0YmU5ZDIxNzkzN2YzN2MiLCJjdXN0b21EYXRhIjp7ImV4aXRJbmZvIjp7InRvYXN0RGVzYyI6bnVsbCwidG9hc3RJbWdVcmwiOm51bGx9fSwicGVuZGFudFR5cGUiOjEsImRpc3BsYXlUeXBlIjoyLCJzaW5nbGVQYWdlSWQiOjAsInNpbmdsZVN1YlBhZ2VJZCI6MCwiY2hhbm5lbCI6MCwiY291bnRkb3duUmVwb3J0Ijp0cnVlLCJ0aGVtZVR5cGUiOjAsIm1peGVkQWQiOnRydWUsImZ1bGxNaXhlZCI6dHJ1ZSwiYXV0b1JlcG9ydCI6dHJ1ZSwiZnJvbVRhc2tDZW50ZXIiOnRydWUsInNlYXJjaEluc3BpcmVTY2hlbWVJbmZvIjp7InNlYXJjaFF1ZXJ5Ijoi5aW96LSnIiwic2VhcmNoU2Vzc2lvbklkIjoiTVRjMU56TTFOVE0zT0RjeE5GOWpiRzkxWkMweU1qWTBNVGMxTFRFeU1qRTROall0TVRBNE5EYzVOeTB5TURBdFpHVndiRzk1TFRnMU9HSTVOelZtTkRZdGJEbHpZbXhmNWFXOTZMU25YekF1TURFME1ETTFNekF3TmpRM01EYzRNRE0iLCJlbnRlclNvdXJjZSI6IkFDVF9yZW53dV9hZF9ib3hfc2luZ2xlX2NvbCJ9LCJhbW91bnQiOjI1MDB9'
},
            'play':{
                'name':'短剧广告',
                'request_scene_type':7,
                'task_type':2,
                'business_id':None,
                'pos_id':None,
                'sub_page_id':None,
                'page_id':None
},
            'cn':{#可用 7037 短剧 7075 7057 7059 7061 7063 7073 7079看内容 7042 看广告得金币
                'name':'内容广告',
                'business_id':None,
                'pos_id':None,
                'sub_page_id':None,
                'page_id':None,
                'request_scene_type':7,
                'task_type':2,
                'linkUrl':'eyJwYWdlSWQiOjExMTAxLCJzdWJQYWdlSWQiOjEwMDA3NDU4NCwicG9zSWQiOjk2MTM0LCJidXNpbmVzc0lkIjo3MDM4LCJleHRQYXJhbXMiOiI0YmJiMWI1OTBiZDViMGEwNzZlNTMxNjg5MThjMGQ5NWNjM2I5NjY1NmViMGVmNmJiNGY5Yjg4MGQ3OTNjZThmOWMwMDUwOWFlYjcxZGUwZTdjZmQ2YWM2Y2MwMjE3MjU0N2U1ZTEzNGZmYWNjOGU0OWQ5M2JhYjM4ZTdiYzRiN2IyZTBmNjIwMDE5Yzc1ODdmMmQzYzM4YWVhYmQ2MzJkN2JjZjA3YzU2Y2I4MDU5NjQ0YmU5ZDIxNzkzN2YzN2MiLCJjdXN0b21EYXRhIjp7ImV4aXRJbmZvIjp7InRvYXN0RGVzYyI6bnVsbCwidG9hc3RJbWdVcmwiOm51bGx9fSwicGVuZGFudFR5cGUiOjEsImRpc3BsYXlUeXBlIjoyLCJzaW5nbGVQYWdlSWQiOjAsInNpbmdsZVN1YlBhZ2VJZCI6MCwiY2hhbm5lbCI6MCwiY291bnRkb3duUmVwb3J0Ijp0cnVlLCJ0aGVtZVR5cGUiOjAsIm1peGVkQWQiOnRydWUsImZ1bGxNaXhlZCI6dHJ1ZSwiYXV0b1JlcG9ydCI6dHJ1ZSwiZnJvbVRhc2tDZW50ZXIiOnRydWUsInNlYXJjaEluc3BpcmVTY2hlbWVJbmZvIjp7InNlYXJjaFF1ZXJ5Ijoi5aW96LSnIiwic2VhcmNoU2Vzc2lvbklkIjoiTVRjMU56TTFOVE0zT0RjeE5GOWpiRzkxWkMweU1qWTBNVGMxTFRFeU1qRTROall0TVRBNE5EYzVOeTB5TURBdFpHVndiRzk1TFRnMU9HSTVOelZtTkRZdGJEbHpZbXhmNWFXOTZMU25YekF1TURFME1ETTFNekF3TmpRM01EYzRNRE0iLCJlbnRlclNvdXJjZSI6IkFDVF9yZW53dV9hZF9ib3hfc2luZ2xlX2NvbCJ9LCJhbW91bnQiOjI1MDB9'
},
            'see':{
                'name':'看奖广告',
                'business_id':None,
                'pos_id':None,
                'sub_page_id':None,
                'page_id':None,
                'request_scene_type':7,
                'task_type':2,
                'linkUrl':'eyJwYWdlSWQiOjExMTAxLCJzdWJQYWdlSWQiOjEwMDA3NDU4NCwicG9zSWQiOjk2MTM0LCJidXNpbmVzc0lkIjo3MDM4LCJleHRQYXJhbXMiOiI0YmJiMWI1OTBiZDViMGEwNzZlNTMxNjg5MThjMGQ5NWNjM2I5NjY1NmViMGVmNmJiNGY5Yjg4MGQ3OTNjZThmOWMwMDUwOWFlYjcxZGUwZTdjZmQ2YWM2Y2MwMjE3MjU0N2U1ZTEzNGZmYWNjOGU0OWQ5M2JhYjM4ZTdiYzRiN2IyZTBmNjIwMDE5Yzc1ODdmMmQzYzM4YWVhYmQ2MzJkN2JjZjA3YzU2Y2I4MDU5NjQ0YmU5ZDIxNzkzN2YzN2MiLCJjdXN0b21EYXRhIjp7ImV4aXRJbmZvIjp7InRvYXN0RGVzYyI6bnVsbCwidG9hc3RJbWdVcmwiOm51bGx9fSwicGVuZGFudFR5cGUiOjEsImRpc3BsYXlUeXBlIjoyLCJzaW5nbGVQYWdlSWQiOjAsInNpbmdsZVN1YlBhZ2VJZCI6MCwiY2hhbm5lbCI6MCwiY291bnRkb3duUmVwb3J0Ijp0cnVlLCJ0aGVtZVR5cGUiOjAsIm1peGVkQWQiOnRydWUsImZ1bGxNaXhlZCI6dHJ1ZSwiYXV0b1JlcG9ydCI6dHJ1ZSwiZnJvbVRhc2tDZW50ZXIiOnRydWUsInNlYXJjaEluc3BpcmVTY2hlbWVJbmZvIjp7InNlYXJjaFF1ZXJ5Ijoi5aW96LSnIiwic2VhcmNoU2Vzc2lvbklkIjoiTVRjMU56TTFOVE0zT0RjeE5GOWpiRzkxWkMweU1qWTBNVGMxTFRFeU1qRTROall0TVRBNE5EYzVOeTB5TURBdFpHVndiRzk1TFRnMU9HSTVOelZtTkRZdGJEbHpZbXhmNWFXOTZMU25YekF1TURFME1ETTFNekF3TmpRM01EYzRNRE0iLCJlbnRlclNvdXJjZSI6IkFDVF9yZW53dV9hZF9ib3hfc2luZ2xlX2NvbCJ9LCJhbW91bnQiOjI1MDB9'
},
            'test':{# 10金币
                'name':'搜索广告',
                'business_id':921,
                'pos_id':216267,
                'sub_page_id':100161535,
                'page_id':10014,
                'request_scene_type':1,
                'task_type':1,
                'linkUrl':'eyJwYWdlSWQiOjExMTAxLCJzdWJQYWdlSWQiOjEwMDA3NDU4NCwicG9zSWQiOjk2MTM0LCJidXNpbmVzc0lkIjo3MDM4LCJleHRQYXJhbXMiOiI0YmJiMWI1OTBiZDViMGEwNzZlNTMxNjg5MThjMGQ5NWNjM2I5NjY1NmViMGVmNmJiNGY5Yjg4MGQ3OTNjZThmOWMwMDUwOWFlYjcxZGUwZTdjZmQ2YWM2Y2MwMjE3MjU0N2U1ZTEzNGZmYWNjOGU0OWQ5M2JhYjM4ZTdiYzRiN2IyZTBmNjIwMDE5Yzc1ODdmMmQzYzM4YWVhYmQ2MzJkN2JjZjA3YzU2Y2I4MDU5NjQ0YmU5ZDIxNzkzN2YzN2MiLCJjdXN0b21EYXRhIjp7ImV4aXRJbmZvIjp7InRvYXN0RGVzYyI6bnVsbCwidG9hc3RJbWdVcmwiOm51bGx9fSwicGVuZGFudFR5cGUiOjEsImRpc3BsYXlUeXBlIjoyLCJzaW5nbGVQYWdlSWQiOjAsInNpbmdsZVN1YlBhZ2VJZCI6MCwiY2hhbm5lbCI6MCwiY291bnRkb3duUmVwb3J0Ijp0cnVlLCJ0aGVtZVR5cGUiOjAsIm1peGVkQWQiOnRydWUsImZ1bGxNaXhlZCI6dHJ1ZSwiYXV0b1JlcG9ydCI6dHJ1ZSwiZnJvbVRhc2tDZW50ZXIiOnRydWUsInNlYXJjaEluc3BpcmVTY2hlbWVJbmZvIjp7InNlYXJjaFF1ZXJ5Ijoi5aW96LSnIiwic2VhcmNoU2Vzc2lvbklkIjoiTVRjMU56TTFOVE0zT0RjeE5GOWpiRzkxWkMweU1qWTBNVGMxTFRFeU1qRTROall0TVRBNE5EYzVOeTB5TURBdFpHVndiRzk1TFRnMU9HSTVOelZtTkRZdGJEbHpZbXhmNWFXOTZMU25YekF1TURFME1ETTFNekF3TmpRM01EYzRNRE0iLCJlbnRlclNvdXJjZSI6IkFDVF9yZW53dV9hZF9ib3hfc2luZ2xlX2NvbCJ9LCJhbW91bnQiOjI1MDB9'
}
}
        self.task_stats={}
        for task_name in self.tasks_to_execute:
            if task_name in self.task_configs:
                self.task_stats[task_name]={
                    'success':0,
                    'failed':0,
                    'total_reward':0
}
        self.low_reward_streak=0
        self.submit_num=0
        self.execute_task_num=0
        self.stop_all_tasks=False
        self.task_limit_reached={}
        self.device_id_changed=False
        self.consecutive_danger_coin_count=0
        for task_name in self.tasks_to_execute:
            if task_name in self.task_configs:
                self.task_limit_reached[task_name]=False
    def extract_cookie_info(self):
        '提取Cookie信息'
        try:
            import re
            egid_match=re.search('egid=([^;]+)',self.cookie)
            oaid_match=re.search('oaid=([^;]+)',self.cookie)
            did_match=re.search('did=([^;]+)',self.cookie)
            user_id_match=re.search('userId=([^;]+)',self.cookie)
            api_st_match=re.search('kuaishou\.api_st=([^;]+)',self.cookie)
            app_ver_match=re.search('appver=([^;]+)',self.cookie)
            ver_match=re.search('ver=([^;]+)',self.cookie)
            sys_match=re.search('sys=([^;]+)',self.cookie)
            net_match=re.search('net=([^;]+)',self.cookie)
            isp_match=re.search('isp=([^;]+)',self.cookie)
            did_tag_match=re.search('did_tag=([^;]+)',self.cookie)
            kcv_match=re.search('kcv=([^;]+)',self.cookie)
            oDid_match=re.search('oDid=([^;]+)',self.cookie)
            boardPlatform_match=re.search('boardPlatform=([^;]+)',self.cookie)
            newOc_match=re.search('newOc=([^;]+)',self.cookie)
            androidApiLevel_match=re.search('androidApiLevel=([^;]+)',self.cookie)
            nbh_match=re.search('nbh=([^;]+)',self.cookie)
            did_gt_match=re.search('did=([^;]+)',self.cookie)
            cdid_tag_match=re.search('cdid=([^;]+)',self.cookie)
            sbh_match=re.search('sbh=([^;]+)',self.cookie)
            rdid_match=re.search('rdid=([^;]+)',self.cookie)
            totalMemory_match=re.search('totalMemory=([^;]+)',self.cookie)
            sw_match=re.search('sw=([^;]+)',self.cookie)
            sh_match=re.search('sh=([^;]+)',self.cookie)
            socName_match=re.search('socName=([^;]+)',self.cookie)
            mod_match=re.search('mod=([^;]+)',self.cookie)
            uQaTag_match=re.search('uQaTag=([^;]+)',self.cookie)
            self.egid=egid_match.group(1)if egid_match else ''
            self.oaid=oaid_match.group(1)if oaid_match else ''
            self.device_id=did_match.group(1)if did_match else ''
            self.user_id=user_id_match.group(1)if user_id_match else ''
            self.kuaishou_api_st=api_st_match.group(1)if api_st_match else ''
            self.app_version=app_ver_match.group(1)if app_ver_match else '13.6.50.43191'
            self.ver=ver_match.group(1)[:4]if ver_match else '13.6'
            self.sys=sys_match.group(1)if sys_match else 'ANDROID_15'
            self.net=net_match.group(1)if net_match else '5G'
            self.isp=isp_match.group(1)if isp_match else 'CUCC'
            self.did_tag=did_tag_match.group(1)if did_tag_match else '0'
            self.kcv=kcv_match.group(1)if kcv_match else '1599'
            self.oDid=oDid_match.group(1)if oDid_match else 'ANDROID_1456ddbf4a2860a9'
            self.boardPlatform=boardPlatform_match.group(1)if boardPlatform_match else 'lahaina'
            self.newOc=newOc_match.group(1)if newOc_match else 'OPPO'
            self.androidApiLevel=androidApiLevel_match.group(1)if androidApiLevel_match else '35'
            self.nbh=nbh_match.group(1)if nbh_match else '0'
            self.did_gt=did_gt_match.group(1)if did_gt_match else '1757780356571'
            self.cdid_tag=cdid_tag_match.group(1)if cdid_tag_match else '2'
            self.sbh=sbh_match.group(1)if sbh_match else '110'
            self.rdid=rdid_match.group(1)if rdid_match else ''
            self.totalMemory=totalMemory_match.group(1)if totalMemory_match else '15160'
            self.sw=sw_match.group(1)if sw_match else '1080'
            self.sh=sh_match.group(1)if sh_match else '2400'
            self.socName=socName_match.group(1)if socName_match else 'Qualcomm Snapdragon 8650'
            self.mod=mod_match.group(1)if mod_match else 'Xiaomi(M2011K2C)'
            self.uQaTag=uQaTag_match.group(1)if uQaTag_match else ''
            if not self.egid or not self.device_id:
                logger.warning(f"账号[{self.nickname}] cookie格式可能无 egid 或 did，但继续尝试...")
            self._load_cached_did()
        except Exception as e:
            logger.error(f"账号[{self.nickname}] 解析cookie失败: {e}")
    def _load_cached_did(self):
        '加载可用的did缓存'
        cache_file=os.path.join(os.getcwd(),'valid_dids.json')
        if os.path.exists(cache_file):
            try:
                with open(cache_file,'r',encoding='utf-8')as f:
                    cache=json.load(f)
                account_id=getattr(self,'user_id',self.nickname)
                if account_id in cache:
                    cached_data=cache[account_id]
                    self.device_id=cached_data.get('device_id',self.device_id)
                    self.egid=cached_data.get('egid',self.egid)
            except Exception as e:
                logger.debug(f"读取缓存失败: {e}")
        self.last_saved_did=self.device_id
        self.last_saved_egid=self.egid
    def _save_cached_did(self):
        '保存可用的did缓存'
        if getattr(self,'last_saved_did',None)==self.device_id and getattr(self,'last_saved_egid',None)==self.egid:
            return
        cache_file=os.path.join(os.getcwd(),'valid_dids.json')
        try:
            cache={}
            if os.path.exists(cache_file):
                try:
                    with open(cache_file,'r',encoding='utf-8')as f:
                        cache=json.load(f)
                except:
                    pass
            account_id=getattr(self,'user_id',self.nickname)
            if account_id not in cache or cache[account_id].get('device_id')!=self.device_id or cache[account_id].get('egid')!=self.egid:
                cache[account_id]={
                    'device_id':self.device_id,
                    'egid':self.egid,
                    'update_time':time.strftime('%Y-%m-%d %H:%M:%S')
}
                with open(cache_file,'w',encoding='utf-8')as f:
                    json.dump(cache,f,indent=4,ensure_ascii=False)
            self.last_saved_did=self.device_id
            self.last_saved_egid=self.egid
        except Exception as e:
            logger.debug(f"保存缓存失败: {e}")
    def _get_task_config(self,task_name:str)->Optional[Dict]:
        '获取任务配置'
        config=self.task_configs.get(task_name)
        if not config:
            return None
        if task_name=='play':
            config=config.copy()
            _b=7037    # business_id
            _p=24068   # pos_id
            _s=100026368  # sub_page_id
            _g=100011251  # page_id
            config['business_id']=_b
            config['pos_id']=_p
            config['sub_page_id']=_s
            config['page_id']=_g
        elif task_name=='cn':
            config=config.copy()
            _b=7075    # business_id
            _p=216267   # pos_id
            _s=100161535  # sub_page_id
            _g=10014  # page_id
            config['business_id']=_b
            config['pos_id']=_p
            config['sub_page_id']=_s
            config['page_id']=_g
        elif task_name=='see':
            config=config.copy()
            _b=7042    # business_id
            _p=20578   # pos_id
            _s=100024209  # sub_page_id
            _g=100011251  # page_id
            config['business_id']=_b
            config['pos_id']=_p
            config['sub_page_id']=_s
            config['page_id']=_g
        return config
    async def _get_imp_ext_data(self,task_config:Dict)->str:
        if task_config.get('name')in['搜索广告','内容广告','看奖广告']:
            link_url=task_config.get('linkUrl','')
            search_key=get_search_value()
            return json.dumps({
                'openH5AdCount':2,
                'sessionLookedCompletedCount':'1',
                'sessionType':'1',
                'searchKey':search_key,
                'triggerType':'2',
                'disableReportToast':'true',
                'businessEnterAction':'7',
                'neoParams':link_url
},separators=(',',':'))
        else:
            return '{}'
    async def check_coin_limit(self)->bool:
        '检查金币限制'
        try:
            basic_info=await get_account_basic_info(self.cookie,self.proxy_url,self.index)
            if basic_info and basic_info['total_coin']:
                total_coin=int(basic_info['total_coin'])
                if total_coin>=self.coin_limit:
                    logger.warning(
                        f"⚠️ 账号[{self.nickname}] 金币已达 {total_coin}，超过 {self.coin_limit} 阈值，将停止任务 [备注：超过金币阈值（KS_COIN_LIMIT={COIN_LIMIT})]")
                    self.coin_exceeded=True
                    self.stop_all_tasks=True
                    return True
            return False
        except Exception as e:
            logger.error(f"账号[{self.nickname}] 金币检查异常: {e}")
            return False
    def get_task_stats(self)->Dict:
        '获取任务统计'
        return self.task_stats
    def print_task_stats(self):
        '打印任务统计'
        logger.info(f"账号[{self.nickname}] 任务执行统计:")
        for task_name,stats in self.task_stats.items():
            task_display_name=self.task_configs[task_name]['name']
            logger.info(
                f"{task_display_name}: 成功{stats['success']}次, 失败{stats['failed']}次, 总奖励{stats['total_reward']}金币")
    async def retry_operation(self,operation,operation_name:str,
                              max_retries:int=3,delay:int=2000):
        '重试操作'
        attempt=0
        last_error=None
        while attempt<max_retries:
            try:
                result=await operation()
                if result:
                    return result
                last_error=Exception(f"{operation_name} 返回空结果")
            except Exception as e:
                last_error=e
                logger.error(f"账号[{self.nickname}] {operation_name} 异常: {e}")
            attempt+=1
            if attempt<=max_retries:
                logger.info(f"账号[{self.nickname}] {operation_name}失败，重试 {attempt}/{max_retries}")
                await asyncio.sleep(delay/1000)
        if DEV_MODE and last_error:
            logger.debug(f"[调试] {operation_name} 最终失败: {last_error}")
        return None
    async def get_ad_info(self,page:str,task_config:Dict)->Optional[Dict]:
        '获取广告信息'
        try:
            ad_path='/rest/e/reward/mixed/ad'
            base_params={
                'encData':'',
                'sign':'',
                'cs':'false',
                'client_key':'3c2cd3f3',
                'videoModelCrowdTag':'1_23',
                'os':'android',
                'kuaishou.api_st':self.kuaishou_api_st,
                'uQaTag':'1##swLdgl:99#ecPp:-9#cmNt:-0#cmHs:-3#cmMnsl:-0'
}
            device_params={
                'earphoneMode':'1'
}
            request_body={
                'appInfo':{
                    'appId':'kuaishou',
                    'name':'快手',
                    'packageName':'com.smile.gifmaker',
                    'version':self.app_version,
                    'versionCode':-1
},
                'deviceInfo':{
                    'osType':1,
                    'osVersion':'15',
                    'language':'zh',
                    'deviceId':self.device_id,
                    'screenSize':{
                        'width':1080,
                        'height':2249
},
                    'ftt':''
},
                'networkInfo':{
                    'ip':'192.168.1.159',
                    'connectionType':4
},
                'geoInfo':{
                    'latitude':0,
                    'longitude':0
},
                'userInfo':{
                    'userId':self.user_id,
                    'age':0,
                    'gender':''
},
                'impInfo':[{
                    'pageId':task_config['page_id'],
                    'subPageId':task_config['sub_page_id'],
                    'action':0,
                    'browseType':3 if task_config.get('name')!='搜索广告' else 4,
                    'impExtData':await self._get_imp_ext_data(task_config),
                    'mediaExtData':'{}'
}]
}
            request_body_b64=base64.b64encode(json.dumps(request_body).encode()).decode()
            # 第一步：获取encsign签名
            encsign_result=await self.get_encsign(request_body_b64)
            if not encsign_result:
                logger.error(f"❌ 账号[{self.nickname}] encsign失败，无法获取{task_config['name']}")
                return None
            # 填入真实的encData和sign
            base_params['encData']=encsign_result.get('encdata','')
            base_params['sign']=encsign_result.get('sign','')
            # 第二步：获取nssig签名
            nssig_result=await self.request_nssig_service({
                'urlpath':ad_path,
                'reqdata':urlencode({**device_params,**base_params}),
                'api_client_salt':self.salt
},f"账号[{self.nickname}] 生成广告签名")
            if not nssig_result:
                logger.error(f"❌ 账号[{self.nickname}] nssig失败，无法获取{task_config['name']}")
                return None
            signature_data={
                'sig':nssig_result['sig'],
                '__NS_sig3':nssig_result['__NS_sig3'],
                '__NStokensig':nssig_result['__NStokensig'],
                'encData':encsign_result.get('encdata',''),
                'sign':encsign_result.get('sign','')
}
            final_params={
**device_params,
                'sig':signature_data['sig'],
                '__NS_sig3':signature_data['__NS_sig3'],
                '__NS_xfalcon':'',
                '__NStokensig':signature_data['__NStokensig']
}
            base_params['encData']=signature_data['encData']
            base_params['sign']=signature_data['sign']
            url=f"https://api.e.kuaishou.cn{ad_path}?{urlencode(final_params)}"
            headers={
                'Host':'api.e.kuaishou.cn',
                'Connection':'keep-alive',
                'X-REQUESTID':'175912631607460914',
                'Accept-Language':'zh-cn',
                'Cookie':f'__NSWJ=;kuaishou_api_st={self.kuaishou_api_st}',
                'ct-context':'{"biz_name":"ATTRIBUTION","error_occurred":false,"sampled":true,"sampled_on_error":true,"segment_id":748334165,"service_name":"CLIENT_TRACE","span_id":1,"trace_id":"My45MTE3NzYwNjY5NjY4MzU1MzExLjYyMTQuMTc2MTk1NTk1MTcxOC4x","upstream_error_occurred":false}',
                'page-code':page,
                'kaw':'MDHkM+9FrbzPSEAqyw6JaWODbXT2Z2h3Z63YJ4O/5X6oLTOx1rTjDZjtwt/T5Fhuu6x0WdZCiG2hrnutaaAO4tegnuHwL6zhn43hBjhhCt4OomV5wJGFzNYAJlsksNvBo9ww0w+eS2OA9s6TzeLiwmuBbZMT9xELXoFlZlJ2YVhQ3kOf/h3R18hWhPeqoRFr4sOTmL+rU8xmufAbR4pncGmwX4vDs6YsBY+kx/tF5lyCNnEQzN9iXINqHCCOocJ0AA==',
                'kas':'0012da23b681b08de055b21d98498e8621',
                'User-Agent':'kwai-android aegon/4.27.0',
                'Content-Type':'application/x-www-form-urlencoded',
                'Accept-Encoding':'gzip, deflate, br',
                'X-Client-Info':'model=M2011K2C;os=Android;nqe-score=37;network=OTHER;signal-strength=1;'
}
            async with aiohttp.ClientSession()as session:
                response=await make_http_request(
                    session,'POST',url,
                    proxy_url=self.proxy_url,
                    headers=headers,
                    data=base_params,
                    timeout=12,
                    request_name=f"账号[{self.nickname}] 获取广告"
)
                if not response:
                    logger.info(f"❌ 账号[{self.nickname}]获取广告信息为 {response}，请更换代理后进行重试")
                    return None
                llsid_val=response.get('llsid')
                result_val=response.get('result')
                if llsid_val is not None and str(llsid_val)=='0' and result_val is not None and str(result_val)=='1':
                    logger.info(f"❌ 账号[{self.nickname}] 获取广告数据失败：result = {result_val},msg = {response.get('errorMsg')}")
                    if not hasattr(self,'antispam_streak'):
                        self.antispam_streak=0
                    self.antispam_streak+=1
                    logger.warning(f"⚠️ 账号[{self.nickname}] 重试次数: {self.antispam_streak}/5")
                    if self.antispam_streak>=5:
                        logger.warning(f"🚨 账号[{self.nickname}] 连续失败5次，{SLEEP_TIME}分钟后重试...")
                        self.antispam_streak=0
                        await asyncio.sleep(SLEEP_TIME*60)
                    else:
                        await asyncio.sleep(10)
                    return await self.get_ad_info(page,task_config)
                else:
                    self.antispam_streak=0
                if(response.get('errorMsg')=='OK' and
                        response.get('feeds')and
                        len(response['feeds'])>0 and
                        response['feeds'][0].get('ad')):
                    feed=response['feeds'][0]
                    caption=feed.get('caption')or feed.get('ad',{}).get('caption','')
                    exp_tag=feed.get('exp_tag','')
                    llsid=''
                    if exp_tag and '/' in exp_tag:
                        parts=exp_tag.split('/')[1].split('_')if len(exp_tag.split('/'))>1 else[]
                        llsid=parts[0]if parts else ''
                    now_time=int(time.time()*1000)
                    liveStreamId=feed.get('liveStreamId','')
                    if liveStreamId:
                        feed_id={'feedId':liveStreamId}
                    else:
                        feed_id={}
                    ad_data_v2=feed.get('ad',{}).get('adDataV2',{})
                    inspireAdInfo=ad_data_v2.get('inspireAdInfo',{})
                    adExtInfo=inspireAdInfo.get('adExtInfo','')
                    neoparams=inspireAdInfo.get('neoParams','')
                    once_again_info=ad_data_v2.get('onceAgainRewardInfo',{})
                    has_more=once_again_info.get('hasMore',False)
                    posid=ad_data_v2.get('posId','')
                    sessionid=response.get('searchSessionId',f'adNeo-500668049-100026367-{now_time}')
                    ad_ext_data=feed.get('ad',{}).get('extData',{})
                    ext_data_dict=json.loads(ad_ext_data)
                    award_coin=ext_data_dict.get('awardCoin')
                    return{
                        'cid':feed['ad']['creativeId'],
                        'llsid':response.get('llsid',None),
                        'adExtInfo':adExtInfo,
                        'posid':posid,
                        'sessionid':sessionid,
                        'hasRewardEnd':has_more,
                        'award_coin':award_coin,
                        'feed_id':feed_id,
                        'feedtype':response.get('feedType',0),
                        'neoparams':neoparams
}
                if llsid_val is None:
                    logger.info(f"❌ 账号[{self.nickname}] 获取广告数据失败：result = {result_val},msg = {response.get('errorMsg')}")
                elif result_val is not None and int(result_val)!=1:
                    logger.info(f"❌ 账号[{self.nickname}] 获取广告数据失败：result = {result_val},msg = {response.get('error_msg')}")
                if DEV_MODE:
                    logger.debug(f"[调试] getAdInfo 原始响应: {json.dumps(response)}")
                return None
        except Exception as e:
            logger.error(f"❌ 账号[{self.nickname}] 获取广告异常: {e}")
            return None
    async def generate_signature(self,creative_id:str,llsid:str,adExtInfo:str,posid:str,sessionid:str,
                                 feed_id,feedtype,neoparams,
                                 task_name:str,task_config:Dict,award_coin=None)->Optional[Dict]:
        '生成签名'
        if feedtype:
            mediaScene='live'
        else:
            mediaScene='video'
        now_time=int(time.time()*1000)
        try:
            if not MODE_CHANGE:
                if award_coin==1 or award_coin=='1' or not award_coin:
                    neo_infos=[
{
                            'creativeId':creative_id,
                            'extInfo':neoparams,
**feed_id,
                            'llsid':llsid,
                            'adExtInfo':adExtInfo,
                            'requestSceneType':task_config['request_scene_type'],
                            'taskType':23,
                            'watchExpId':'',
                            'watchStage':0
},{
                            'creativeId':creative_id,
                            'extInfo':neoparams,
**feed_id,
                            'llsid':llsid,
                            'adExtInfo':adExtInfo,
                            'requestSceneType':1,
                            'taskType':1,
                            'watchExpId':'',
                            'watchStage':0
},
]
                else:
                    neo_infos=[
{
                            'creativeId':creative_id,
                            'extInfo':neoparams,
**feed_id,
                            'llsid':llsid,
                            'adExtInfo':adExtInfo,
                            'requestSceneType':1,
                            'taskType':2,
                            'watchExpId':'',
                            'watchStage':0
},
{
                            'creativeId':creative_id,
                            'extInfo':neoparams,
**feed_id,
                            'llsid':llsid,
                            'adExtInfo':adExtInfo,
                            'requestSceneType':7,
                            'taskType':2,
                            'watchExpId':'',
                            'watchStage':0
},
]
            else:
                if award_coin==1 or award_coin=='1' or not award_coin:
                    neo_infos=[
{
                            'creativeId':creative_id,
                            'extInfo':neoparams,
**feed_id,
                            'llsid':llsid,
                            'adExtInfo':adExtInfo,
                            'requestSceneType':task_config['request_scene_type'],
                            'taskType':3,
                            'watchExpId':'',
                            'watchStage':0
},{
                            'creativeId':creative_id,
                            'extInfo':neoparams,
**feed_id,
                            'llsid':llsid,
                            'adExtInfo':adExtInfo,
                            'requestSceneType':1,
                            'taskType':1,
                            'watchExpId':'',
                            'watchStage':0
}
]
                else:
                    neo_infos=[
{
                            'creativeId':creative_id,
                            'extInfo':neoparams,
**feed_id,
                            'llsid':llsid,
                            'adExtInfo':adExtInfo,
                            'requestSceneType':1,
                            'taskType':1,
                            'watchExpId':'',
                            'watchStage':0
}
,
{
                            'creativeId':creative_id,
                            'extInfo':neoparams,
**feed_id,
                            'llsid':llsid,
                            'adExtInfo':adExtInfo,
                            'requestSceneType':7,
                            'taskType':2,
                            'watchExpId':'',
                            'watchStage':0
},
{
                            'creativeId':creative_id,
                            'extInfo':neoparams,
**feed_id,
                            'llsid':llsid,
                            'adExtInfo':adExtInfo,
                            'requestSceneType':task_config['request_scene_type'],
                            'taskType':4,
                            'watchExpId':'',
                            'watchStage':0
},{
                            'creativeId':creative_id,
                            'extInfo':neoparams,
**feed_id,
                            'llsid':llsid,
                            'adExtInfo':adExtInfo,
                            'requestSceneType':task_config['request_scene_type'],
                            'taskType':6,
                            'watchExpId':'',
                            'watchStage':0
},
{
                            'creativeId':creative_id,
                            'extInfo':neoparams,
**feed_id,
                            'llsid':llsid,
                            'adExtInfo':adExtInfo,
                            'requestSceneType':7,
                            'taskType':20,
                            'watchExpId':'',
                            'watchStage':0
},
{
                            'creativeId':creative_id,
                            'extInfo':neoparams,
**feed_id,
                            'llsid':llsid,
                            'adExtInfo':adExtInfo,
                            'requestSceneType':task_config['request_scene_type'],
                            'taskType':23,
                            'watchExpId':'',
                            'watchStage':0
}
]
            biz_data={
                'businessId':task_config['business_id'],
                'endTime':now_time+5693,
                'extParams':'',
                'mediaScene':mediaScene,
                'neoInfos':neo_infos,
                'pageId':task_config['page_id'],
                'posId':posid,
                'reportType':0,
                'sessionId':sessionid,
                'startTime':now_time-25562,
                'subPageId':task_config['sub_page_id']
}
            payload={
                'bizStr':json.dumps(biz_data,separators=(',',':')),
                'cs':'false',
                'client_key':'3c2cd3f3',
                'videoModelCrowdTag':'1_23',
                'os':'android',
                'kuaishou.api_st':self.kuaishou_api_st,
                'uQaTag':'66113##cmWns:-3#swRs:-9#swLdgl:-9#ecPp:-0#cmNt:-1#cmHs:-1#cmAu:-3'
}
            url_param={
                'earphoneMode':'1',
                'mod':self.mod,
                'appver':self.app_version,
                'isp':self.isp,
                'language':'zh-cn',
                'ud':self.user_id,
                'did_tag':self.did_tag,
                'egid':self.egid,
                'thermal':'10000',
                'net':self.net,
                'kcv':self.kcv,
                'app':'0',
                'kpf':'ANDROID_PHONE',
                'bottom_navigation':'true',
                'ver':self.ver,
                'android_os':'0',
                'oDid':self.oDid,
                'boardPlatform':self.boardPlatform,
                'kpn':'KUAISHOU',
                'newOc':'OPPO',
                'androidApiLevel':self.androidApiLevel,
                'slh':'0',
                'country_code':'cn',
                'nbh':self.nbh,
                'hotfix_ver':'',
                'did_gt':self.did_gt,
                'apilnvokeTiming':'ON_HOME_PAGE_CREATED',
                'keyconfig_state':'2',
                'cdid_tag':self.cdid_tag,
                'sys':self.sys,
                'max_memory':'256',
                'oc':'OPPO',
                'sh':self.sh,
                'deviceBit':'0',
                'browseType':'3',
                'ddpi':'560',
                'socName':self.socName,
                'is_background':'0',
                'c':'OPPO',
                'sw':self.sw,
                'ftt':'',
                'apptype':'22',
                'abi':'arm64',
                'userRecoBit':'0',
                'device_abi':'arm64',
                'icaver':'1',
                'totalMemory':self.totalMemory,
                'grant_browse_type':'AUTHORIZED',
                'iuid':'',
                'rdid':self.rdid,
                'sbh':self.sbh,
                'darkMode':'false',
                'did':self.device_id,
}
            new_dict=copy.deepcopy(url_param)
            new_dict.update(payload)
            urldata=''
            for key,value in sorted(new_dict.items()):
                if urldata:
                    urldata+='&'
                urldata+=f"{quote(str(key), safe='')}={quote(str(value), safe='')}"
            signature_result=await self.request_nssig_service({
                'urlpath':self.task_report_path,
                'reqdata':urldata,
                'api_client_salt':self.salt
},f"账号[{self.nickname}] 生成报告签名")
            if not signature_result:
                return None
            return{
                'sig':signature_result['sig'],
                'sig3':signature_result['__NS_sig3'],
                'sigtoken':signature_result['__NStokensig'],
                'post':payload,
                'url_param':url_param
}
        except Exception as e:
            logger.error(f"❌ 账号[{self.nickname}] 生成签名异常: {e}")
            return None
    async def generate_signature_v2(self,url_path:str,url_data:str,
                                    salt:str,req_str:str)->Optional[Dict]:
        '生成签名V2（使用encsign+nssig）'
        # 第一步：获取encsign签名
        encsign_result=await self.get_encsign(req_str)
        if not encsign_result:
            logger.error(f"❌ 账号[{self.nickname}] encsign签名失败")
            return None
        enc_data=encsign_result.get('encdata','')
        sign_val=encsign_result.get('sign','')
        # 第二步：将encData和sign加入url_data，获取nssig签名
        # 替换占位符
        updated_url_data=url_data.replace('|encData|',quote(enc_data,safe='')).replace('|sign|',quote(sign_val,safe=''))
        nssig_result=await self.request_nssig_service({
            'urlpath':url_path,
            'reqdata':updated_url_data,
            'api_client_salt':salt
},f"账号[{self.nickname}] 生成广告签名")
        if not nssig_result:
            logger.error(f"❌ 账号[{self.nickname}] nssig签名失败")
            return None
        return{
            'sig':nssig_result['sig'],
            '__NS_sig3':nssig_result['__NS_sig3'],
            '__NStokensig':nssig_result['__NStokensig'],
            'encData':enc_data,
            'sign':sign_val
}
    async def submit_report(self,sig:str,sig3:str,sigtoken:str,
                            post_data:str,url_param:str,page:str,task_name:str,task_config:Dict,
                            is_additional:bool=False,award_coin:Optional[int]=None)->Dict:
        """提交任务报告
        is_additional: 是否为追加模式任务，如果是追加任务则不输出金币奖励日志
        
        """
        try:
            url=(
                f"https://api.e.kuaishou.cn{self.task_report_path}?{urlencode(url_param)}&sig={sig}&__NS_sig3={sig3}&__NS_xfalcon=;&__NStokensig={sigtoken}")
            headers={
                'Host':'api.e.kuaishou.cn',
                'Connection':'keep-alive',
                'X-REQUESTID':'175912636245416273',
                'User-Agent':'kwai-android aegon/3.56.0',
                'Accept-Language':'zh-cn',
                'Cookie':f'kuaishou_api_st={self.kuaishou_api_st}',
                'ct-context':'{"biz_name":"ATTRIBUTION","error_occurred":false,"sampled":true,"sampled_on_error":true,"segment_id":1781103420,"service_name":"CLIENT_TRACE","span_id":1,"trace_id":"My4xMjA0MjgyOTE4ODkzNDk4MTEyMC4yNjQ3My4xNzU5MTI2MzYyNDU3LjEx","upstream_error_occurred":false}',
                'page-code':page,
                'kaw':'MDHkM+9FrbzPSEAqyw6JaWODbXTwZGh3Z63YJ4O/5X6oLTOx1rTjDZjtwt/T5Fhqu6x0WdZCiG2hrnutaaAA4tegnuHwL6zhn43hBjhhCt4OomV5wJGFzNYAJlsksNvBo9ww0w+eS2OA9s6TzeLiw2uBY5MT9xELXoFlZlJ2YVhQ3kOf+hjR0c9XhfOrphFr4sOTmL+rU8xmufAbR4pncGmwX4vDs6YsBY+kx/tF5lyCNnEQzN9iXINqHCCOocJ0AA==',
                'kas':'0014d270b4d2e38ce35eb21b991ad6d674',
                'Content-Type':'application/x-www-form-urlencoded',
                'Accept-Encoding':'gzip, deflate, br',
                'X-Client-Info':'model=M2011K2C;os=Android;nqe-score=37;network=OTHER;signal-strength=2;'
}
            connector=None
            if self.proxy_url:
                try:
                    from aiohttp_socks import ProxyConnector
                    connector=ProxyConnector.from_url(self.proxy_url)
                    if DEV_MODE:
                        logger.debug(f"[调试] 账号[{self.nickname}] 完整代理URL: {self.proxy_url}")
                except Exception as e:
                    logger.error(f"[错误] 账号[{self.nickname}]代理URL无效({e})，尝试直连模式")
            else:
                if DEV_MODE:
                    logger.debug(f"[调试] 账号[{self.nickname}]未配置代理，使用直连模式")
            timeout_obj=aiohttp.ClientTimeout(total=12)
            if connector:
                async with aiohttp.ClientSession(connector=connector,timeout=timeout_obj)as proxy_session:
                    async with proxy_session.post(url,headers=headers,data=post_data)as response:
                        if response.status !=200:
                            return{'success':False,'reward':0}
                        result=await response.json()
            else:
                async with aiohttp.ClientSession(timeout=timeout_obj)as session:
                    async with session.post(url,headers=headers,data=post_data)as response:
                        if response.status !=200:
                            return{'success':False,'reward':0}
                        result=await response.json()
            if result.get('result')==1:
                self.submit_num=0
                reward=result.get('data',{}).get('neoAmount',0)
                self._save_cached_did()
                if not is_additional:
                    self.count+=reward
                    if award_coin is not None:
                        logger.info(
                            f"💰 账号[{self.nickname}] {task_config['name']} 预计[{award_coin}]，实际[{reward}]金币！-> [{self.count}]")
                    else:
                        logger.info(f"💰 账号[{self.nickname}] {task_config['name']} 获得{reward}金币！-> [{self.count}]")
                CHANGE_DID=int(os.getenv('CHANGE_DID',0))
                reward_danger_coin=list(map(int,DANGER_COIN.strip('[]').split(',')))
                if reward<=self.low_reward_threshold:
                    self.low_reward_streak+=1
                    if self.low_reward_streak>self.low_reward_limit:
                        logger.info(
                            f"🏁 账号[{self.nickname}] 连续{self.low_reward_limit}次奖励≤{self.low_reward_threshold}，停止全部任务")
                        self.stop_all_tasks=True
                else:
                    self.low_reward_streak=0
                if not self.stop_all_tasks:
                    if reward in reward_danger_coin:
                        if getattr(self,'did_change_count',0)<CHANGE_DID_TIMES:
                            self.device_id=generate_device_id()
                            self.egid=generate_egid()
                            self.did_change_count=getattr(self,'did_change_count',0)+1
                            logger.warning(f"⚠️ 账号[{self.nickname}] 获得危险金币{reward}，更换MK神秘参数")
                        else:
                            logger.warning(f"🚨 账号[{self.nickname}] 本轮更换神秘参数已上限，停止该账号运行")
                            self.stop_all_tasks=True
                    elif CHANGE_DID:
                        change_did_range=list(map(int,CHANGE_DID_RANGE.strip('[]').split(',')))
                        if len(change_did_range)>=2:
                            min_range=change_did_range[0]
                            max_range=change_did_range[1]
                        else:
                            min_range=10
                            max_range=100
                            logger.warning('⚠️ CHANGE_DID_RANGE格式不正确，使用默认值[10,100]')
                        is_in_range=(min_range<reward<max_range)
                        if is_in_range:
                            if getattr(self,'did_change_count',0)<CHANGE_DID_TIMES:
                                self.device_id=generate_device_id()
                                self.egid=generate_egid()
                                self.did_change_count=getattr(self,'did_change_count',0)+1
                                logger.warning(f"⚠️ 账号[{self.nickname}] 获得金币过低，更换MK神秘参数")
                            else:
                                pass
                return{'success':True,'reward':reward}
            if result.get('result')in[20107,20108,1003,415]:
                logger.warning(f"⚠️ 账号[{self.nickname}] {task_config['name']} 已达上限")
                self.task_limit_reached[task_name]=True
                return{'success':False,'reward':0}
            logger.error(
                f"❌ 账号[{self.nickname}] {task_config['name']} 奖励失败，result={result.get('result')} msg={result.get('data', '')}")
            self.submit_num+=1
            if DEV_MODE:
                logger.debug(f"[调试] submitReport 原始响应: {json.dumps(result)}")
            if self.submit_num>=3:
                logger.warning(f"⚠️ 账号[{self.nickname}] {task_config['name']} 提交任务失败3次，停止该任务")
                self.stop_all_tasks=True
                return{'success':False,'reward':0}
            return{'success':False,'reward':0}
        except Exception as e:
            logger.error(f"❌ 账号[{self.nickname}] 提交任务异常: {e}")
            return{'success':False,'reward':0}
    async def get_encsign(self,encoded_data:str)->Optional[Dict]:
        '获取encsign签名（直连上游，无需卡密）'
        try:
            dynamic_key=generate_dynamic_api_key()
            sign_request=json.dumps({'data':encoded_data,'timestamp':dynamic_key['timestamp']})
            timeout_obj=aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout_obj)as session:
                async with session.post(
                    f"{SIGN_BASE_URL}/encsign",
                    data=sign_request,
                    headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0'}
)as resp:
                    resp_text=await resp.text()
                    if resp.status!=200:
                        logger.error(f"❌ 账号[{self.nickname}] encsign HTTP状态码异常: {resp.status}，响应: {resp_text[:200]}")
                        return None
                    try:
                        result=json.loads(resp_text)
                    except:
                        logger.error(f"❌ 账号[{self.nickname}] encsign响应非JSON: {resp_text[:200]}")
                        return None
                    if result.get('status'):
                       # logger.info(f"✅ 账号[{self.nickname}] encsign签名成功")
                        return result.get('data')
                    else:
                        error_msg=result.get('error','未知错误')
                        logger.error(f"❌ 账号[{self.nickname}] encsign签名失败: {error_msg}")
                        return None
        except asyncio.TimeoutError:
            logger.error(f"❌ 账号[{self.nickname}] encsign请求超时（15秒），签名服务可能无法访问: {SIGN_BASE_URL}/encsign")
            return None
        except Exception as e:
            logger.error(f"❌ 账号[{self.nickname}] encsign签名异常: {e}")
            return None
    async def request_nssig_service(self,request_data:Dict,request_name:str)->Optional[Dict]:
        '请求nssig签名服务（直连上游，无需卡密）'
        try:
            sign_request=json.dumps({
                'salt':request_data.get('api_client_salt',''),
                'path':request_data.get('urlpath',''),
                'data':request_data.get('reqdata','')
})
            timeout_obj=aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout_obj)as session:
                async with session.post(
                    f"{SIGN_BASE_URL}/nssig",
                    data=sign_request,
                    headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0'}
)as resp:
                    resp_text=await resp.text()
                    if resp.status!=200:
                        logger.error(f"❌ 账号[{self.nickname}] nssig HTTP状态码异常: {resp.status}，响应: {resp_text[:200]}")
                        return None
                    try:
                        result=json.loads(resp_text)
                    except:
                        logger.error(f"❌ 账号[{self.nickname}] nssig响应非JSON: {resp_text[:200]}")
                        return None
                    if result.get('status'):
                        sig_data=result.get('data',{})
                       # logger.info(f"✅ 账号[{self.nickname}] nssig签名成功")
                        return{
                            'sig':sig_data.get('sig',''),
                            '__NStokensig':sig_data.get('nstokensig',''),
                            '__NS_sig3':sig_data.get('nssig3',''),
                            '__NS_xfalcon':sig_data.get('xfalcon','')
}
                    else:
                        error_msg=result.get('error','未知错误')
                        logger.error(f"❌ 账号[{self.nickname}] nssig签名失败: {error_msg}")
                        return None
        except asyncio.TimeoutError:
            logger.error(f"❌ 账号[{self.nickname}] nssig请求超时（15秒），签名服务可能无法访问: {SIGN_BASE_URL}/nssig")
            return None
        except Exception as e:
            logger.error(f"❌ 账号[{self.nickname}] nssig签名异常: {e}")
            return None
    async def execute_task(self,task_name:str,is_additional:bool=False,
                           task_config_override:Dict=None)->Dict:
        """执行单个任务
        Args:
        task_name: 任务名称
        is_additional: 是否为追加模式任务
        task_config_override: 任务配置覆盖（用于追加模式）
        Returns:
        Dict: {"success": bool, "hasRewardEnd": bool}
        
        """
        task_config=task_config_override if task_config_override else self._get_task_config(task_name)
        if not task_config:
            logger.error(f"❌ 账号[{self.nickname}] 未知任务: {task_name}")
            return{'success':False,'hasRewardEnd':False}
        if self.task_limit_reached.get(task_name,False):
            return{'success':False,'hasRewardEnd':False}
        try:
            ad_info=await self.retry_operation(
                lambda:self.get_ad_info('NEW_TASK_CENTER',task_config),
                f"获取{task_config['name']}信息",
                3
)
            if not ad_info:
                self.execute_task_num+=1
                self.task_stats[task_name]['failed']+=1
                if self.execute_task_num>=3:
                    logger.warning(f"⚠️ 账号[{self.nickname}] {task_config['name']} 执行任务失败3次，停止所有任务")
                    self.stop_all_tasks=True
                return{'success':False,'hasRewardEnd':False}
            play_wait_time=list(map(int,PLAY_WAIT_TIME.strip('[]').split(',')))
            min_wait=play_wait_time[0]
            max_wait=play_wait_time[1]
            if int(min_wait)<30000:
                min_wait=30000
                max_wait=35000
            wait_time=random.randint(int(min_wait),int(max_wait))
            await asyncio.sleep(wait_time/1000)
            signature=await self.retry_operation(
                lambda:self.generate_signature(ad_info['cid'],ad_info['llsid'],ad_info['adExtInfo'],
                                                ad_info['posid'],ad_info['sessionid'],ad_info['feed_id'],
                                                ad_info['feedtype'],ad_info['neoparams'],task_name,task_config,ad_info.get('award_coin')),
                f"生成{task_config['name']}签名",
                3
)
            if not signature:
                self.execute_task_num+=1
                self.task_stats[task_name]['failed']+=1
                if self.execute_task_num>=3:
                    logger.warning(f"⚠️ 账号[{self.nickname}] {task_config['name']} 执行任务失败3次，停止所有任务")
                    self.stop_all_tasks=True
                return{'success':False,'hasRewardEnd':False}
            result=await self.retry_operation(
                lambda:self.submit_report(signature['sig'],signature['sig3'],
                                           signature['sigtoken'],signature['post'],signature['url_param'],
                                           'NEW_TASK_CENTER',
                                           task_name,task_config,is_additional,ad_info.get('award_coin')),
                f"提交{task_config['name']}报告",
                3
)
            if result and result.get('success'):
                self.execute_task_num=0
                self.task_stats[task_name]['success']+=1
                self.task_stats[task_name]['total_reward']+=result.get('reward',0)
                has_reward_end=ad_info.get('hasRewardEnd',False)
                return{'success':True,'hasRewardEnd':has_reward_end,'reward':result.get('reward',0),
                        'award_coin':ad_info.get('award_coin')}
            self.task_stats[task_name]['failed']+=1
            self.execute_task_num+=1
            if self.execute_task_num>=3:
                logger.warning(f"⚠️ 账号[{self.nickname}] {task_config['name']} 执行任务失败3次，停止所有任务")
                self.stop_all_tasks=True
            return{'success':False,'hasRewardEnd':False}
        except Exception as e:
            logger.error(f"❌ 账号[{self.nickname}] 任务异常({task_name}): {e}")
            self.execute_task_num+=1
            self.task_stats[task_name]['failed']+=1
            if self.execute_task_num>=3:
                logger.warning(f"⚠️ 账号[{self.nickname}] {task_config['name']} 执行任务失败3次，停止所有任务")
                self.stop_all_tasks=True
            return{'success':False,'hasRewardEnd':False}
    async def execute_all_tasks_by_priority(self)->Dict[str,bool]:
        '按优先级执行所有任务'
        results={}
        for task_name in self.tasks_to_execute:
            if self.stop_all_tasks:
                break
            if task_name not in self.task_configs:
                logger.warning(f"⚠️ 账号[{self.nickname}] 跳过未知任务: {task_name}")
                continue
            if self.task_limit_reached.get(task_name,False):
                continue
            additional_config=None
            if SUCCESS_AD_NUM>0:
                base_config=self._get_task_config(task_name)
                if base_config:
                    additional_config=base_config.copy()
                    additional_config['request_scene_type']=7
                    additional_config['task_type']=2
            for i in range(TASK_NUM_ROUND):
                if self.stop_all_tasks:
                    break
                if self.task_limit_reached.get(task_name,False):
                    break
                task_result=await self.execute_task(task_name,is_additional=False)
                if i==0:
                    results[task_name]=task_result.get('success',False)
                task_wait_time=list(map(int,WAIT_TIME.strip('[]').split(',')))
                min_wait=task_wait_time[0]
                max_wait=task_wait_time[1]
                wait_time=random.randint(int(min_wait),int(max_wait))
                await asyncio.sleep(wait_time/1000)
                if SUCCESS_AD_NUM>0 and task_result.get('success',False)and task_result.get('hasRewardEnd',
                                                                                                False)and additional_config:
                    logger.info(
                        f"📺 账号[{self.nickname}] {self.task_configs[task_name]['name']} 检测到追加广告，开始支线任务")
                    additional_count=0
                    max_additional=SUCCESS_AD_NUM
                    while additional_count<max_additional and not self.stop_all_tasks:
                        if self.task_limit_reached.get(task_name,False):
                            logger.warning(
                                f"⚠️ 账号[{self.nickname}] {self.task_configs[task_name]['name']} 任务已达上限，返回主线运行其他任务")
                            break
                        additional_task_result=await self.execute_task(task_name,is_additional=True,
                                                                         task_config_override=additional_config)
                        if self.task_limit_reached.get(task_name,False):
                            logger.warning(
                                f"⚠️ 账号[{self.nickname}] {self.task_configs[task_name]['name']} 任务已达上限，返回主线运行其他任务")
                            break
                        if additional_task_result.get('success',False):
                            additional_count+=1
                            reward=additional_task_result.get('reward',0)
                            award_coin=additional_task_result.get('award_coin')
                            self.count+=reward
                            if reward==10:
                                if award_coin is not None:
                                    logger.warning(f"⚠️ 账号[{self.nickname}] {self.task_configs[task_name]['name']} 预计[{award_coin}]，实际[{reward}]金币，-> [{self.count}]，结束追加并切换任务")
                                break
                            if award_coin is not None:
                                logger.info(
                                    f"✅ 账号[{self.nickname}] {self.task_configs[task_name]['name']} 预计[{award_coin}]，实际[{reward}]金币，-> [{self.count}]，追加进度: {additional_count}/{max_additional}")
                            else:
                                logger.info(
                                    f"✅ 账号[{self.nickname}] {self.task_configs[task_name]['name']} 获得{reward}金币，-> [{self.count}]，追加进度: {additional_count}/{max_additional}")
                            if additional_count>=max_additional:
                                logger.info(f"📺 账号[{self.nickname}] 追加任务完成，返回主线任务")
                                break
                        task_wait_time=list(map(int,WAIT_TIME.strip('[]').split(',')))
                        min_wait=task_wait_time[0]
                        max_wait=task_wait_time[1]
                        wait_time=random.randint(int(min_wait),int(max_wait))
                        await asyncio.sleep(wait_time/1000)
            if self.stop_all_tasks:
                break
            if task_name !=self.tasks_to_execute[-1]:
                wait_time=random.randint(7000,15000)
                await asyncio.sleep(wait_time/1000)
        return results
async def run_concurrent_tasks(items:List,max_concurrency:int,task_func):
    '并发执行任务'
    results=[None]*len(items)
    index=0
    async def worker():
        nonlocal index
        while True:
            current_index=index
            index+=1
            if current_index>=len(items):
                return
            item=items[current_index]
            try:
                results[current_index]=await task_func(item,current_index)
            except Exception as e:
                logger.error(f"并发执行异常（index={current_index + 1}）：{e}")
                results[current_index]=None
    workers=[worker()for _ in range(min(max_concurrency,len(items)))]
    await asyncio.gather(*workers)
    return results
async def run_single_account(account_config:Dict,max_rounds:int=MAX_ROUNDS)->Dict:
    '运行单个账号任务'
    account_display_name=account_config.get('nickname')if account_config.get('has_remark')else account_config[
        'index']
    if account_config.get('proxy_url'):
        max_retries=5
        proxy_test=None
        for retry_count in range(max_retries):
            proxy_test=await test_proxy_connection(account_config['proxy_url'],f"账号[{account_display_name}]")
            if proxy_test['ok']:
                logger.info(f"✅ 账号[{account_display_name}] 代理验证通过，IP: {proxy_test['ip']}")
                if proxy_test['ip']and proxy_test['ip']!='localhost':
                    pass
                break
            else:
                if retry_count<max_retries-1:
                    logger.warning(
                        f"⚠️ 账号[{account_display_name}]代理验证失败，正在重试 {retry_count + 1}/{max_retries}")
                    await asyncio.sleep(2)# 重试前等待2秒
                else:
                    logger.error(f"❌ 账号[{account_display_name}]代理验证失败，已重试{max_retries}次，停止该账号运行")
                    nickname=account_config.get('nickname')or f"账号{account_config['index']}"
                    return{
                        'index':account_config['index'],
                        'nickname':nickname,
                        'initial_coin':0,
                        'final_coin':0,
                        'coin_change':0,
                        'initial_cash':0,
                        'final_cash':0,
                        'cash_change':0,
                        'stats':{},
                        'proxy_verification_failed':True,
                        'error':'代理验证失败'
}
    else:
        logger.info(f"账号[{account_display_name}] 未配置代理，走直连")
    basic_info=await get_account_basic_info(
        account_config['cookie'],
        account_config.get('proxy_url'),
        account_config['index']
)
    if account_config.get('has_remark',False):
        nickname=account_config.get('nickname')or f"账号{account_config['index']}"
    else:
        nickname=(basic_info.get('nickname')if basic_info else None)or f"账号{account_config['index']}"
    if basic_info:
        total_coin=basic_info['total_coin']if basic_info['total_coin']is not None else '未知'
        all_cash=basic_info['all_cash']if basic_info['all_cash']is not None else '未知'
        logger.info(f"💰 账号[{account_config['index']} => {nickname}] 当前金币: {total_coin}，当前余额: {all_cash}")
    else:
        logger.warning(f"账号[{nickname}] ❌ 基本信息获取失败，继续执行")
    account_config['nickname']=nickname
    tasks_to_execute=parse_task_config()
    worker=KuaishouTaskWorker(account_config,tasks_to_execute)
    await worker.check_coin_limit()
    if worker.coin_exceeded:
        logger.info(f"账号[{worker.nickname}] 初始金币已超过阈值，不执行任务")
        final_info=await get_account_basic_info(
            account_config['cookie'],
            account_config.get('proxy_url'),
            account_config['index']
)
        initial_coin=int(basic_info.get('total_coin',0)or 0)if basic_info else 0
        final_coin=int(final_info.get('total_coin',0)or 0)if final_info else 0
        coin_change=final_coin-initial_coin
        initial_cash=float(basic_info.get('all_cash',0)or 0)if basic_info else 0
        final_cash=float(final_info.get('all_cash',0)or 0)if final_info else 0
        cash_change=final_cash-initial_cash
        return{
            'index':account_config['index'],
            'nickname':nickname,
            'initial_coin':initial_coin,
            'final_coin':final_coin,
            'coin_change':coin_change,
            'initial_cash':initial_cash,
            'final_cash':final_cash,
            'cash_change':cash_change,
            'stats':worker.get_task_stats(),
            'coin_limit_exceeded':True
}
    consecutive_no_success_rounds=0
    for round_num in range(max_rounds):
        wait_time=random.randint(4000,8000)
        logger.info(f"⌛ 账号[{worker.nickname}] 开始第{round_num + 1}/{max_rounds}轮任务")
        await asyncio.sleep(wait_time/1000)
        round_results=await worker.execute_all_tasks_by_priority()
        basic_info1=await get_account_basic_info(
            account_config['cookie'],
            account_config.get('proxy_url'),
            account_config['index']
)
        total_coin1=basic_info1['total_coin']if basic_info1 and basic_info1.get('total_coin')is not None else '未知'
        if any(round_results.values()):
            if basic_info1:
                logger.info(f"✅ 账号[{worker.nickname}] 第{round_num + 1}轮执行完成，当前金币: {total_coin1}")
            else:
                logger.info(f"✅ 账号[{worker.nickname}] 第{round_num + 1}轮执行完成，获取基本信息失败，当前金币未知")
            consecutive_no_success_rounds=0
        else:
            logger.warning(f"⚠️ 账号[{worker.nickname}] 第{round_num + 1}轮没有成功任务")
            consecutive_no_success_rounds+=1
        if worker.stop_all_tasks or consecutive_no_success_rounds>=2:
            logger.info(f"🏁 账号[{worker.nickname}] 达到停止条件，终止后续轮次")
            break
        if total_coin1 !='未知' and int(total_coin1)>COIN_LIMIT:
            logger.info(f"账号[{worker.nickname}] 金币已超过阈值，结束任务")
            break
        if round_num<max_rounds-1:
            rounds_wait_time=list(map(int,ROUNDS_WAIT_TIME.strip('[]').split(',')))
            min_wait=rounds_wait_time[0]
            max_wait=rounds_wait_time[1]
            wait_time=random.randint(int(min_wait),int(max_wait))
            await asyncio.sleep(wait_time/1000)
    final_info=await get_account_basic_info(
        account_config['cookie'],
        account_config.get('proxy_url'),
        account_config['index']
)
    initial_coin=int(basic_info.get('total_coin',0)or 0)if basic_info else 0
    final_coin=int(final_info.get('total_coin',0)or 0)if final_info else 0
    coin_change=final_coin-initial_coin
    initial_cash=float(basic_info.get('all_cash',0)or 0)if basic_info else 0
    final_cash=float(final_info.get('all_cash',0)or 0)if final_info else 0
    cash_change=final_cash-initial_cash
    worker.print_task_stats()
    return{
        'index':account_config['index'],
        'nickname':nickname,
        'initial_coin':initial_coin,
        'final_coin':final_coin,
        'coin_change':coin_change,
        'initial_cash':initial_cash,
        'final_cash':final_cash,
        'cash_change':cash_change,
        'stats':worker.get_task_stats(),
        'coin_limit_exceeded':worker.coin_exceeded
}
def display_summary_table(account_results:List[Dict]):
    '显示汇总表格'
    if not account_results:
        logger.info('没有可显示的账号信息。')
        return
    total_initial_coin=sum(int(result['initial_coin']or 0)for result in account_results)
    total_final_coin=sum(int(result['final_coin']or 0)for result in account_results)
    total_coin_change=total_final_coin-total_initial_coin
    total_initial_cash=sum(float(result['initial_cash']or 0)for result in account_results)
    total_final_cash=sum(float(result['final_cash']or 0)for result in account_results)
    total_cash_change=total_final_cash-total_initial_cash
    total_tasks=0
    total_success=0
    total_reward=0
    for result in account_results:
        if result.get('stats'):
            for task_stats in result['stats'].values():
                total_tasks+=task_stats['success']+task_stats['failed']
                total_success+=task_stats['success']
                total_reward+=task_stats['total_reward']
    success_rate=(total_success/total_tasks*100)if total_tasks>0 else 0.0
    exceeded_count=sum(1 for result in account_results if result.get('coin_limit_exceeded',False))
    print('\n' + '=' * 80)
    print('|'+center_text('         任务执行结果汇总表        ',78)+'|')
    print('='*80)
    line1=f"总账号数: {len(account_results)}".ljust(22)
    line2=f"超过金币阈值账号: {exceeded_count}".ljust(22)
    line3=f"总任务数: {total_tasks}".ljust(22)
    line4=f"任务成功率: {success_rate:.1f}%".ljust(10)
    print('|'+line1+line2+line3+line4+'|')
    line5=f"总金币变化: {total_coin_change}".ljust(26)
    line6=f"总金币奖励: {total_reward}".ljust(26)
    line7=f"总余额变化: {total_cash_change:.2f}".ljust(24)
    print('|'+line5+line6+line7+'|')
    print('-'*80)
    headers=['序号','账号昵称','初始金币','最终金币','金币变化','初始余额','最终余额','余额变化']
    widths=[6,16,12,12,12,12,12,12]
    header_line='|'
    for header,width in zip(headers,widths):
        header_line+=center_text(header,width)+'|'
    print(header_line)
    separator_line='|'
    for width in widths:
        separator_line+='-'*width+'|'
    print(separator_line)
    for result in account_results:
        line='|'
        line+=center_text(result['index'],widths[0])+'|'
        nickname_display=(result.get('nickname','-')+
(' ⚠️' if result.get('coin_limit_exceeded',False)else ''))
        line+=center_text(nickname_display[:widths[1]-2],widths[1])+'|'
        line+=center_text(result['initial_coin'],widths[2])+'|'
        line+=center_text(result['final_coin'],widths[3])+'|'
        coin_change_str=f"+{result['coin_change']}"if result['coin_change']>=0 else str(result['coin_change'])
        line+=center_text(coin_change_str,widths[4])+'|'
        line+=center_text(result['initial_cash'],widths[5])+'|'
        line+=center_text(result['final_cash'],widths[6])+'|'
        cash_change_str=f"+{result['cash_change']:.2f}"if result[
                                                                 'cash_change']>=0 else f"{result['cash_change']:.2f}"
        line+=center_text(cash_change_str,widths[7])+'|'
        print(line)
    print('='*80)
    print('|'+center_text('      任务执行完成，请查看详细结果      ',78)+'|')
    print('='*80)
async def main():
    '主函数'
    max_concurrency=MAX_CONCURRENCY_DEFAULT
    account_configs=load_account_configs()
    logger.info(f"✅ 成功加载 {len(account_configs)} 个有效账号")
    if not account_configs:
        sys.exit(1)
    logger.info(f"🎯 将执行以下任务：{', '.join(parse_task_config())}\\n")
    logger.info(f"环境变量配置")
    logger.info(f"账号CK(k_ksck10)")
    logger.info(f"任务类型(k_task10)")
    logger.info(f"签名服务地址(SIGN_BASE_URL = {SIGN_BASE_URL})")
    logger.info(f"轮数(ROUNDS = {MAX_ROUNDS})")
    logger.info(f"金币总阈值(KS_COIN_LIMIT = {COIN_LIMIT})")
    logger.info(f"开启追加广告及次数(SUCCESS_AD_NUM = {SUCCESS_AD_NUM})")
    logger.info(f"每轮单任务运行次数(TASK_NUM_ROUND = {TASK_NUM_ROUND})")
    logger.info(f"低奖励停止次数(LOW_REWARD_LIMIT = {LOW_REWARD_LIMIT})")
    logger.info(f"低奖励阈值(LOW_REWARD_THRESHOLD = {LOW_REWARD_THRESHOLD})")
    logger.info(f"金币在修改范围内更换 did (CHANGE_DID = {os.getenv('CHANGE_DID', '0')})")
    logger.info(f"修改did的金币范围(CHANGE_DID_RANGE = {CHANGE_DID_RANGE})")
    logger.info(f"更换did次数(CHANGE_DID_TIMES = {CHANGE_DID_TIMES})")
    logger.info(f"危险金币数,出现一次立马停止(DANGER_COIN = {DANGER_COIN})")
    logger.info(f"获取每次广告等待时间(WAIT_TIME = {WAIT_TIME})")
    logger.info(f"看广告等待时间(PLAY_WAIT_TIME = {PLAY_WAIT_TIME})")
    logger.info(f"轮次间等待时间(ROUNDS_WAIT_TIME = {ROUNDS_WAIT_TIME})")
    logger.info(f"连续失败后等待时间(SLEEP_TIME = {SLEEP_TIME}) 单位分钟")
    logger.info(f"模式更改(MODE_CHANGE = {MODE_CHANGE}) 0为叠加模式，1为额外模式\\n")
    print('============🎉MK集团版 KS V2.4 启动！🎉=============')
    time.sleep(1)
    results=[]
    async def process_account(account_config,index):
        logger.info(f"—— 开始账号[{account_config['index']}] ——")
        try:
            result=await run_single_account(account_config,MAX_ROUNDS)
            return{
                'index':account_config['index'],
                'remark':account_config.get('remark','无备注'),
                'nickname':result.get('nickname',account_config.get('nickname',f"账号{account_config['index']}")),
                'initial_coin':result.get('initial_coin',0),
                'final_coin':result.get('final_coin',0),
                'coin_change':result.get('coin_change',0),
                'initial_cash':result.get('initial_cash',0),
                'final_cash':result.get('final_cash',0),
                'cash_change':result.get('cash_change',0),
                'stats':result.get('stats',{}),
                'coin_limit_exceeded':result.get('coin_limit_exceeded',False)
}
        except Exception as e:
            logger.error(f"账号[{account_config['index']}] ❌ 执行异常：{e}")
            return{
                'index':account_config['index'],
                'remark':account_config.get('remark','无备注'),
                'nickname':account_config.get('nickname',f"账号{account_config['index']}"),
                'initial_coin':0,
                'final_coin':0,
                'coin_change':0,
                'initial_cash':0,
                'final_cash':0,
                'cash_change':0,
                'error':str(e)
}
    results=await run_concurrent_tasks(account_configs,max_concurrency,process_account)
    valid_results=[r for r in results if r is not None]
    valid_results.sort(key=lambda x:x['index'])
    logger.info('✅全部完成。 ')
    logger.info(
        '---------------------------------------------- 账号信息汇总 ----------------------------------------------')
    display_summary_table(valid_results)
if __name__=='__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('\n程序被用户中断')
        sys.exit(0)


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