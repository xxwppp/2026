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
from datetime import datetime
from requests.exceptions import RequestException, ConnectionError

# ================= 代理管理类 =================
class ProxyManager:
    """每个账号独立的代理管理器，支持最多5个代理，每个代理最多使用10次"""
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
def request_with_proxy(method, url, headers, proxy_manager=None, timeout=10, max_retries=3):
    retries = 0
    while retries < max_retries:
        proxies = proxy_manager.get_current_proxy() if proxy_manager else None
        try:
            if method.upper() == 'GET':
                resp = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
            else:
                resp = requests.post(url, headers=headers, proxies=proxies, timeout=timeout)
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
def sign_in(token, proxy_manager):
    """调用签到接口，使用当前日期"""
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://api.tianjinzhitongdaohe.com/sqx_fast/app/integral/signIn?date={today}"
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
    resp = request_with_proxy('GET', url, headers, proxy_manager, timeout=10)
    if resp:
        try:
            return resp.json()
        except:
            return {"error": "非JSON响应", "text": resp.text[:200]}
    return None

def add_look_video_num(token, proxy_manager):
    url = "https://api.tianjinzhitongdaohe.com/sqx_fast/app/integral/addLookVideoNum"
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
    resp = request_with_proxy('GET', url, headers, proxy_manager, timeout=10)
    if resp:
        try:
            return resp.json()
        except:
            return {"error": "非JSON响应", "text": resp.text[:200]}
    return None

def get_look_video_num(token, proxy_manager):
    url = "https://api.tianjinzhitongdaohe.com/sqx_fast/app/integral/lookVideoNum"
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
    resp = request_with_proxy('GET', url, headers, proxy_manager, timeout=10)
    if resp:
        try:
            return resp.json()
        except:
            return {"error": "非JSON响应", "text": resp.text[:200]}
    return None

# ================= 多账号处理 =================
def process_account(token, account_index, total_times, proxy_url, delay_between_requests=5):
    print(f"\n{'='*50}")
    print(f"开始处理账号 {account_index}，Token: {token[:20]}...")
    print(f"将执行 {total_times} 次增加视频次数请求，每次请求间隔约 {delay_between_requests} 秒")
    print(f"代理策略：最多5个代理，每个代理最多使用10次")
    print(f"{'='*50}")

    proxy_manager = ProxyManager(proxy_url, max_proxies=5, max_uses_per_proxy=10)

    # ---------- 新增：先执行签到 ----------
    print(f"\n[账号 {account_index}] 正在执行签到...")
    sign_resp = sign_in(token, proxy_manager)
    if sign_resp:
        print(f"签到响应: {sign_resp}")
    else:
        print("签到请求失败")
    # 签到后稍作延迟，避免请求过快
    if delay_between_requests > 0:
        time.sleep(delay_between_requests)
    # ------------------------------------

    for i in range(1, total_times + 1):
        print(f"\n--- 账号 {account_index} 第 {i}/{total_times} 次增加请求 ---")

        add_resp = add_look_video_num(token, proxy_manager)
        if add_resp:
            print(f"增加接口响应: {add_resp}")
            if add_resp.get('code') == 500 and add_resp.get('msg') == '调用失败,请联系客服处理':
                print("⚠️ 检测到失败响应，立即调用查询接口 lookVideoNum ...")
                query_resp = get_look_video_num(token, proxy_manager)
                if query_resp:
                    print(f"查询接口响应: {query_resp}")
                else:
                    print("查询接口调用失败")
        else:
            print("增加接口请求失败（网络错误或超时）")

        if i < total_times:
            sleep_time = random.uniform(delay_between_requests - 1, delay_between_requests + 1)
            print(f"等待 {sleep_time:.2f} 秒后继续...")
            time.sleep(sleep_time)

    print(f"\n✅ 账号 {account_index} 所有请求处理完毕")

# ================= 主函数 =================
def main():
    parser = argparse.ArgumentParser(description="多账号视频积分脚本（支持代理轮换），运行前自动签到")
    parser.add_argument("-n", "--num", type=int, default=14, help="每个账号执行增加次数的次数 (默认20)")
    parser.add_argument("-d", "--delay", type=float, default=5, help="每个接口请求之间的延迟秒数 (默认5秒)")
    parser.add_argument("-t", "--token", type=str, help="单个账号的token（与-f互斥）")
    parser.add_argument("-f", "--file", type=str, help="包含多个token的文件，每行一个token")
    parser.add_argument("-p", "--proxy-url", type=str, default=os.getenv("douya15", ""),
                        help="获取代理的API地址，可从环境变量 douya15 读取。留空则直连")
    args = parser.parse_args()

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
    if args.proxy_url:
        print(f"使用代理API: {args.proxy_url}")
    else:
        print("未配置代理API，将使用直连模式")

    for idx, token in enumerate(tokens, start=1):
        process_account(token, idx, args.num, args.proxy_url, args.delay)
        if idx < len(tokens):
            print(f"\n等待 5 秒后处理下一个账号...")
            time.sleep(5)

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