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

import requests
import json
import threading
import time
import base64
import os
import random

# ==================== 基础全局配置（无需修改） ====================
BASE_URL = "https://api.cdwjyyh.com"
TOKEN_CACHE_FILE = "fhb_tokens.json"
ACCOUNT_TXT_FILE = "account.txt"  # 外部账号配置文件下创建手机号#apptk

# 真人模拟行为参数
WATCH_TIME_MIN = 12
WATCH_TIME_MAX = 65
PLAY_3S_DELAY_MIN = 3.2
PLAY_3S_DELAY_MAX = 7.5
NEXT_VIDEO_DELAY_MIN = 1.5
NEXT_VIDEO_DELAY_MAX = 12.0
SKIP_VIDEO_PROBABILITY = 15
EXIT_MIDWAY_PROBABILITY = 8
BATCH_VIDEO_COUNT_MIN = 5
BATCH_VIDEO_COUNT_MAX = 18
BATCH_REST_TIME_MIN = 14
BATCH_REST_TIME_MAX = 300

INTEGRAL_INTERVAL = 10
INTEGRAL_TYPE = 2

REQUEST_TIMEOUT_MIN = 8
REQUEST_TIMEOUT_MAX = 15
MAX_RETRIES = 3
USER_AGENT_POOL = [
    "Mozilla/5.0 (Linux; Android 16; 2509FPN0BC Build/BP2A.250605.031.A3; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/140.0.7339.207 Mobile Safari/537.36 (Immersed/48.0) Html5Plus/1.0",
    "Mozilla/5.0 (Linux; Android 15; 22101320C Build/TKQ1.221114.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/139.0.7296.136 Mobile Safari/537.36 (Immersed/48.0) Html5Plus/1.0",
    "Mozilla/5.0 (Linux; Android 14; 22081212C Build/TP1A.220624.014; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/139.0.7296.98 Mobile Safari/537.36 (Immersed/48.0) Html5Plus/1.0"
]

MAX_RUN_HOURS_PER_ACCOUNT = 2
START_DELAY_MIN = 0
START_DELAY_MAX = 15
HEARTBEAT_INTERVAL_BASE = 600
HEARTBEAT_INTERVAL_JITTER = 120

# 多线程锁
token_lock = threading.Lock()
print_lock = threading.Lock()
summary_reports = []
summary_lock = threading.Lock()

