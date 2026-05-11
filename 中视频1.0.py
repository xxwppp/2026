# 业务规则说明：
# - 一个广告0.2元，不需要养机
# - 每天看20个广告上限=4元
# - 积分比例100：1元（100积分=1元）
# - 积分每天晚上12点自动到余额
# - 10元起提，一机一号一ip
# - 先注册并完成本人认证：https://zsp.99panel.top/#/register?inviteCode=1ymGPhqw
# 变量名称pg  单账号： secretId&secretKey&代理 （代理可选） 多账号：每行一个账号，换行分隔
# 1. secretId ：账号唯一标识（必选） 2.  secretKey ：账号密钥（必选） 3.  代理 ：支持普通格式、带账号密码格式、竖线分隔格式（可选，省略则本地直连）
# 新增变量pgxc：自定义线程数，默认1，最大100

import requests
import json
import sys
import os
import time
import random
import re
import urllib3
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode = True

# 全局配置常量
ENV_VAR_NAME = "pg"
LOOP_COUNT = int(os.environ.get("RUN_LOOP_COUNT", 60))
PROXY_TIMEOUT = 10
REQ_TIMEOUT = 30
LOGIN_RETRY = 3
POINT_TO_CASH_RATIO = 100
DEFAULT_THREAD_NUM = 1
MAX_THREAD_NUM = 100

# 线程数配置
try:
    CUSTOM_THREAD_NUM = int(os.environ.get("pgxc", DEFAULT_THREAD_NUM))
    CUSTOM_THREAD_NUM = max(DEFAULT_THREAD_NUM, min(CUSTOM_THREAD_NUM, MAX_THREAD_NUM))
except (ValueError, TypeError):
    CUSTOM_THREAD_NUM = DEFAULT_THREAD_NUM

# 接口URL
LOGIN_URL = "https://x1.zsptv.online/api/app/v1/auth/secretKeyLogin"
AD_URL = "https://x1.zsptv.online/api/app/v1/ad/next"
AD_PLAY_URL = "https://x1.zsptv.online/api/app/v1/ad/video/play"
AD_ENDED_URL = "https://x1.zsptv.online/api/app/v1/ad/video/ended"

# 全局状态与锁
account_limit_status = {}
limit_lock = threading.Lock()

# 设备池（仅作哈希分配用，不再运行中随机）
DEVICE_MODELS = {
    "huawei": ["TAS-AN00", "NOH-AN00"],
    "xiaomi": ["Redmi Note 12", "Xiaomi 13"],
    "oppo": ["Reno8", "Find X5"],
    "vivo": ["V2426A", "X90"]
}
ANDROID_VERSIONS = ["13", "14", "15", "16"]
CHROME_VERSIONS = ["132.0.0.0", "134.0.6998.135"]

# 全局缓存：secretId -> 固定指纹，只算一次
acc_finger_cache = {}

def get_bind_finger(secretId):
    """根据secretId生成永久固定全套指纹：DeviceID+设备信息+UA"""
    if secretId in acc_finger_cache:
        return acc_finger_cache[secretId]
    
    hx = hashlib.md5(secretId.encode("utf-8")).hexdigest()
    hi = int(hx, 16)
    
    # 固定设备ID
    fixed_device_id = hx
    
    # 固定设备信息
    brands = list(DEVICE_MODELS.keys())
    brand = brands[hi % len(brands)]
    model = DEVICE_MODELS[brand][hi % len(DEVICE_MODELS[brand])]
    android_ver = ANDROID_VERSIONS[hi % len(ANDROID_VERSIONS)]
    chrome_ver = CHROME_VERSIONS[hi % len(CHROME_VERSIONS)]
    
    # 绑定你指定格式的标准UA
    ua = (
        f"Mozilla/5.0 (Linux; Android {android_ver}; {model} Build/BP2A.250605.031.A3_V000L1; wv) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{chrome_ver} "
        f"Mobile Safari/537.36 (Immersed/42.0) Html5Plus/1.0"
    )
    
    info = {
        "device_id": fixed_device_id,
        "brand": brand,
        "model": model,
        "android_version": android_ver,
        "chrome_version": chrome_ver,
        "ua": ua
    }
    acc_finger_cache[secretId] = info
    return info

