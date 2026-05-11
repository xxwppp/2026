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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import argparse
import time
import random
import os
import sys
from requests.exceptions import RequestException, ConnectionError
from concurrent.futures import ThreadPoolExecutor, as_completed

# ================= 代理管理类 =================
class ProxyManager:
    def __init__(self, proxy_url, max_proxies=5, max_uses_per_proxy=10):
        self.proxy_url = proxy_url
        self.max_proxies = max_proxies
        self.max_uses_per_proxy = max_uses_per_proxy
        self.current_proxy = None
        self.proxy_use_count = 0
        self.proxy_used_count = 0
        self.use_proxy = True

    def _fetch_proxy(self):
        if not self.proxy_url:
            print("⚠️ 未配置代理获取URL，将使用直连")
            self.use_proxy = False
            return None
        try:
            resp = requests.get(self.proxy_url, timeout=5)
            if resp.status_code == 200 and resp.text.strip():
                proxy = resp.text.strip()
                print(f"🔄 获取到新代理: {proxy}")
                return proxy
            else:
                print(f"⚠️ 代理API返回异常: {resp.text[:100]}")
        except Exception as e:
            print(f"⚠️ 获取代理失败: {e}")
        print("⚠️ 无法获取代理，将降级为直连模式")
        self.use_proxy = False
        return None

    def get_current_proxy(self):
        if not self.use_proxy:
            return None
        if self.current_proxy is None or self.proxy_use_count >= self.max_uses_per_proxy:
            if self.proxy_used_count >= self.max_proxies:
                print(f"⚠️ 已达到最大代理数量限制 ({self.max_proxies})，后续请求将使用直连")
                self.use_proxy = False
                return None
            new_proxy = self._fetch_proxy()
            if new_proxy:
                self.current_proxy = new_proxy
                self.proxy_use_count = 0
                self.proxy_used_count += 1
                print(f"✅ 启用新代理 [{self.proxy_used_count}/{self.max_proxies}]: {self.current_proxy}")
            else:
                self.use_proxy = False
                return None
        return {
            'http': f'http://{self.current_proxy}',
            'https': f'http://{self.current_proxy}'
        }

    def mark_success(self):
        if self.use_proxy and self.current_proxy:
            self.proxy_use_count += 1
            print(f"📊 代理使用进度: {self.proxy_use_count}/{self.max_uses_per_proxy}")

    def mark_failure_and_switch(self):
        if self.use_proxy and self.current_proxy:
            print(f"⚠️ 当前代理 {self.current_proxy} 请求失败，立即切换新代理")
            self.current_proxy = None
            self.proxy_use_count = 0
            if self.proxy_used_count >= self.max_proxies:
                print(f"⚠️ 已达到最大代理数量限制 ({self.max_proxies})，无法切换新代理，将使用直连")
                self.use_proxy = False

# ================= 带代理的请求函数 =================
def request_with_proxy(method, url, headers, data=None, proxy_manager=None, timeout=10, max_retries=3):
    retries = 0
    while retries < max_retries:
        proxies = proxy_manager.get_current_proxy() if proxy_manager else None
        try:
            if method.upper() == 'GET':
                resp = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
            elif method.upper() == 'POST':
                resp = requests.post(url, headers=headers, json=data, proxies=proxies, timeout=timeout)
            else:
                raise ValueError(f"不支持的请求方法: {method}")
            if resp.status_code < 400:
                if proxy_manager:
                    proxy_manager.mark_success()
                return resp
            else:
                print(f"⚠️ 请求返回状态码 {resp.status_code}，将重试")
                if proxy_manager:
                    proxy_manager.mark_failure_and_switch()
                retries += 1
                time.sleep(2)
        except (RequestException, ConnectionError) as e:
            print(f"⚠️ 网络请求异常: {e}")
            if proxy_manager:
                proxy_manager.mark_failure_and_switch()
            retries += 1
            time.sleep(2)
    print(f"❌ 请求最终失败，已重试 {max_retries} 次: {url}")
    return None

