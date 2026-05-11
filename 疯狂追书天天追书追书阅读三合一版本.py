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

import base64
import requests
from pyDes import des, CBC, PAD_PKCS5
import random
import time
import re
import os
import json
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

DEBUG = False
# 疯狂追书，天天追书，追书阅读三合一版本！

# ==================== 账号配置区域 ====================
# 请在这里直接填写你的账号加密字符串（用引号括起来）

# 疯狂追书账号（每行一个，不需要的账号前面加#注释掉）
# 抓包p参数即可！填到下方""中间
FKZS_ACCOUNTS = [
    "p值填这里，不要去掉双引号！",



#多账号空行新增"", 中间填p值
  
]

# 天天追书账号（每行一个，不需要的账号前面加#注释掉）
# 抓包p参数即可！填到下方""中间
TTZS_ACCOUNTS = [
        "p值填这里，不要去掉双引号！",



#多账号空行新增"", 中间填p值
  

  
]

# 追书阅读账号（每行一个，不需要的账号前面加#注释掉）
# 抓包p参数即可！填到下方""中间
ZSYD_ACCOUNTS = [

    "p值填这里，不要去掉双引号！",



#多账号空行新增"", 中间填p值
  

]

# ==================== 账号配置结束 ====================

# ========== 任务开关配置 ==========
# 基础任务开关
ENABLE_SIGN_IN = True                # 每日签到（新增）
ENABLE_DRINK_WATER = True            # 喝水打卡领金币
ENABLE_WATCH_AD = True               # 看广告领金币奖励
ENABLE_EXCHANGE_GOLD = True          # 换金币观看视频
ENABLE_RED_PACKET = True             # 开红包必得微信打款
ENABLE_AD_WATER = True               # 喝水打卡观看视频领金币
ENABLE_SIGN_AD = True                # 签到广告
ENABLE_HOME_GOLD = True              # 主页领金币

# 限次任务开关
ENABLE_READ_GOLD = True              # 阅读赚金币
ENABLE_AUDIO_GOLD = True           # 听书赚金币
MAX_READ_GOLD_COUNT = 380            # 阅读赚金币最大执行次数
MAX_AUDIO_GOLD_COUNT = 380           # 听书赚金币最大执行次数

# 可提现/领取任务开关
ENABLE_NOVEL_WITHDRAW = True         # 看小说可提现
ENABLE_READ_GOLD_CLAIM = True        # 阅读赚金币领取
ENABLE_AUDIO_NOVEL_WITHDRAW = True   # 听小说可提现
ENABLE_AUDIO_GOLD_CLAIM = True       # 听书赚金币领取

# 额外奖励任务开关
ENABLE_AUDIO_BONUS = True            # 听书额外奖励
# =================================

ERROR_PATTERNS = [r'wWMEGtyKZ2YIo90WVXVhlHzkBqOr3d\+thy4E6JxMoklFS6aG4Y0B8ULEP7iuUXCc']

# API URLs
URL_SIGN_DATA = "http://fiction.52leho.com/v1/task/sign/data"  # 签到数据接口
URL_SIGN_REWARD = "http://fiction.52leho.com/v1/task/reward"   # 签到奖励接口
URL_DRINK = "http://fiction.52leho.com/v1/task/reward/drink"
URL_AD = "http://fiction.52leho.com/v1/task/ad/reward"
URL_READ = "http://fiction.52leho.com/v1/book/read"
URL_AUDIO_BOOK = "http://fiction.52leho.com/v1/book/audio"
URL_AUDIO_TASK = "http://fiction.52leho.com/v1/audio/book/task"
URL_TASK_REWARD = "http://fiction.52leho.com/v1/task/reward"

# 应用配置映射
APP_CONFIGS = {
    "FKZS": {
        "key": "4d60FY1O",
        "app_pkg": "com.dt.fkzs",
        "name": "疯狂追书",
        "env_var": "FKZS"
    },
    "TTZS": {
        "key": "UXjLDsEg",
        "app_pkg": "com.dt.ttzs",
        "name": "天天追书",
        "env_var": "TTZS"
    },
    "ZSYD": {
        "key": "BSSMxvCw",
        "app_pkg": "com.dt.zsyd",
        "name": "追书阅读",
        "env_var": "ZSYD"
    }
}

# 全局锁用于打印
print_lock = threading.Lock()

