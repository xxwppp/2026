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
"""
善M/YSKJ 每日签到脚本，适配青龙面板。

推荐环境变量：
  SHANM_TOKEN       Token；多账号用换行、& 或 | 分隔
  SHANM_WX_CODE     首次登录使用的一次性微信 code
  SHANM_DEVICE_ID   首次登录时的 device_id
  SHANM_INVITE_CODE 首次登录时的邀请码，可选
  定时任务：0 0 8,14,19 * * *

例如：
  SHANM_TOKEN=token1&token2

说明：微信 code 不能由普通 Python 脚本自动获取，首次登录后请把响应中的
    token 填入 SHANM_TOKEN 环境变量中，后续即可使用 token 直接签到。
    暂时不知道token的有效期，若出现鉴权失败请重新登录获取token。
"""

import json
import hashlib
import os
import random
import sys
from typing import Any, Dict, List

try:
    import requests
except ImportError:
    print("缺少 requests 依赖，请在青龙容器中执行: pip3 install requests")
    sys.exit(1)


BASE_URL = "https://net.todaypayforyou.fun/YSKJ/api"
REFERER = "https://servicewechat.com/wxc59eee06736849e8/3/page-frame.html"
UA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".shanm_ua.json")
ANDROID_VERSIONS = ["12", "13", "14"]
PHONE_MODELS = ["M2012K10C", "M2101K9C", "V2183A", "PGT-AN00", "SM-G9860"]
BUILD_IDS = ["TP1A.220624.014", "SP1A.210812.016", "UP1A.231005.007"]
CHROME_VERSIONS = [
    "140.0.7339.80", "142.0.7444.175", "144.0.7559.132",
    "146.0.7680.178",
]


def generate_ua() -> str:
    """生成与抓包中一致格式的安卓微信小程序 WebView UA。"""
    return (
        "Mozilla/5.0 (Linux; Android %s; %s Build/%s; wv) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
        "Chrome/%s Mobile Safari/537.36 "
        "MicroMessenger/8.0.76.3140 WeChat/arm64 "
        "MiniProgramEnv/android"
        % (
            random.choice(ANDROID_VERSIONS),
            random.choice(PHONE_MODELS),
            random.choice(BUILD_IDS),
            random.choice(CHROME_VERSIONS),
        )
    )


def account_ua(account_key: str) -> str:
    """按账号读取或创建固定 UA，文件损坏时自动重建。"""
    try:
        with open(UA_FILE, "r", encoding="utf-8") as handle:
            values = json.load(handle)
        if isinstance(values, dict) and values.get(account_key):
            return str(values[account_key])
    except (OSError, ValueError, TypeError):
        values = {}

    if not isinstance(values, dict):
        values = {}
    values[account_key] = generate_ua()
    try:
        with open(UA_FILE, "w", encoding="utf-8") as handle:
            json.dump(values, handle, ensure_ascii=False, indent=2)
    except OSError as exc:
        print("UA 持久化失败，将继续使用本次生成值: %s" % exc)
    return values[account_key]


def notify(title: str, content: str) -> None:
    """兼容青龙 notify.py；没有通知模块时只输出日志。"""
    try:
        from notify import send  # type: ignore
        send(title, content)
    except Exception as exc:
        print("通知发送失败: %s" % exc)


def split_accounts(value: str) -> List[str]:
    return [item.strip() for item in value.replace("&", "\n").replace("|", "\n").splitlines() if item.strip()]


def safe_json(response: requests.Response) -> Dict[str, Any]:
    try:
        value = response.json()
    except ValueError:
        raise RuntimeError("HTTP %s，响应不是 JSON: %s" % (response.status_code, response.text[:200]))
    if not isinstance(value, dict):
        raise RuntimeError("接口返回格式异常: %s" % type(value).__name__)
    return value


class ShanmApi:
    def __init__(self, token: str = "", account_key: str = "") -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": account_ua(account_key),
            "Referer": REFERER,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        self.token = token.strip()
        if self.token:
            self.session.headers["X-Token"] = self.token

    def request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        response = self.session.request(
            method, BASE_URL + path, timeout=(10, 20), **kwargs
        )
        if response.status_code in (401, 403):
            raise RuntimeError("鉴权失败，Token 可能已过期或已失效 (HTTP %s)" % response.status_code)
        response.raise_for_status()
        body = safe_json(response)
        if body.get("code") not in (None, 200):
            raise RuntimeError("接口失败: %s" % body.get("msg", body))
        return body

    def login(self, wx_code: str, device_id: str, invite_code: str = "") -> str:
        body = self.request("POST", "/user/login_wx", json={
            "code": wx_code,
            "device_id": device_id,
            "invite_code": invite_code,
            "nickname": "",
            "avatar": "",
        })
        token = str((body.get("data") or {}).get("token") or "")
        if not token:
            raise RuntimeError("登录响应中没有 token")
        self.token = token
        self.session.headers["X-Token"] = token
        return token

    def profile(self) -> Dict[str, Any]:
        return self.request("GET", "/user/profile").get("data") or {}

    def sign_status(self) -> Dict[str, Any]:
        return self.request("GET", "/sign/status").get("data") or {}

    def checkin(self) -> Dict[str, Any]:
        return self.request("POST", "/sign/checkin", json={}).get("data") or {}


def run_account(index: int, token: str) -> str:
    # Token 只做 SHA-256 指纹，不把真实凭证写入 UA 配置文件。
    account_key = "account-%d" % index
    if token.strip():
        account_key = "token-" + hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
    api = ShanmApi(token, account_key)
    wx_code = os.getenv("SHANM_WX_CODE", "").strip()
    if not api.token and wx_code:
        device_id = os.getenv("SHANM_DEVICE_ID", "").strip()
        if not device_id:
            raise RuntimeError("使用 SHANM_WX_CODE 时必须同时设置 SHANM_DEVICE_ID")
        api.login(wx_code, device_id, os.getenv("SHANM_INVITE_CODE", "").strip())

    if not api.token:
        raise RuntimeError("未配置 SHANM_TOKEN；微信 code 不能由脚本自动获取")

    profile = api.profile()
    name = str(profile.get("nickname") or "账号%d" % index)
    status = api.sign_status()
    if not status.get("can_checkin"):
        current = status.get("current_session") or "当前时段"
        return "%s：无需签到（%s 已签到或不在签到时段）" % (name, current)

    result = api.checkin()
    session = result.get("session", "未知时段")
    points = result.get("points_earned", "?")
    balance = result.get("points_balance", "?")
    return "%s：签到成功，时段=%s，获得积分=%s，积分余额=%s" % (
        name, session, points, balance
    )


def main() -> None:
    tokens = split_accounts(os.getenv("SHANM_TOKEN", ""))
    # 允许只配置一次性 code 进行首次登录；登录成功后应改用 SHANM_TOKEN。
    if not tokens and os.getenv("SHANM_WX_CODE", "").strip():
        tokens = [""]

    if not tokens:
        raise RuntimeError("请配置青龙环境变量 SHANM_TOKEN")

    results: List[str] = []
    for index, token in enumerate(tokens, 1):
        try:
            results.append(run_account(index, token))
        except Exception as exc:
            results.append("账号%d：失败，%s" % (index, exc))

    message = "\n".join(results)
    print(message)
    notify("善M签到", message)
    if any("失败" in item for item in results):
        sys.exit(1)


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