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
import os
import random
import time

# 青龙面板环境变量配置
# 环境变量名: 轻享多利账号，格式：账号#密码，多账号用&分隔
# 示例：QINGXIANGDUOLI_ACCOUNTS="账号1#密码1&账号2#密码2"
accounts_env = os.getenv("QINGXIANGDUOLI_ACCOUNTS", "")

# 请求的URL
login_url = "https://qingxianggf.jndz.asia/index.php/appapi/login"
signin_url = "https://qingxianggf.jndz.asia/index.php/appapi/signIn"
signin_status_url = "https://qingxianggf.jndz.asia/index.php/appapi/signInStatus"

# 模拟UA列表
USER_AGENTS = [
    "Dalvik/2.1.0 (Linux; U; Android 9; PJJ110 Build/PQ3A.190705.05211459)",
    "Dalvik/2.1.0 (Linux; U; Android 10; SM-G975F Build/QP1A.190711.020)",
    "Dalvik/2.1.0 (Linux; U; Android 11; Pixel 5 Build/RQ3A.210605.005)",
    "Dalvik/2.1.0 (Linux; U; Android 12; SM-S908B Build/SP1A.210812.016)",
    "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 7 Build/TD1A.220804.031)",
]


def get_random_ua():
    """获取随机UA"""
    return random.choice(USER_AGENTS)


def login(account, password, session):
    """登录并获取token"""
    payload = {
        "password": password,
        "version": "1.4",
        "account": account
    }

    headers = {
        "User-Agent": get_random_ua(),
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json"
    }

    print(f"正在登录账号: {account}")
    response = session.post(login_url, data=payload, headers=headers)

    try:
        result = response.json()

        # 尝试从不同可能的字段名中获取token
        token = None
        if 'data' in result and isinstance(result['data'], dict):
            token = result['data'].get('token') or result['data'].get('access_token') or result['data'].get(
                'user_token')

        if not token:
            token = result.get('token') or result.get('access_token') or result.get('user_token')

        if token:
            print(f"✓ 登录成功")
            return token
        else:
            print(f"✗ 登录失败: 未能获取token")
            print(f"响应信息: {result.get('message', result.get('msg', '未知错误'))}")
            return None

    except Exception as e:
        print(f" 登录异常: {e}")
        return None


def signin(token, session):
    """执行签到"""
    headers = {
        "User-Agent": get_random_ua(),
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    print("正在签到...")
    response = session.post(signin_url, headers=headers)

    try:
        result = response.json()
        if result.get('code') == 200 or result.get('code') == 0 or result.get('status') == 1 or result.get('success'):
            print("✓ 签到成功")
            return True
        else:
            print(f"✗ 签到失败: {result.get('message', result.get('msg', '未知错误'))}")
            return False
    except Exception as e:
        print(f"✗ 签到异常: {e}")
        return False


def get_signin_status(token, session):
    """查询签到状态"""
    headers = {
        "User-Agent": get_random_ua(),
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    print("正在查询签到状态...")
    response = session.post(signin_status_url, headers=headers)

    try:
        result = response.json()
        if result.get('code') == 0 or result.get('code') == 200:
            data = result.get('data', {})
            print("\n========== 签到总结 ==========")
            print(f"签到日期: {data.get('sign_date', '未知')}")
            print(f"本次奖励: {data.get('reward', 0)} 平台币")
            print(f"平台币总额: {data.get('platform_coin', 0)}")
            print(f"USDT余额: {data.get('usdt_balance', 0)}")
            print("==============================\n")
            return True
        else:
            print(f"✗ 查询失败: {result.get('message', '未知错误')}")
            return False
    except Exception as e:
        print(f"✗ 查询异常: {e}")
        return False


def process_account(account_info, session):
    """处理单个账号的登录、签到和查询"""
    if '#' not in account_info:
        print(f"✗ 账号格式错误: {account_info} (应为: 账号#密码)")
        return

    account, password = account_info.split('#', 1)
    account = account.strip()
    password = password.strip()

    print(f"\n{'=' * 50}")
    print(f"开始处理账号: {account}")
    print(f"{'=' * 50}")

    # 登录
    token = login(account, password, session)
    if not token:
        return

    # 签到
    signin_success = signin(token, session)

    # 查询签到状态
    if signin_success:
        time.sleep(1)  # 延迟1秒避免请求过快
        get_signin_status(token, session)


def main():
    """主函数"""
    print("=" * 50)
    print("轻享多利自动签到脚本")
    print("=" * 50)

    # 检查环境变量
    if not accounts_env:
        print("✗ 未找到环境变量 QINGXIANGDUOLI_ACCOUNTS")
        print("请在青龙面板环境变量中添加:")
        print("变量名: QINGXIANGDUOLI_ACCOUNTS")
        print("变量值: 账号#密码 (多账号用&分隔)")
        print("示例: 2453508538#2453508538&123456#123456")
        return

    # 解析账号列表
    accounts_list = [acc.strip() for acc in accounts_env.split('&') if acc.strip()]

    if not accounts_list:
        print("✗ 环境变量格式错误，未解析到有效账号")
        return

    print(f"\n共找到 {len(accounts_list)} 个账号")
    print(f"开始执行签到任务...\n")

    # 创建session保持连接
    session = requests.Session()

    # 处理每个账号
    for i, account_info in enumerate(accounts_list, 1):
        print(f"\n>>> 处理第 {i}/{len(accounts_list)} 个账号")
        process_account(account_info, session)

        # 多个账号之间延迟，避免请求过快
        if i < len(accounts_list):
            delay = random.randint(2, 5)
            print(f"等待 {delay} 秒后处理下一个账号...")
            time.sleep(delay)

    print("\n" + "=" * 50)
    print("所有账号处理完成")
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