def extract_iv_from_prefix(encrypted_data):
    """从加密数据前缀提取IV - 支持多种格式"""
    try:
        # URL解码处理
        decoded = encrypted_data.replace('%3D', '=').replace('%3d', '=')

        # 格式1: xxxxxxxx=... (标准格式，IV是=前的8位)
        if '=' in decoded:
            prefix = decoded.split('=')[0]
            if len(prefix) >= 8:
                return prefix[:8]  # 取前8位作为IV

        # 格式2: 纯base64无等号，取前8位
        if len(decoded) >= 8:
            return decoded[:8]

    except Exception as e:
        if DEBUG:
            print(f"IV提取失败: {e}")
    return None

def des_decrypt(data, key, iv):
    """DES解密函数"""
    try:
        # 确保数据长度是8的倍数
        if len(data) % 8 != 0:
            # 填充到8的倍数
            padding = 8 - (len(data) % 8)
            data += b'\x00' * padding
        
        des_obj = des(key.encode(), CBC, iv.encode(), padmode=PAD_PKCS5)
        result = des_obj.decrypt(data).decode('utf-8', errors='ignore')
        return result
    except Exception as e:
        return None

def des_encrypt(data, key, iv):
    des_obj = des(key.encode(), CBC, iv.encode(), padmode=PAD_PKCS5)
    return des_obj.encrypt(data.encode())

def encrypt_and_format(text, key, iv):
    encrypted = des_encrypt(text, key, iv)
    b64 = base64.b64encode(encrypted).decode().replace('+', '-').replace('/', '_').replace('=', '%3D')
    final = f"m-sYQQBYfQmI%3D{b64}"
    return final