# ================= 业务接口函数 =================
def get_eat_gold(token, proxy_manager):
    """调用 /integral/eatGold 领取补贴金币"""
    url = "https://api.tianjinzhitongdaohe.com/sqx_fast/app/integral/eatGold"
    headers = {
        "Host": "api.tianjinzhitongdaohe.com",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf254181d) XWEB/19201",
        "xweb_xhr": "1",
        "Content-Type": "application/x-www-form-urlencoded",
        "token": token,
        "Accept": "*/*",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://servicewechat.com/wxcb95401f250e9a53/19/page-frame.html",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    resp = request_with_proxy('GET', url, headers, proxy_manager=proxy_manager)
    if resp:
        try:
            return resp.json()
        except:
            return {"error": "非JSON响应", "text": resp.text[:200]}
    return None

def get_recommend_courses(token, proxy_manager):
    """获取每日推荐剧集列表，返回课程ID列表"""
    url = "https://api.tianjinzhitongdaohe.com/sqx_fast/app/common/type/922"
    headers = {
        "Host": "api.tianjinzhitongdaohe.com",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf254181d) XWEB/19201",
        "xweb_xhr": "1",
        "Content-Type": "application/x-www-form-urlencoded",
        "token": token,
        "Accept": "*/*",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://servicewechat.com/wxcb95401f250e9a53/19/page-frame.html",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    resp = request_with_proxy('GET', url, headers, proxy_manager=proxy_manager)
    if resp:
        try:
            data = resp.json()
            if data.get('code') == 0 and 'data' in data:
                value_str = data['data'].get('value', '')
                if value_str:
                    course_ids = [int(x.strip()) for x in value_str.split(',') if x.strip().isdigit()]
                    return course_ids
                else:
                    print("⚠️ 推荐列表为空")
                    return []
            else:
                print(f"⚠️ 获取推荐列表失败: {data.get('msg')}")
        except Exception as e:
            print(f"解析推荐列表响应失败: {e}")
    return []

def get_course_details(course_id, token, proxy_manager):
    """获取课程详情（包含所有剧集列表）"""
    url = f"https://api.tianjinzhitongdaohe.com/sqx_fast/app/course/selectCourseDetailsById?id={course_id}"
    headers = {
        "Host": "api.tianjinzhitongdaohe.com",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf254181d) XWEB/19201",
        "xweb_xhr": "1",
        "Content-Type": "application/x-www-form-urlencoded",
        "token": token,
        "Accept": "*/*",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://servicewechat.com/wxcb95401f250e9a53/19/page-frame.html",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    resp = request_with_proxy('GET', url, headers, proxy_manager=proxy_manager)
    if resp:
        try:
            data = resp.json()
            if data.get('code') == 0 and 'data' in data:
                return data['data']
            else:
                print(f"⚠️ 获取课程 {course_id} 详情失败: {data.get('msg')}")
        except Exception as e:
            print(f"解析课程详情失败: {e}")
    return None

def insert_course_collect(course_id, course_details_id, classify, collect_type, token, proxy_manager):
    """
    收藏/点赞/评论等操作
    :param course_id: 课程ID
    :param course_details_id: 剧集ID
    :param classify: 分类，如 2(点赞),3(收藏)
    :param collect_type: 类型，0=取消/点赞? 1=收藏? 根据示例推断
    :param token: 用户token
    :param proxy_manager: 代理管理器
    """
    url = "https://api.tianjinzhitongdaohe.com/sqx_fast/app/courseCollect/insertCourseCollect"
    headers = {
        "Host": "api.tianjinzhitongdaohe.com",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf254181d) XWEB/19201",
        "xweb_xhr": "1",
        "Content-Type": "application/json",
        "token": token,
        "Accept": "*/*",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://servicewechat.com/wxcb95401f250e9a53/19/page-frame.html",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    payload = {
        "courseId": course_id,
        "courseDetailsId": course_details_id,
        "classify": classify,
        "type": collect_type
    }
    resp = request_with_proxy('POST', url, headers, data=payload, proxy_manager=proxy_manager)
    if resp:
        try:
            return resp.json()
        except:
            return {"error": "非JSON响应", "text": resp.text[:200]}
    return None

