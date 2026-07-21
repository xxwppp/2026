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

# # 当前脚本来自于 http://script.nnioj.com/ 脚本库下载！
# # 当前脚本来自于 http://script.nnioj.com/ 脚本库下载！
# # 当前脚本来自于 http://script.nnioj.com/ 脚本库下载！
# # 脚本库中的所有脚本文件均来自热心网友上传和互联网收集。
# # 脚本库仅提供文件上传和下载服务，不提供脚本文件的审核。
# # 您在使用脚本库下载的脚本时自行检查判断风险。
# # 所涉及到的 账号安全、数据泄露、设备故障、软件违规封禁、财产损失等问题及法律风险，与脚本库无关！均由开发者、上传者、使用者自行承担。

"""
星汇甄选
环境变量 XHZX_ACCOUNTS："账号#密码...
环境变量 XHZX_ACCOUNTS："账号1#密码1&账号2#密码2...
多账号请用&隔开
注册地址：https://xhzhenxuan.net/addons/yun_shop/?menu#/register?pageType=register&i=1&type=5&shop_id&mid=20193
"""


import requests
import json
import random
import time
import os
import warnings

warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://xhzhenxuan.net"
USER_AGENT = "Mozilla/5.0 (Linux; Android 10; MI 8 Build/QKQ1.190828.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.96 Mobile Safari/537.36  XiaoMi/MiuiBrowser/10.8.1 LT-APP/48/134/YM-RT/"
LOG_PREFIX = "星汇甄选"

def log(msg):
    print(f"[{LOG_PREFIX}] {msg}", flush=True)

def login(session, username, password):
    url = f"{BASE_URL}/addons/yun_shop/api.php?i=1&uuid=0&type=5&app_id=null&version=v1.1.150&scope=pass&route=member.login.index"
    
    data = {
        "country": "86",
        "mobile": username,
        "password": password,
        "captcha": "",
        "uuid": 0,
        "mid": "20193",
        "mobileErr": "",
        "passwordErr": "",
        "login_checked": True,
        "is_sms": 0,
        "basic_info": 1
    }
    
    headers = {
        "Host": "xhzhenxuan.net",
        "Content-Length": str(len(json.dumps(data))),
        "Authorization": "Basic Og==",
        "Origin": BASE_URL,
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
        "Accept": "*/*",
        "X-Requested-With": "xh.zhenxuan.net",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cookie": "PHPSESSID=l0NJahJSSqVqaR3cjZrFH2mjChSvCI0M3zr4PrBC"
    }
    
    try:
        response = session.post(url, headers=headers, json=data, timeout=30, verify=False)
        response.encoding = 'utf-8'
        result = response.json()
        
        if "data" in result and "uid" in result["data"]:
            uid = str(result["data"]["uid"])
            log(f"✅ 登录成功, uid={uid}")
            return uid
        else:
            log(f"❌ 登录失败: {json.dumps(result, ensure_ascii=False)}")
            return None
    except Exception as e:
        log(f"❌ 登录异常: {e}")
        return None