def send_request(final_p, url, task_name, app_config):
    payload = f"app_pkg={app_config['app_pkg']}&p={final_p}"
    headers = {
        "device-platform": "android",
        "User-Agent": "android",
        "app_pkg": app_config['app_pkg'],
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        resp = requests.post(url, data=payload, headers=headers, timeout=10)
        resp_bytes = len(resp.text.encode('utf-8'))
        
        if resp_bytes < 150:
            return "no_reward", resp.text, resp_bytes
        elif re.search(ERROR_PATTERNS[0], resp.text):
            return "skip", resp.text, resp_bytes
        elif resp.status_code == 200:
            return "success", resp.text, resp_bytes
        else:
            return "fail", resp.text, resp_bytes
    except Exception as e:
        return "fail", "", 0

def decrypt_account(data, iv, key):
    """解密账号数据 - 支持URL编码格式"""
    try:
        # URL解码
        decoded = data.replace('%3D', '=').replace('%3d', '=')

        if 'm-sYQQBYfQmI=' in decoded:
            b64_part = decoded.split('=', 1)[1]
        elif '=' in decoded:
            prefix, b64_part = decoded.split('=', 1)
        else:
            b64_part = decoded
        
        b64_data = b64_part.replace('-', '+').replace('_', '/')
        
        missing = len(b64_data) % 4
        if missing:
            b64_data += '=' * (4 - missing)
        
        encrypted = base64.b64decode(b64_data)
        plain = des_decrypt(encrypted, key, iv)
        
        if not plain:
            return None
        
        # 清理解密后字符串开头的奇怪字符
        if '&' in plain:
            plain = plain.split('&', 1)[1] if plain.startswith('&') else plain
        
        params = {}
        for p in plain.split('&'):
            if '=' in p:
                k, v = p.split('=', 1)
                params[k] = v
        
        return params
    except Exception as e:
        return None

def process_sign_in(params, app_config, iv):
    """处理签到任务：先获取签到数据，再领取签到奖励"""
    try:
        # 第一步：调用 sign/data 接口获取签到数据
        plain_text = '&'.join([f"{k}={v}" for k, v in params.items()])
        final_p = encrypt_and_format(plain_text, app_config['key'], iv)
        
        result, resp_text, resp_bytes = send_request(final_p, URL_SIGN_DATA, "签到获取数据", app_config)
        
        if result == "success":
            with print_lock:
                print(f"  ✅ 签到数据获取成功 (字节:{resp_bytes})")
            
            # 等待1-3秒
            time.sleep(random.randint(1, 3))
            
            # 第二步：调用 reward 接口领取签到奖励，添加 action=sign_reward
            params['action'] = 'sign_reward'
            plain_text = '&'.join([f"{k}={v}" for k, v in params.items()])
            final_p = encrypt_and_format(plain_text, app_config['key'], iv)
            
            result2, resp_text2, resp_bytes2 = send_request(final_p, URL_SIGN_REWARD, "签到领取奖励", app_config)
            
            if result2 == "success":
                with print_lock:
                    print(f"  ✅ 签到奖励领取成功 (字节:{resp_bytes2})")
                return True, "签到成功"
            else:
                with print_lock:
                    print(f"  ⚠️ 签到奖励领取失败: {result2}")
                return False, f"领取失败: {result2}"
        else:
            with print_lock:
                print(f"  ⚠️ 签到数据获取失败: {result}")
            return False, f"获取数据失败: {result}"
            
    except Exception as e:
        with print_lock:
            print(f"  ❌ 签到过程出错: {e}")
        return False, str(e)

def build_task_list():
    tasks = []
    
    # 签到任务放在最前面
    if ENABLE_SIGN_IN:
        tasks.append(("每日签到", "sign_reward", URL_SIGN_REWARD, None, False, True))  # 新增签到标记
    
    if ENABLE_DRINK_WATER:
        tasks.append(("喝水打卡领金币", "water_video_reward", URL_DRINK, None, False, False))
    if ENABLE_WATCH_AD:
        tasks.append(("看广告领金币奖励", "view_ad_video_reward", URL_AD, None, False, False))
    if ENABLE_EXCHANGE_GOLD:
        tasks.append(("换金币观看视频", "score_exchange_money_reward", URL_AD, None, False, False))
    if ENABLE_RED_PACKET:
        tasks.append(("开红包必得微信打款", "new_watch_ad", URL_AD, None, False, False))
    if ENABLE_AD_WATER:
        tasks.append(("喝水打卡观看视频领金币", "ad_water_video_reward", URL_AD, None, False, False))
    if ENABLE_SIGN_AD:
        tasks.append(("签到广告", "next_video_ad_reward", URL_AD, None, False, False))
    if ENABLE_HOME_GOLD:
        tasks.append(("主页领金币", "surprise_pop_reward_1", URL_AD, None, False, False))
    
    if ENABLE_READ_GOLD:
        tasks.append(("阅读赚金币", "read_ad_reward", URL_READ, MAX_READ_GOLD_COUNT, False, False))
    if ENABLE_AUDIO_GOLD:
        tasks.append(("听书赚金币", "", URL_AUDIO_BOOK, MAX_AUDIO_GOLD_COUNT, False, False))
    
    if ENABLE_NOVEL_WITHDRAW:
        tasks.append(("看小说可提现", "read_chapter_reward", URL_TASK_REWARD, None, True, False))
    if ENABLE_READ_GOLD_CLAIM:
        tasks.append(("阅读赚金币领取", "read_reward", URL_TASK_REWARD, None, False, False))
    if ENABLE_AUDIO_NOVEL_WITHDRAW:
        tasks.append(("听小说可提现", "audio_chapter_reward", URL_TASK_REWARD, None, True, False))
    if ENABLE_AUDIO_GOLD_CLAIM:
        tasks.append(("听书赚金币领取", "audio_reward", URL_TASK_REWARD, None, False, False))
    
    if ENABLE_AUDIO_BONUS:
        tasks.append(("听书额外奖励", "bonus_video_ad_award", URL_AD, None, True, False))
    
    return tasks

def get_media_extra(task_name):
    if task_name == "看小说可提现":
        return {
            "media_app_id": "sspGgBvDDjOL1bGA",
            "media_replace_score": 0,
            "media_scene_id": "",
            "media_slot_id": "973305152",
            "media_verify": "8vH6Xy1M7OkXLZEDpGUUDq8+htbL5jrJiNNx5FYV7OB1djll/Mnf7TqCg/I7L1q4RoY7U+jxQnyaWTqkKf5+W5zdu9vJa2SgcVVUynfDsrgRmBO25n9yYlOgiAFUy5ytHm+MyNI9lNqVAgMFtRKVnQ==\u003d\u003d",
            "params_action_type": "DEEPLINK",
            "params_app_name": "美团",
            "params_app_package": "com.sankuai.meituan",
            "params_slot_type": "RewardVideo",
            "position_id": "671",
            "slot_platform": "CSJ",
            "slot_price": "600.0",
            "slot_type": "RewardVideo",
            "tactics_mold": "bidding"
        }
    elif task_name == "听小说可提现":
        return {
            "media_app_id": "sspGgBvDDjOL1bGA",
            "media_replace_score": 0,
            "media_scene_id": "",
            "media_slot_id": "973305153",
            "media_verify": "8vH6Xy1M7OkXLZEDpGUUDq8+htbL5jrJiNNx5FYV7OB1djll/Mnf7TqCg/I7L1q4RoY7U+jxQnyaWTqkKf5+W5zdu9vJa2SgcVVUynfDsriNWwIAM3auBSFEAt1g5nfxLSDbIOyJbXZ/8epqdSQO5A==\u003d\u003d",
            "params_action_type": "DEEPLINK",
            "params_app_name": "今日头条",
            "params_app_package": "com.ss.android.article.news",
            "params_slot_type": "RewardVideo",
            "position_id": "671",
            "slot_platform": "CSJ",
            "slot_price": "300.0",
            "slot_type": "RewardVideo",
            "tactics_mold": "bidding"
        }
    elif task_name == "听书额外奖励":
        return {
            "media_app_id": "sspGgBvDDjOL1bGA",
            "media_replace_score": 0,
            "media_scene_id": "",
            "media_slot_id": "973305155",
            "media_verify": "8vH6Xy1M7OkXLZEDpGUUDq8+htbL5jrJiNNx5FYV7OB1djll/Mnf7TqCg/I7L1q4RoY7U+jxQnyaWTqkKf5+W5zdu9vJa2SgcVVUynfDsri5BSWXN3abIH1PyzIzoGw/O/q2Vcua+zz04UbJGt8PDA==\u003d\u003d",
            "params_action_type": "DEEPLINK",
            "params_app_name": "今日头条",
            "params_app_package": "com.ss.android.article.news",
            "params_slot_type": "RewardVideo",
            "position_id": "671",
            "slot_platform": "CSJ",
            "slot_price": "400.0",
            "slot_type": "RewardVideo",
            "tactics_mold": "bidding"
        }
    return None

def process_task(acc, app_config, task_info, iv, print_lock):
    """处理单个任务"""
    task_name, action, url, max_count, need_media_extra, is_sign_task = task_info
    app_name = app_config['name']
    
    with print_lock:
        print(f"▶️ {app_name} 开始任务: {task_name}")
    
    # 解密账号参数
    params = decrypt_account(acc, iv, app_config['key'])
    if not params:
        with print_lock:
            print(f"❌ {app_name} 解密失败，任务 {task_name} 跳过")
        return {
            "task_name": task_name,
            "success": 0,
            "fail": 1
        }
    
    # 如果是签到任务，使用特殊的签到处理函数
    if is_sign_task:
        success, msg = process_sign_in(params.copy(), app_config, iv)
        if success:
            with print_lock:
                print(f"📊 {app_name} 任务完成: {task_name} (成功:1 失败:0)")
            return {
                "task_name": task_name,
                "success": 1,
                "fail": 0
            }
        else:
            with print_lock:
                print(f"📊 {app_name} 任务完成: {task_name} (成功:0 失败:1)")
            return {
                "task_name": task_name,
                "success": 0,
                "fail": 1
            }
    
    # 普通任务的循环处理
    task_success = 0
    task_fail = 0
    consecutive_fail = 0
    media_extra_added = False
    
    while True:
        if max_count is not None and task_success >= max_count:
            with print_lock:
                print(f"  🎯 {app_name} 已达到最大执行次数 {max_count} 次，任务结束")
            break
        
        if action:
            params['action'] = action
        
        if need_media_extra and not media_extra_added:
            media_extra = get_media_extra(task_name)
            if media_extra:
                params['media_extra'] = json.dumps(media_extra, separators=(',', ':'))
                media_extra_added = True
        
        plain_text = '&'.join([f"{k}={v}" for k, v in params.items()])
        final_p = encrypt_and_format(plain_text, app_config['key'], iv)
        
        result, resp_text, resp_bytes = send_request(final_p, url, task_name, app_config)
        
        if result == "success":
            task_success += 1
            consecutive_fail = 0
            with print_lock:
                if max_count:
                    print(f"  ✅ {app_name} 第{task_success}/{max_count}次成功 (字节:{resp_bytes})")
                else:
                    print(f"  ✅ {app_name} 第{task_success}次成功 (字节:{resp_bytes})")
            
            # 阅读/听书 15~20秒，其他 20~35秒，静默等待
            if task_name in ["阅读赚金币", "听书赚金币"]:
                wait = random.randint(15, 20)
            else:
                wait = random.randint(20, 35)
            time.sleep(wait)
            
        elif result == "no_reward":
            task_fail += 1
            consecutive_fail += 1
            with print_lock:
                print(f"  ⚠️ {app_name} 无奖励 (字节:{resp_bytes}) 失败次数:{consecutive_fail}")
            if consecutive_fail >= 3:
                with print_lock:
                    print(f"  ❌ {app_name} 连续3次无奖励，结束任务")
                break
            wait = random.randint(3, 5)
            time.sleep(wait)
            
        elif result == "skip":
            with print_lock:
                print(f"  ⚠️ {app_name} 检测到跳过模式，结束任务")
            break
            
        else:
            task_fail += 1
            consecutive_fail += 1
            with print_lock:
                print(f"  ❌ {app_name} 请求失败 (字节:{resp_bytes}) 失败次数:{consecutive_fail}")
            if consecutive_fail >= 3:
                with print_lock:
                    print(f"  ❌ {app_name} 连续3次失败，结束任务")
                break
            wait = random.randint(3, 5)
            time.sleep(wait)
    
    with print_lock:
        print(f"📊 {app_name} 任务完成: {task_name} (成功:{task_success} 失败:{task_fail})")
    
    return {
        "task_name": task_name,
        "success": task_success,
        "fail": task_fail
    }

def process_account(acc, app_config, account_index, total_accounts):
    """处理单个账号"""
    results = {
        "app_name": app_config['name'],
        "uid": None,
        "total_success": 0,
        "total_fail": 0,
        "task_results": []
    }
    
    app_name = app_config['name']
    
    with print_lock:
        print(f"\n{'='*50}")
        print(f"[{account_index}/{total_accounts}] {app_name} 账号处理中")
        print(f"{'='*50}")
    
    iv = extract_iv_from_prefix(acc)
    if not iv:
        with print_lock:
            print(f"❌ {app_name} 无法提取IV，跳过")
        return results
    
    # 解密账号获取UID
    params = decrypt_account(acc, iv, app_config['key'])
    if not params:
        with print_lock:
            print(f"❌ {app_name} 解密失败，跳过")
        return results
    
    results['uid'] = params.get('uid', 'N/A')
    
    with print_lock:
        print(f"✅ 解密成功 - UID: {results['uid']}")
        print(f"   设备: {params.get('device_brand', 'N/A')} {params.get('device_model', 'N/A')}")
        print(f"{'━'*31}")
    
    tasks = build_task_list()
    
    # 并行执行所有任务
    task_results = []
    with ThreadPoolExecutor(max_workers=len(tasks)) as task_executor:
        futures = []
        for task_info in tasks:
            future = task_executor.submit(process_task, acc, app_config, task_info, iv, print_lock)
            futures.append(future)
        
        for future in as_completed(futures):
            try:
                task_result = future.result()
                task_results.append(task_result)
            except Exception as e:
                with print_lock:
                    print(f"❌ 任务执行出错: {e}")
    
    # 汇总结果
    for task_result in task_results:
        results['total_success'] += task_result['success']
        results['total_fail'] += task_result['fail']
        results['task_results'].append(task_result)
    
    return results

def main():
    print(f"{'='*50}")
    print("三合一自动任务脚本 - 疯狂追书 & 天天追书 & 追书阅读 (任务同步)")
    print(f"启动: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    print(f"\n📋 任务配置:")
    print(f"   ✅ 每日签到: {'✅' if ENABLE_SIGN_IN else '❌'} (新增)")
    print(f"   💧 喝水打卡领金币: {'✅' if ENABLE_DRINK_WATER else '❌'}")
    print(f"   📺 看广告领金币奖励: {'✅' if ENABLE_WATCH_AD else '❌'}")
    print(f"   💰 换金币观看视频: {'✅' if ENABLE_EXCHANGE_GOLD else '❌'}")
    print(f"   🧧 开红包必得微信打款: {'✅' if ENABLE_RED_PACKET else '❌'}")
    print(f"   💧📺 喝水打卡观看视频: {'✅' if ENABLE_AD_WATER else '❌'}")
    print(f"   📝 签到广告: {'✅' if ENABLE_SIGN_AD else '❌'}")
    print(f"   🏠 主页领金币: {'✅' if ENABLE_HOME_GOLD else '❌'}")
    print(f"   📖 阅读赚金币: {'✅' if ENABLE_READ_GOLD else '❌'} (上限: {MAX_READ_GOLD_COUNT}次)")
    print(f"   🎧 听书赚金币: {'✅' if ENABLE_AUDIO_GOLD else '❌'} (上限: {MAX_AUDIO_GOLD_COUNT}次)")
    print(f"   📚 看小说可提现: {'✅' if ENABLE_NOVEL_WITHDRAW else '❌'}")
    print(f"   💰 阅读赚金币领取: {'✅' if ENABLE_READ_GOLD_CLAIM else '❌'}")
    print(f"   🎧📚 听小说可提现: {'✅' if ENABLE_AUDIO_NOVEL_WITHDRAW else '❌'}")
    print(f"   🎧💰 听书赚金币领取: {'✅' if ENABLE_AUDIO_GOLD_CLAIM else '❌'}")
    print(f"   🎁 听书额外奖励: {'✅' if ENABLE_AUDIO_BONUS else '❌'}")
    print(f"{'='*50}")
    
    # 收集所有账号（从代码顶部变量加载）
    all_accounts = []
    
    # 从代码变量加载账号
    account_map = {
        'FKZS': (FKZS_ACCOUNTS, APP_CONFIGS['FKZS']),
        'TTZS': (TTZS_ACCOUNTS, APP_CONFIGS['TTZS']),
        'ZSYD': (ZSYD_ACCOUNTS, APP_CONFIGS['ZSYD']),
    }
    
    for app_key, (acc_list, app_config) in account_map.items():
        valid_accounts = []
        for acc in acc_list:
            # 跳过注释掉的行和空行
            if isinstance(acc, str) and acc.strip() and not acc.strip().startswith('#'):
                # 移除可能的注释部分
                acc_clean = acc.split('#')[0].strip().strip('"').strip("'")
                if acc_clean:
                    valid_accounts.append(acc_clean)
                    all_accounts.append((acc_clean, app_config))
        
        if valid_accounts:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 加载 {len(valid_accounts)} 个{app_config['name']}账号")
    
    if not all_accounts:
        print("❌ 未找到任何账号配置")
        print("\n请编辑脚本顶部的账号配置区域：")
        print("  1. 找到 FKZS_ACCOUNTS / TTZS_ACCOUNTS / ZSYD_ACCOUNTS")
        print("  2. 在方括号内填入你的账号加密字符串")
        print("  3. 示例：")
        print('     TTZS_ACCOUNTS = [')
        print('         "9HB0xH0mC6pw%3D...你的加密字符串...",')
        print('     ]')
        return
    
    total_accounts = len(all_accounts)
    tasks = build_task_list()
    
    print(f"📊 共找到 {total_accounts} 个账号，共 {len(tasks)} 个任务，开始并行执行...")
    print(f"{'='*50}")
    
    # 并行执行所有账号
    results = []
    with ThreadPoolExecutor(max_workers=total_accounts) as executor:
        futures = []
        for idx, (acc, app_config) in enumerate(all_accounts, 1):
            future = executor.submit(process_account, acc, app_config, idx, total_accounts)
            futures.append(future)
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"❌ 执行出错: {e}")
    
    # 输出最终统计
    print(f"\n{'='*50}")
    print("📊 最终统计结果")
    print(f"{'='*50}")
    
    total_success_all = 0
    total_fail_all = 0
    
    for result in results:
        print(f"\n📱 {result['app_name']} (UID: {result['uid']})")
        print(f"   ✅ 总成功: {result['total_success']} 次")
        print(f"   ❌ 总失败: {result['total_fail']} 次")
        print(f"   💰 预估收益: {result['total_success'] * 0.5:.2f} 元")
        
        # 详细任务统计
        print(f"   📋 任务详情:")
        for task_result in result['task_results']:
            if task_result['success'] > 0 or task_result['fail'] > 0:
                print(f"      - {task_result['task_name']}: 成功 {task_result['success']} 次, 失败 {task_result['fail']} 次")
        
        total_success_all += result['total_success']
        total_fail_all += result['total_fail']
    
    print(f"\n{'='*50}")
    print(f"🎉 所有任务执行完成!")
    print(f"📈 总统计: 成功 {total_success_all} 次 | 失败 {total_fail_all} 次")
    print(f"💰 总预估收益: {total_success_all * 0.5:.2f} 元")
    print(f"结束: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

if __name__ == "__main__":
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