# ================= 多账号处理（线程任务） =================
def process_account(token, account_index, proxy_url, delay_between_requests=3, max_courses=2, max_episodes_per_course=3):
    """
    处理单个账号：
    0. 调用 eatGold 领取补贴
    1. 获取推荐课程列表
    2. 对每个课程获取详情
    3. 对课程的部分剧集进行点赞和收藏
    """
    print(f"\n[账号 {account_index}] {'='*50}")
    print(f"[账号 {account_index}] 开始处理，Token: {token[:20]}...")
    print(f"[账号 {account_index}] 代理策略：最多5个代理，每个代理最多10次")
    print(f"[账号 {account_index}] 请求间隔: {delay_between_requests} 秒")

    proxy_manager = ProxyManager(proxy_url, max_proxies=5, max_uses_per_proxy=10)

    # 0. 先调用 eatGold 领取补贴
    print(f"\n[账号 {account_index}] 正在领取 eatGold 补贴...")
    eat_resp = get_eat_gold(token, proxy_manager)
    if eat_resp:
        print(f"[账号 {account_index}] eatGold 响应: {eat_resp}")
    else:
        print(f"[账号 {account_index}] eatGold 请求失败")

    # 请求间隔（可选）
    if delay_between_requests > 0:
        time.sleep(delay_between_requests)

    # 1. 获取推荐课程ID列表
    print(f"\n[账号 {account_index}] 正在获取推荐课程列表...")
    course_ids = get_recommend_courses(token, proxy_manager)
    if not course_ids:
        print(f"[账号 {account_index}] 未获取到推荐课程，退出")
        return
    print(f"[账号 {account_index}] 获取到推荐课程ID: {course_ids}")

    # 只处理前 max_courses 个课程（避免过多请求）
    selected_course_ids = course_ids[:max_courses]

    for idx, cid in enumerate(selected_course_ids, 1):
        print(f"\n[账号 {account_index}] 处理课程 {idx}/{len(selected_course_ids)}: ID={cid}")
        # 获取课程详情
        course_data = get_course_details(cid, token, proxy_manager)
        if not course_data:
            print(f"[账号 {account_index}] 课程 {cid} 详情获取失败")
            continue

        episode_list = course_data.get('listsDetail', [])  # 注意字段名可能是 listsDetail 或 courseDetailsList
        if not episode_list:
            # 尝试其他可能的字段名
            episode_list = course_data.get('courseDetailsList', [])
        if not episode_list:
            print(f"[账号 {account_index}] 课程 {cid} 没有剧集数据")
            continue

        print(f"[账号 {account_index}] 课程 {cid} 共有 {len(episode_list)} 集")
        # 只处理前 max_episodes_per_course 集
        episodes_to_process = episode_list[:max_episodes_per_course]

        for ep in episodes_to_process:
            details_id = ep.get('courseDetailsId')
            if not details_id:
                continue

            # 延迟控制
            if delay_between_requests > 0:
                sleep_time = random.uniform(delay_between_requests - 1, delay_between_requests + 1)
                print(f"[账号 {account_index}] 等待 {sleep_time:.2f} 秒...")
                time.sleep(sleep_time)

            # 收藏（classify=3, type=1）
            print(f"[账号 {account_index}] 收藏剧集 {details_id}...")
            collect_resp = insert_course_collect(cid, details_id, 3, 1, token, proxy_manager)
            if collect_resp:
                print(f"[账号 {account_index}] 收藏响应: {collect_resp}")

            # 延迟
            if delay_between_requests > 0:
                sleep_time = random.uniform(delay_between_requests - 1, delay_between_requests + 1)
                print(f"[账号 {account_index}] 等待 {sleep_time:.2f} 秒...")
                time.sleep(sleep_time)

            # 点赞（classify=2, type=0）
            print(f"[账号 {account_index}] 点赞剧集 {details_id}...")
            like_resp = insert_course_collect(cid, details_id, 2, 0, token, proxy_manager)
            if like_resp:
                print(f"[账号 {account_index}] 点赞响应: {like_resp}")

    # 可选：最后调用一次 selectMessageCount 检查消息数
    if delay_between_requests > 0:
        time.sleep(delay_between_requests)
    print(f"\n[账号 {account_index}] 调用 selectMessageCount 接口...")
    url_msg = "https://api.tianjinzhitongdaohe.com/sqx_fast/app/message/selectMessageCount"
    headers = {
        "Host": "api.tianjinzhitongdaohe.com",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf254181d) XWEB/19201",
        "xweb_xhr": "1",
        "Content-Type": "application/x-www-form-urlencoded",
        "token": token,
        "Accept": "*/*",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://servicewechat.com/wxcb95401f250e9a53/19/page-frame.html",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    msg_resp = request_with_proxy('GET', url_msg, headers, proxy_manager=proxy_manager)
    if msg_resp:
        try:
            print(f"[账号 {account_index}] 消息数量: {msg_resp.json()}")
        except:
            print(f"[账号 {account_index}] 消息接口响应: {msg_resp.text[:100]}")

    print(f"\n[账号 {account_index}] ✅ 处理完毕")