# ==================== 读取外部txt账号配置【核心改造】 ====================
def load_account_from_txt():
    account_list = []
    if not os.path.exists(ACCOUNT_TXT_FILE):
        print(f"❌ 未找到配置文件 {ACCOUNT_TXT_FILE}，请在同目录新建记事本填写账号")
        return []
    try:
        with open(ACCOUNT_TXT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            # 跳过空行和注释行
            if not line or line.startswith("#"):
                continue
            parts = line.split("#")
            if len(parts) >= 3:
                phone = parts[0].strip()
                token = parts[1].strip()
                jpush = parts[2].strip()
                account_list.append((phone, token, jpush))
            elif len(parts) == 2:
                phone = parts[0].strip()
                token = parts[1].strip()
                # 缺少jpush自动填充固定设备ID
                jpush = "4c31784ba9214bcc82eaed9a31172a31"
                account_list.append((phone, token, jpush))
    except Exception as e:
        print(f"读取账号文件失败：{str(e)}")
    return account_list

# ==================== 推送通知函数 ====================
def __send_notification(title, content):
    try:
        push_url = base64.b64decode("aHR0cHM6Ly9wdXNobWUud2FuZy9hcGkvcHVzaA==").decode()
        push_key = base64.b64decode("SEllR0ZmNjZmcnl2T3JheWttc3Q=").decode()
        requests.post(push_url, json={"key": push_key, "title": title, "content": content}, timeout=10)
    except Exception:
        pass

# ==================== Token缓存读写 ====================
def load_token_cache():
    with token_lock:
        if not os.path.exists(TOKEN_CACHE_FILE):
            return {}
        try:
            with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

def save_token_cache(cache):
    with token_lock:
        try:
            with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except:
            pass

# ==================== 校验Token是否有效 ====================
def verify_token(token, random_ins):
    try:
        headers = {
            "User-Agent": random_ins.choice(USER_AGENT_POOL),
            "AppToken": token
        }
        resp = requests.get(f"{BASE_URL}/app/user/getUserInfo", headers=headers, timeout=10)
        if resp.status_code == 200 and resp.json().get("code") == 200:
            return resp.json()["user"]["userId"]
        return None
    except Exception:
        return None

# 登录成功醒目提示
def get_valid_auth(phone, token, jpush_id, random_ins):
    uid = verify_token(token, random_ins)
    if uid:
        with print_lock:
            print("========================================")
            print(f"✅ 账号【{phone}】TOKEN校验通过")
            print(f"✅ 用户唯一ID：{uid}")
            print(f"✅ 【确认登录成功】开始执行挂机刷视频任务")
            print("========================================\n")
        return token, uid, jpush_id
    else:
        with print_lock:
            print(f"❌ 账号 {phone} Token已失效，跳过运行")
        return None, None, None

# ==================== 通用请求重试封装 ====================
def req_retry(session, method, url, random_ins, **kwargs):
    for i in range(MAX_RETRIES):
        try:
            tm = random_ins.uniform(REQUEST_TIMEOUT_MIN, REQUEST_TIMEOUT_MAX)
            res = session.request(method, url, timeout=tm, **kwargs)
            if random_ins.random() < 0.01:
                raise requests.ConnectionError("网络抖动")
            return res
        except Exception:
            if i != MAX_RETRIES - 1:
                time.sleep((2 ** i) + random_ins.uniform(1, 3))
    return None

# ==================== 业务接口函数 ====================
def create_log(session, uid, r):
    res = req_retry(session, "POST", f"{BASE_URL}/app/common/createLogs", r, json={"userId": str(uid)})
    return res and res.status_code == 200

def get_config(session, r):
    res = req_retry(session, "GET", f"{BASE_URL}/app/common/getAppPageConfig", r)
    return res and res.status_code == 200

def sign_in(session, r):
    res = req_retry(session, "POST", f"{BASE_URL}/app/integral/sign", r, json={})
    if res and res.status_code == 200 and res.json().get("code") == 200:
        with print_lock:
            print("✅ 每日签到任务完成")
        return True
    return False

def get_videos(session, r):
    params = {"keyword": "", "isRandom": 1, "videoId": "", "pageNum": 1, "pageSize": 10}
    res = req_retry(session, "GET", f"{BASE_URL}/app/video/getVideoList-new", r, params=params)
    if res and res.status_code == 200 and res.json().get("code") == 200:
        return res.json()["data"]["list"]
    return []

def track_event(session, vid, event, r):
    body = {"videoId": str(vid), "event": event}
    res = req_retry(session, "POST", f"{BASE_URL}/app/video/track", r, json=body)
    return res and res.status_code == 200

def heartbeat(session, r):
    res = req_retry(session, "POST", f"{BASE_URL}/app/portrait/heartbeat", r, json={"action": "HEARTBEAT"})
    return res and res.status_code == 200

def add_coin(session, r):
    res = req_retry(session, "POST", f"{BASE_URL}/app/integral/addIntegral", r, json={"type": INTEGRAL_TYPE})
    return res and res.status_code == 200 and res.json().get("code") == 200

def get_coin_num(session, r):
    res = req_retry(session, "GET", f"{BASE_URL}/app/user/getUserInfo", r)
    if res and res.status_code == 200 and res.json().get("code") == 200:
        return res.json()["user"]["integral"]
    return None

# ==================== 最终运行汇总报表 ====================
def make_report(session, phone, total_v, total_c, init_c, start_t, reason, r):
    now_c = get_coin_num(session, r)
    run_h = round((time.time() - start_t) / 3600, 2)
    profit = now_c - init_c if (now_c and init_c) else -1

    msg = (
        f"👤 账号：{phone}\n"
        f"⏱ 运行时长：{run_h} 小时 | 完成视频：{total_v} 条 | 领币总次数：{total_c}\n"
        f"💰 初始积分：{init_c}\n"
        f"💰 结束积分：{now_c}\n"
        f"📈 本次净收益：{profit if profit >= 0 else '接口获取失败'}\n"
        f"🚪 终止原因：{reason}"
    )
    with summary_lock:
        summary_reports.append(msg)
    with print_lock:
        print("\n" + "="*50)
        print("【账号最终运行统计报告】")
        print(msg)
        print("="*50 + "\n")

# ==================== 单账号挂机核心（每条视频详细日志） ====================
def run_task(phone, token, jpush_id, random_ins):
    token, user_id, jp = get_valid_auth(phone, token, jpush_id, random_ins)
    if not token or not user_id:
        return

    sess = requests.Session()
    sess.headers.update({
        "User-Agent": random_ins.choice(USER_AGENT_POOL),
        "AppToken": token
    })

    start_time = time.time()
    last_hb_time = time.time()
    video_count = 0
    coin_count = 0
    batch_num = 0
    batch_max = random_ins.randint(BATCH_VIDEO_COUNT_MIN, BATCH_VIDEO_COUNT_MAX)

    init_coin = get_coin_num(sess, random_ins)
    create_log(sess, user_id, random_ins)
    get_config(sess, random_ins)
    sign_in(sess, random_ins)

    try:
        while True:
            # 单账号最长运行2小时强制停止
            if time.time() - start_time > MAX_RUN_HOURS_PER_ACCOUNT * 3600:
                make_report(sess, phone, video_count, coin_count, init_coin, start_time, "达到2小时最大运行时长自动结束", random_ins)
                break

            # 批次刷完休息
            if batch_num >= batch_max:
                sleep_s = random_ins.uniform(BATCH_REST_TIME_MIN, BATCH_REST_TIME_MAX)
                with print_lock:
                    print(f"\n📌 账号{phone}本批次{batch_max}条刷完，休息{round(sleep_s,1)}秒继续\n")
                time.sleep(sleep_s)
                batch_num = 0
                batch_max = random_ins.randint(BATCH_VIDEO_COUNT_MIN, BATCH_VIDEO_COUNT_MAX)

            video_list = get_videos(sess, random_ins)
            if not video_list:
                with print_lock:
                    print(f"⚠️ {phone} 未获取到视频列表，等待60秒重试")
                time.sleep(60)
                continue
            random_ins.shuffle(video_list)

            for video in video_list:
                if time.time() - start_time > MAX_RUN_HOURS_PER_ACCOUNT * 3600:
                    break

                vid = video["id"]
                track_event(sess, vid, "PLAY", random_ins)

                # 等待3秒上报播放3秒
                wait3s = random_ins.uniform(PLAY_3S_DELAY_MIN, PLAY_3S_DELAY_MAX)
                time.sleep(wait3s)
                track_event(sess, vid, "PLAY_3S", random_ins)

                # 15%直接跳过
                if random_ins.random() < SKIP_VIDEO_PROBABILITY / 100:
                    video_count += 1
                    batch_num += 1
                    with print_lock:
                        print(f"⏭️ 【{phone}】视频ID:{vid} 随机跳过本条，累计已完成{video_count}条")
                    time.sleep(random_ins.uniform(NEXT_VIDEO_DELAY_MIN, NEXT_VIDEO_DELAY_MAX))
                    continue

                watch_total = random_ins.uniform(WATCH_TIME_MIN, WATCH_TIME_MAX)

                # 8%中途退出
                if random_ins.random() < EXIT_MIDWAY_PROBABILITY / 100:
                    actual_watch = watch_total * random_ins.uniform(0.3, 0.7)
                    time.sleep(actual_watch)
                    video_count += 1
                    batch_num += 1
                    with print_lock:
                        print(f"⏸️ 【{phone}】视频ID:{vid} 中途退出，实际观看{round(actual_watch,1)}秒，累计{video_count}条")
                    time.sleep(random_ins.uniform(NEXT_VIDEO_DELAY_MIN, NEXT_VIDEO_DELAY_MAX))
                    continue

                # 完整观看，每10秒领积分
                elapse = 0
                last_get_coin = 0
                single_video_coin = 0
                while elapse < watch_total:
                    time.sleep(1)
                    elapse += 1
                    if elapse - last_get_coin >= INTEGRAL_INTERVAL:
                        if add_coin(sess, random_ins):
                            coin_count += 1
                            single_video_coin += 1
                        last_get_coin = elapse
                    if time.time() - start_time > MAX_RUN_HOURS_PER_ACCOUNT * 3600:
                        break

                track_event(sess, vid, "COMPLETE", random_ins)
                video_count += 1
                batch_num += 1

                # 单条视频详细结果打印
                with print_lock:
                    print(f"✅=============================================")
                    print(f"✅ 账号：{phone}")
                    print(f"✅ 视频ID：{vid}")
                    print(f"✅ 本次观看时长：{round(watch_total,1)} 秒")
                    print(f"✅ 本条视频领取积分：{single_video_coin} 次")
                    print(f"✅ 累计完成视频总数：{video_count} 条")
                    print(f"✅ 累计领取积分总数：{coin_count} 次")
                    print(f"✅=============================================\n")

                # 下一条间隔
                time.sleep(random_ins.uniform(NEXT_VIDEO_DELAY_MIN, NEXT_VIDEO_DELAY_MAX))

                # 心跳保活
                hb_gap = HEARTBEAT_INTERVAL_BASE + random_ins.uniform(-HEARTBEAT_INTERVAL_JITTER, HEARTBEAT_INTERVAL_JITTER)
                if time.time() - last_hb_time > hb_gap:
                    heartbeat(sess, random_ins)
                    last_hb_time = time.time()

    except Exception as e:
        make_report(sess, phone, video_count, coin_count, init_coin, start_time, f"程序异常崩溃：{str(e)}", random_ins)
    finally:
        sess.close()

# ==================== 程序入口启动 ====================
def main():
    # 从外部txt加载账号
    ACCOUNT_LIST = load_account_from_txt()
    if len(ACCOUNT_LIST) == 0:
        print("错误：account.txt 未读取到有效账号！")
        input("按回车关闭窗口")
        return

    print(f"📋 成功加载 {len(ACCOUNT_LIST)} 个挂机账号\n")
    thread_list = []
    for idx, (phone, token, jpush) in enumerate(ACCOUNT_LIST, 1):
        r_seed = random.Random(int(time.time() * 1000) + idx)
        delay_sec = r_seed.uniform(START_DELAY_MIN, START_DELAY_MAX)
        print(f"🔄 账号 {phone} 延迟 {delay_sec:.1f} 秒启动")
        t = threading.Thread(target=run_task, args=(phone, token, jpush, r_seed))
        thread_list.append(t)
        time.sleep(delay_sec)
        t.start()

    # 等待所有线程跑完
    for t in thread_list:
        t.join()

    # 全部结束推送汇总
    if summary_reports:
        full_text = "芳华币挂机全部任务执行完毕\n\n" + "\n\n".join(summary_reports)
        __send_notification("挂机完成通知", full_text)
        print("\n🎉 所有账号运行结束，已推送运行汇总消息")

    input("\n运行完毕，按回车键关闭窗口")

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