def proxy_check(proxy):
    test_urls = ["http://httpbin.org/ip", "http://ip-api.com/json"]
    if not proxy:
        for test_url in test_urls:
            try:
                resp = requests.get(test_url, timeout=PROXY_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"}, verify=False)
                if resp.status_code == 200:
                    local_ip = resp.json().get("query", "未知")
                    return {"valid": True, "proxy": None, "msg": f"✅ 无代理 IP:{local_ip}"}
            except:
                continue
        return {"valid": False, "proxy": None, "msg": "❌ 本地网络异常"}

    proxy_url = proxy.strip()
    if "|" in proxy_url and "://" not in proxy_url:
        parts = proxy_url.split("|")
        if len(parts)>=2:
            ip,port = parts[0],parts[1]
            user = parts[2] if len(parts)>=3 else ""
            pwd = parts[3] if len(parts)>=4 else ""
            if user and pwd:
                proxy_url = f"socks5://{user}:{pwd}@{ip}:{port}"
            else:
                proxy_url = f"socks5://{ip}:{port}"
    elif re.match(r'\d+\.\d+\.\d+\.\d+:\d+',proxy_url):
        proxy_url = f"socks5://{proxy_url}"

    pp = {"http":proxy_url,"https":proxy_url}
    for _ in range(2):
        for u in test_urls:
            try:
                r = requests.get(u, proxies=pp, timeout=PROXY_TIMEOUT, headers={"User-Agent":"Mozilla/5.0"}, verify=False)
                if r.status_code==200:
                    ip = r.json().get("query","未知")
                    return {"valid":True,"proxy":proxy_url,"msg":f"✅ 代理有效 IP:{ip}"}
            except:
                pass
        time.sleep(1)
    return {"valid":False,"proxy":None,"msg":"❌ 代理无效"}

def load_accounts_from_pg():
    accounts = []
    pg_env = os.environ.get(ENV_VAR_NAME,"").strip()
    if not pg_env:
        return accounts
    lines = [l.strip() for l in pg_env.splitlines() if l.strip()]
    for idx,line in enumerate(lines,1):
        parts = line.split("&")
        if len(parts)<2:
            print(f"⚠️ 跳过第{idx}行：格式错误")
            continue
        sid = parts[0].strip()
        sk = parts[1].strip()
        px = parts[2].strip() if len(parts)>=3 else ""
        accounts.append({"seq":idx,"secretId":sid,"secretKey":sk,"proxy":px})
        with limit_lock:
            account_limit_status[idx] = False
    return accounts

def all_accounts_limited():
    with limit_lock:
        return all(account_limit_status.values())

def get_final_concurrent_num(cnt):
    return min(CUSTOM_THREAD_NUM, cnt, MAX_THREAD_NUM)

def account_run(account):
    seq = account["seq"]
    sid = account["secretId"]
    sk = account["secretKey"]
    proxy = account["proxy"]

    total_point = 0.0
    succ_cnt = 0
    token = ""
    is_limit = False

    # 核心：绑定ID，全套设备指纹永久固定
    finger = get_bind_finger(sid)
    device_id = finger["device_id"]
    user_agent = finger["ua"]
    brand = finger["brand"]
    model = finger["model"]
    android_v = finger["android_version"]

    # 代理校验
    px_res = proxy_check(proxy)
    proxies = {"http":px_res["proxy"],"https":px_res["proxy"]} if px_res["valid"] and px_res["proxy"] else None

    print(f"\n=== 账号{seq} 启动 ===")
    print(f"账号{seq} | {px_res['msg']}")
    print(f"账号{seq} | 固化设备：{brand} {model} Android{android_v}")
    print(f"账号{seq} | 固化DeviceID：{device_id}")

    # 固定请求头
    base_headers = {
        "app-device": json.dumps({
            "id": device_id,
            "brand": brand,
            "model": model,
            "platform": "android",
            "system": f"Android {android_v}",
            "version": "1.0.0"
        }, ensure_ascii=False),
        "app-version":"1.0.0",
        "user-agent": user_agent,
        "Host":"x1.zsptv.online",
        "Connection":"Keep-Alive",
        "Accept-Encoding":"gzip"
    }

    sess = requests.Session()
    sess.headers.update(base_headers)
    sess.timeout = REQ_TIMEOUT
    sess.verify = False
    if proxies:
        sess.proxies.update(proxies)

    # 安全登录
    login_ok = False
    login_payload = {"secretId":sid,"secretKey":sk}
    for rt in range(LOGIN_RETRY+1):
        print(f"\n账号{seq} 登录尝试 {rt+1}/{LOGIN_RETRY+1}")
        try:
            resp = sess.post(LOGIN_URL, json=login_payload, headers={"Content-Type":"application/json"})
            print(f"响应码：{resp.status_code}")
            if resp.status_code!=200:
                time.sleep(3)
                continue
            try:
                res_json = resp.json()
            except:
                print("响应非JSON，跳过")
                time.sleep(3)
                continue
            token = res_json.get("token") or res_json.get("data",{}).get("token") or ""
            if token:
                print(f"登录成功 Token:{token[:20]}...")
                login_ok = True
                break
            else:
                print("未获取到Token")
        except Exception as e:
            print(f"登录异常：{str(e)[:35]}")
        if rt == LOGIN_RETRY-1 and proxies:
            print("清空代理重试本地网络")
            sess.proxies.clear()
            proxies = None
        time.sleep(3)

    if not login_ok:
        print(f"账号{seq} 登录失败，终止")
        with limit_lock:
            account_limit_status[seq]=True
        sess.close()
        return

    ad_hd = {"Authorization":f"Bearer {token}"}
    for loop in range(1, LOOP_COUNT+1):
        if is_limit or all_accounts_limited():
            break
        print(f"\n—— 账号{seq} 第{loop}轮 ——")
        try:
            ad_resp = sess.get(AD_URL, headers=ad_hd)
            ad_resp.raise_for_status()
            ad_json = ad_resp.json()
            code = ad_json.get("code",-1)
            data = ad_json.get("data",{})
            status = data.get("status",-1)

            if status == 4000503:
                print(f"账号{seq} 今日广告已超限")
                is_limit = True
                with limit_lock:
                    account_limit_status[seq]=True
                break
            if code!=0 or "result" not in data:
                print(f"无有效广告：{data.get('message','')}")
                time.sleep(5)
                continue

            ad_info = data["result"]
            ad_id = ad_info.get("id")
            reward_str = ad_info.get("reward","0")
            if not ad_id:
                time.sleep(5)
                continue

            # 解析积分
            add_point = 0.0
            try:
                if isinstance(reward_str,(int,float)):
                    add_point = float(reward_str)
                else:
                    m = re.search(r"\d+\.?\d*",reward_str)
                    if m:
                        add_point = float(m.group())
            except:
                pass

            # 播放上报
            play_hd = {"Authorization":f"Bearer {token}","Content-Type":"application/json"}
            play_pl = {
                "id":ad_id,"clientIp":"0.0.0.0",
                "playTime":datetime.utcnow().isoformat()+"Z",
                "deviceInfo":{"deviceId":device_id,"platform":"android"}
            }
            play_r = sess.post(AD_PLAY_URL,json=play_pl,headers=play_hd)
            play_r.raise_for_status()
            play_data = play_r.json().get("data",{})
            play_id = play_data.get("id","")
            if not play_id:
                print("无播放ID，跳过")
                time.sleep(5)
                continue

            # 模拟播放时长
            time.sleep(random.randint(30,50))

            # 结束上报
            end_pl = {
                "id":play_id,"clientIp":"0.0.0.0",
                "endTime":datetime.utcnow().isoformat()+"Z",
                "deviceInfo":{"deviceId":device_id,"platform":"android"}
            }
            end_r = sess.post(AD_ENDED_URL,json=end_pl,headers=play_hd)
            end_r.raise_for_status()
            end_json = end_r.json()

            if end_json.get("message")=="success":
                succ_cnt += 1
                total_point += add_point
                cash = total_point / POINT_TO_CASH_RATIO
                print(f"本轮成功 | 累计积分:{total_point:.2f} 折合:{cash:.2f}元")
            else:
                print("本轮上报失败")

        except Exception as e:
            print(f"轮次异常：{str(e)[:40]}")
            time.sleep(10)

        if loop < LOOP_COUNT and not is_limit:
            time.sleep(20)

    sess.close()
    print(f"\n账号{seq} 任务结束 | 成功{succ_cnt}个广告 | 总积分{total_point:.2f}")

if __name__ == "__main__":
    acc_list = load_accounts_from_pg()
    if not acc_list:
        print("请配置环境变量 pg = secretId&secretKey&代理，多账号换行")
        sys.exit()
    acc_num = len(acc_list)
    work_num = get_final_concurrent_num(acc_num)
    print(f"启动 | 账号数:{acc_num} 并发线程:{work_num} 循环轮数:{LOOP_COUNT}")
    exe = ThreadPoolExecutor(max_workers=work_num)
    tasks = []
    for a in acc_list:
        tasks.append(exe.submit(account_run,a))
        time.sleep(0.5)
    while True:
        if all_accounts_limited() or all(t.done() for t in tasks):
            exe.shutdown(wait=False)
            break
        time.sleep(20)
    print("全部任务执行完毕")