# ================= 主函数 =================
def main():
    parser = argparse.ArgumentParser(description="多账号自动收藏/点赞推荐短剧（支持代理轮换和并发）")
    parser.add_argument("-d", "--delay", type=float, default=3, help="每个请求之间的延迟秒数 (默认3秒)")
    parser.add_argument("-c", "--concurrent", type=int, default=3, help="并发账号数量 (默认3)")
    parser.add_argument("-t", "--token", type=str, help="单个账号的token（与-f互斥）")
    parser.add_argument("-f", "--file", type=str, help="包含多个token的文件，每行一个token")
    parser.add_argument("-p", "--proxy-url", type=str, default=os.getenv("douya15", ""),
                        help="获取代理的API地址，可从环境变量 douya15 读取。留空则直连")
    parser.add_argument("--max-courses", type=int, default=2, help="每个账号最多处理几个推荐课程 (默认2)")
    parser.add_argument("--max-episodes", type=int, default=3, help="每个课程最多处理几集 (默认3)")
    args = parser.parse_args()

    # 收集所有token
    tokens = []
    if args.token:
        tokens.append(args.token)
    elif args.file:
        if not os.path.exists(args.file):
            print(f"错误：文件 {args.file} 不存在")
            sys.exit(1)
        with open(args.file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    tokens.append(line)
    else:
        env_tokens = os.getenv("niuniuTOKENS", "")
        if env_tokens:
            tokens = [t.strip() for t in env_tokens.split('\n') if t.strip()]
        else:
            print("错误：请通过 -t、-f 或环境变量 niuniuTOKENS 提供至少一个token")
            sys.exit(1)

    if not tokens:
        print("错误：未提供任何有效的token")
        sys.exit(1)

    print(f"共加载 {len(tokens)} 个账号")
    print(f"并发数: {args.concurrent}")
    print(f"每个账号最多处理 {args.max_courses} 个课程，每个课程最多处理 {args.max_episodes} 集")
    if args.proxy_url:
        print(f"使用代理API: {args.proxy_url}")
    else:
        print("未配置代理API，将使用直连模式")

    # 并发执行
    with ThreadPoolExecutor(max_workers=args.concurrent) as executor:
        futures = []
        for idx, token in enumerate(tokens, start=1):
            future = executor.submit(
                process_account, token, idx, args.proxy_url,
                args.delay, args.max_courses, args.max_episodes
            )
            futures.append(future)

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"❌ 线程执行出错: {e}")

    print("\n🎉 所有账号处理完毕")

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