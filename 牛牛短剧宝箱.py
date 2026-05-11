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
#  */3 * * * *  定时规则
import requests
import argparse
import time
import random
import os
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# ================= 提示信息 =================
def print_cron_tip():
    print("=" * 50)
    print("【定时运行提示】")
    print("建议设置 Cron 任务：运行")
    print("*/3 * * * *  ")
    print("=" * 50 + "\n")

# ================= 请求核心函数 =================
def make_request(name, method, url, headers, timeout=10):
    """请求函数：支持返回完整的响应内容以便打印"""
    try:
        if method.upper() == 'GET':
            resp = requests.get(url, headers=headers, timeout=timeout)
        else:
            resp = requests.post(url, headers=headers, timeout=timeout)
        
        # 尝试解析 JSON
        try:
            res_json = resp.json()
            return True, res_json
        except:
            return True, resp.text
            
    except Exception as e:
        return False, str(e)

def format_info(data):
    """从返回数据中提取关键结果信息"""
    if isinstance(data, dict):
        # 尝试寻找常见的提示字段
        msg = data.get('msg') or data.get('message') or ""
        info = data.get('data') or ""
        # 如果 data 是个字典，看看里面有没有积分之类的
        if isinstance(info, dict):
            # 展平字典内容
            info = ", ".join([f"{k}:{v}" for k, v in info.items()])
        
        result = f"{msg} | {info}".strip(" | ")
        return result if result else json.dumps(data, ensure_ascii=False)
    return str(data)

# ================= 业务接口 =================
def run_task(token, account_idx):
    headers = {
        "Host": "api.tianjinzhitongdaohe.com",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows",
        "xweb_xhr": "1",
        "Content-Type": "application/x-www-form-urlencoded",
        "token": token,
        "Accept": "*/*",
        "Referer": "https://servicewechat.com/wxcb95401f250e9a53/19/page-frame.html",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }

    base_url = "https://api.tianjinzhitongdaohe.com/sqx_fast/app"
    tasks = [
        ("用户计时", f"{base_url}/integral/userTimer"),
        ("积分查询", f"{base_url}/integral/selectByUserId"),
        ("消息统计", f"{base_url}/message/selectMessageCount")
    ]

    print(f"🚀 [账号 {account_idx}] 开始执行任务...")
    all_success = True
    summary_results = []
    
    for name, url in tasks:
        success, response_data = make_request(name, 'GET', url, headers)
        if success:
            detail = format_info(response_data)
            print(f" ✅ [账号 {account_idx}] {name}: {detail}")
            summary_results.append(f"{name}:成功")
        else:
            print(f" ❌ [账号 {account_idx}] {name}: 请求失败 ({response_data})")
            summary_results.append(f"{name}:失败")
            all_success = False
        
        # 接口间随机延迟，模拟真人操作
        time.sleep(random.uniform(1.5, 3.0))

    return all_success, account_idx

# ================= 主程序 =================
def main():
    print_cron_tip()

    parser = argparse.ArgumentParser(description="多账号金币领取脚本（增强版）")
    parser.add_argument("-c", "--concurrent", type=int, default=3, help="并发数量")
    parser.add_argument("-t", "--token", type=str, help="单个token")
    parser.add_argument("-f", "--file", type=str, help="token文件路径")
    args = parser.parse_args()

    # 1. 获取 Tokens
    tokens = []
    if args.token:
        tokens.append(args.token)
    elif args.file and os.path.exists(args.file):
        with open(args.file, 'r', encoding='utf-8') as f:
            tokens = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    else:
        env_tokens = os.getenv("niuniuTOKENS", "")
        if env_tokens:
            tokens = [t.strip() for t in env_tokens.split('\n') if t.strip()]

    if not tokens:
        print("【错误】未找到有效 Token！请通过环境变量 niuniuTOKENS 或参数提供。")
        sys.exit(1)

    print(f"--- 已加载 {len(tokens)} 个账号，并发数: {args.concurrent} ---\n")

    # 2. 执行并发任务
    success_count = 0
    failed_indices = []

    with ThreadPoolExecutor(max_workers=args.concurrent) as executor:
        future_to_idx = {executor.submit(run_task, token, i): i for i, token in enumerate(tokens, 1)}
        
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                success, account_idx = future.result()
                if success:
                    success_count += 1
                else:
                    failed_indices.append(account_idx)
            except Exception as e:
                print(f"❗ [账号 {idx}] 运行期间发生崩溃: {e}")
                failed_indices.append(idx)

    # 3. 最终汇总打印
    print("\n" + "=" * 50)
    print("【任务执行汇总】")
    print(f"总计账号 : {len(tokens)}")
    print(f"成功完成 : {success_count}")
    if failed_indices:
        failed_indices.sort()
        print(f"失败账号 : {', '.join(map(str, failed_indices))} (请检查Token是否过期)")
    else:
        print(f"失败账号 : 无")
    print("=" * 50)

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