def get_ad_info(session, uid):
    url = f"{BASE_URL}/addons/yun_shop/api.php?i=1&uuid=0&type=5&mid={uid}&version=v1.1.150&validate_page=1&app_id=null&route=plugin.lucky-draw.frontend.draw.index&lotteryId=1"
    
    headers = {
        "Host": "xhzhenxuan.net",
        "Authorization": "Basic Og==",
        "Local-Url": "/lottery",
        "User-Agent": USER_AGENT,
        "Full-Url": f"https://xhzhenxuan.net/addons/yun_shop/?menu#/lottery?lotteryId=1&mark=draw_activity&i=1",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "X-Requested-With": "xh.zhenxuan.net",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    try:
        response = session.get(url, headers=headers, timeout=30, verify=False)
        response.encoding = 'utf-8'
        result = response.json()
        
        if "data" in result:
            point = result["data"].get("point", 0)
            surplus_time = result["data"].get("surplus_time", 0)
            return point, surplus_time
        else:
            return None, None
    except Exception as e:
        return None, None

def sign_in(session, uid):
    url = f"{BASE_URL}/addons/yun_shop/api.php?i=1&uuid=0&type=5&mid={uid}&version=v1.1.150&validate_page=1&app_id=null&route=plugin.sign.Frontend.Modules.Sign.Controllers.sign.sign"
    
    headers = {
        "Host": "xhzhenxuan.net",
        "Authorization": "Basic Og==",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
        "Accept": "*/*",
        "X-Requested-With": "xh.zhenxuan.net",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    try:
        response = session.get(url, headers=headers, timeout=30, verify=False)
        response.encoding = 'utf-8'
        result = response.json()
        log(f"📝 签到响应: {json.dumps(result, ensure_ascii=False)}")
        return True
    except Exception as e:
        log(f"❌ 签到异常: {e}")
        return False

def get_ad(session, uid):
    url = f"{BASE_URL}/addons/yun_shop/api.php?i=1&uuid=0&type=5&mid={uid}&version=v1.1.150&validate_page=1&app_id=null&route=plugin.lucky-draw.frontend.draw.doDraw&lotteryId=1"
    
    headers = {
        "Host": "xhzhenxuan.net",
        "Authorization": "Basic Og==",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
        "Accept": "*/*",
        "X-Requested-With": "xh.zhenxuan.net",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    try:
        response = session.get(url, headers=headers, timeout=30, verify=False)
        response.encoding = 'utf-8'
        result = response.json()
        
        if "data" in result and "record_id" in result["data"]:
            record_id = str(result["data"]["record_id"])
            log(f"🎬 获取广告成功, record_id={record_id}")
            return record_id
        else:
            log(f"❌ 获取广告失败: {json.dumps(result, ensure_ascii=False)}")
            return None
    except Exception as e:
        log(f"❌ 获取广告异常: {e}")
        return None

def claim_prize(session, uid, record_id):
    url = f"{BASE_URL}/addons/yun_shop/api.php?i=1&uuid=0&type=5&mid={uid}&app_id=null&version=v1.1.150&validate_page=1&route=plugin.lucky-draw.frontend.draw.claimPrize"
    
    data = {"record_id": int(record_id)}
    
    headers = {
        "Host": "xhzhenxuan.net",
        "Authorization": "Basic Og==",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
        "Accept": "*/*",
        "X-Requested-With": "xh.zhenxuan.net",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    try:
        response = session.post(url, headers=headers, json=data, timeout=30, verify=False)
        response.encoding = 'utf-8'
        result = response.json()
        log(f"🎁 领取奖励响应: {json.dumps(result, ensure_ascii=False)}")
        return True
    except Exception as e:
        log(f"❌ 领取奖励异常: {e}")
        return False

def transfer(session, uid, point):
    if point is None or float(point) < 10000:
        return False
    
    point_value = float(point)
    change_value = int(point_value // 10000 * 10000)
    
    url = f"{BASE_URL}/addons/yun_shop/api.php?i=1&uuid=0&type=5&mid={uid}&version=v1.1.150&validate_page=1&app_id=null&route=plugin.period-credit.frontend.transfer.transfer&api=plugin.period-credit.frontend.transfer.get-detail&shop_id=null&transfer_mid=&change_value={change_value}"
    
    headers = {
        "Host": "xhzhenxuan.net",
        "Authorization": "Basic Og==",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
        "Accept": "*/*",
        "X-Requested-With": "xh.zhenxuan.net",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    try:
        response = session.get(url, headers=headers, timeout=30, verify=False)
        response.encoding = 'utf-8'
        result = response.json()
        log(f"💰 转账响应: {json.dumps(result, ensure_ascii=False)}")
        return True
    except Exception as e:
        log(f"❌ 转账异常: {e}")
        return False

def get_contribution(session, uid):
    url = f"{BASE_URL}/addons/yun_shop/api.php?i=1&uuid=0&type=5&mid={uid}&app_id=null&version=v1.1.150&validate_page=1&route=member.member.member-data"
    
    headers = {
        "Host": "xhzhenxuan.net",
        "Content-Length": "35",
        "Authorization": "Basic Og==",
        "Origin": "https://xhzhenxuan.net",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
        "Accept": "*/*",
        "X-Requested-With": "xh.zhenxuan.net",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    data = {"v": 2, "basic_info": 1, "page_id": ""}
    
    try:
        response = session.post(url, headers=headers, json=data, timeout=30, verify=False)
        response.encoding = 'utf-8'
        result = response.json()
        usable = result.get("basic_info", {}).get("home", {}).get("memberinfo", {}).get("usable", 0)
        log(f"📈 贡献值: {usable}")
        return usable
    except Exception as e:
        log(f"❌ 查询贡献值异常: {e}")
        return None

def run_account(username, password, idx, total):
    log(f"\n{'='*50}")
    log(f"🚀 账号 {idx}/{total} ({username[:3]}****{username[-4:]})")
    log(f"{'='*50}")
    
    session = requests.Session()
    session.verify = False
    
    log("🔐 正在登录...")
    uid = login(session, username, password)
    if not uid:
        log("❌ 登录失败, 跳过此账号")
        return {"success": False, "username": username, "point": None, "contribution": None}
    
    time.sleep(3)
    
    sign_in(session, uid)
    
    time.sleep(3)
    
    _, surplus_time = get_ad_info(session, uid)
    
    if surplus_time is None or surplus_time <= 0:
        log("✅ 广告剩余次数为0, 跳过广告任务")
        time.sleep(3)
        point, _ = get_ad_info(session, uid)
    else:
        total_ads = int(surplus_time)
        log(f"📊 任务: 目标{total_ads}, 剩余{total_ads}")
        log(f"⚙️ 本次执行 {total_ads} 个, 观看20~30s/个")
        
        log(f"\n🎬 开始看 {total_ads} 个广告...")
        
        for i in range(1, total_ads + 1):
            log(f"\n  📽️ ====== 第 {i}/{total_ads} 次看广告 ======")
            
            time.sleep(3)
            
            record_id = get_ad(session, uid)
            if not record_id:
                log(f"  ❌ 第 {i} 次获取广告失败, 跳过")
                continue
            
            watch = random.randint(20, 30)
            log(f"  ⏳ 模拟观看广告 {watch} 秒...")
            time.sleep(watch)
            
            claim_prize(session, uid, record_id)
            
            time.sleep(3)
        
        log(f"\n✅ 全部 {total_ads} 次广告观看完成")
        
        time.sleep(3)
        
        point, _ = get_ad_info(session, uid)
        
        time.sleep(3)
        
        transfer(session, uid, point)
    
    time.sleep(3)
    
    contribution = get_contribution(session, uid)
    
    log(f"\n{'='*50}")
    log(f"📊 账号{idx}状态: 金币余额={point if point is not None else '未知'}, 贡献值={contribution if contribution is not None else '未知'}")
    log(f"{'='*50}")
    
    return {"success": True, "username": username, "point": point, "contribution": contribution}

def main():
    log("🤖 星汇甄选每日任务 启动")
    log(f"⏰ 运行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    accounts_env = os.environ.get("XHZX_ACCOUNTS", "")
    if not accounts_env:
        log("❌ 未设置环境变量 XHZX_ACCOUNTS")
        log("请在青龙 -> 环境变量 添加:")
        log("  XHZX_ACCOUNTS    账号#密码, 多账号用 & 分隔")
        log("示例: XHZX_ACCOUNTS='19281219747#hss567890&17776532590#hsxnb666'")
        return
    
    accounts = []
    for item in accounts_env.split("&"):
        if "#" in item:
            username, password = item.split("#", 1)
            accounts.append((username.strip(), password.strip()))
        else:
            log(f"⚠️ 忽略格式错误的账号: {item[:20]}...")
    
    n = len(accounts)
    if n == 0:
        log("❌ 没有有效的账号")
        return
    
    log(f"📝 共 {n} 个账号")
    log(f"🔑 自动登录 + 签到 + 看广告 + 转账 + 贡献值查询")
    
    results = []
    
    for i in range(1, n + 1):
        username, password = accounts[i - 1]
        result = run_account(username, password, i, n)
        results.append(result)
        
        if i < n:
            wait = random.randint(5, 10)
            log(f"\n⏳ 账号间隔 {wait} 秒...")
            time.sleep(wait)
    
    log(f"\n{'='*50}")
    log(f"📊 全部账号执行完毕")
    log(f"{'='*50}")
    
    for i, result in enumerate(results, 1):
        log(f"📌 执行账号{i}: {result['username']}")
        log(f"   金币余额: {result['point'] if result['point'] is not None else '未知'}")
        log(f"   贡献值: {result['contribution'] if result['contribution'] is not None else '未知'}")
        if i < len(results):
            log(f"{'='*50}")
    
    try:
        from notify import send
        summary_lines = []
        for i, result in enumerate(results, 1):
            summary_lines.append(f"账号{i}({result['username'][:3]}****{result['username'][-4:]}): 金币{result['point']}, 贡献值{result['contribution']}")
        summary = "\n".join(summary_lines)
        send(LOG_PREFIX, summary)
    except Exception:
        pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("用户中断")
    except Exception as e:
        log(f"❌ 异常退出: {e}")

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