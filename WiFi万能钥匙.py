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

# ======================================
#           【配置区｜直接在这里改】
# ======================================
wifitoken = ""
COIN_CATEGORY = 3          # 金刚位分类 1/2/3
COIN_MODE = "kingkong"     # kingkong / downPlay / taskReport / both / all
COIN_COUNT = 0            # 执行次数 0=无限循环
COIN_INTERVAL_MS = 2000    # 每次间隔毫秒
COIN_PROJECT_CODE = "wifi"
COIN_APP_ID = "wifi"
COIN_UID = "5550fc8e1b0d4ebaa8a0688e6b25d7bc"
COIN_TASK_ID = 0
COIN_HOST = "https://coin-api.y5coin.com/coin"
COIN_DEBUG = False
COIN_SKIP_CREDIT = False
COIN_DRY_RUN = False
# 设备参数
verCode = "395"
verName = "6.25.0"
channelId = "0"
platform = "android"
model = "Pixel 6"
manuf = "Google"
osVerCode = "33"
net = "WIFI"
adSdkType = "csj"
ecpm = 120
pkgName = "com.ss.android.ugc.aweme"
appName = "抖音"
backType = 1
businessType = 1
step = 1
# ======================================

import requests
import json
import time
import base64
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

AES_KEY_PROD = b'W98$9@F9@NlJ6oIwIylrjR2JP8JNa5wt'
AES_KEY_PRE = b'W98$9@F9@NlJ6oIwIylrjR2JP8JNa5li'
AES_IV = b'iijbSYXWrsjQksaS'
SDK_VERSION = '1.3.6'
SDK_VER_CODE = '202607021633'

def now_ts():
    return int(time.time() * 1000)

def aes_encrypt(plain_obj, use_pre=False):
    plain = json.dumps(plain_obj, ensure_ascii=False) if isinstance(plain_obj, dict) else str(plain_obj)
    key = AES_KEY_PRE if use_pre else AES_KEY_PROD
    cipher = AES.new(key, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(plain.encode("utf-8"), AES.block_size))

def aes_decrypt(buf:bytes, use_pre=False):
    key = AES_KEY_PRE if use_pre else AES_KEY_PROD
    cipher = AES.new(key, AES.MODE_CBC, AES_IV)
    raw = unpad(cipher.decrypt(buf), AES.block_size).decode("utf-8")
    return raw

def parse_jwt_payload(token:str):
    try:
        t = token.replace("Bearer ","").strip()
        parts = t.split(".")
        if len(parts)<2:
            return {}
        b64 = parts[1].replace("-","+").replace("_","/")
        b64 += "=" * ((4 - len(b64)%4)%4)
        data = base64.b64decode(b64)
        return json.loads(data)
    except:
        return {}

def log_print(level, msg):
    t = datetime.now().strftime("%H:%M:%S")
    prefix = ""
    if level == "error":
        prefix = "【错误】"
    elif level == "warn":
        prefix = "【警告】"
    print(f"[{t}] {prefix}{msg}")

def http_post_binary(url, headers, body_bytes, timeout=20):
    safe_header = {}
    for k, v in headers.items():
        try:
            v_str = str(v)
            v_str.encode("latin-1")
            safe_header[str(k)] = v_str
        except UnicodeEncodeError:
            continue
    resp = requests.post(url, headers=safe_header, data=body_bytes, timeout=timeout)
    return {"status":resp.status_code, "body":resp.content, "headers":dict(resp.headers)}

def sleep_ms(ms):
    time.sleep(ms / 1000)

def build_common(jwt_claims:dict):
    def pick(*keys):
        for k in keys:
            if jwt_claims.get(k) not in (None,""):
                return str(jwt_claims[k])
        return ""
    return {
        "projectCode":COIN_PROJECT_CODE,
        "appId":COIN_APP_ID,
        "verCode":verCode,
        "verName":verName,
        "channelId":channelId,
        "uid":COIN_UID if COIN_UID else pick("uid","sub","userId"),
        "dhid":"",
        "deviceId":"",
        "aid":"",
        "model":model,
        "manuf":manuf,
        "osVerCode":osVerCode,
        "sim_operator":"",
        "net":net,
        "oaid":"",
        "bootId":"",
        "sdkVersion":SDK_VERSION,
        "sdkVerCode":SDK_VER_CODE,
        "timestamp":now_ts(),
        "clientTaichis":"",
        "platform":platform
    }

class CoinClient:
    def __init__(self, token):
        self.host = COIN_HOST.rstrip("/")
        self.token = token.replace("Bearer ","").strip()
        self.jwt_claims = parse_jwt_payload(self.token)
        self.use_pre = "coin-api-pre" in self.host

    def headers(self):
        h = {
            "x-project-code":COIN_PROJECT_CODE,
            "x-sdk-version":SDK_VER_CODE,
            "x-platform":platform,
            "Content-Type":"application/json; charset=utf-8"
        }
        if self.token:
            h["x-http-jwt-token"] = f"Bearer {self.token}"
        return h

    async def api(self, path, biz_params:dict):
        common = build_common(self.jwt_claims)
        payload = {"common":common,**biz_params}
        enc_body = aes_encrypt(payload, self.use_pre)
        full_url = f"{self.host}{path}"
        if COIN_DRY_RUN:
            log_print("info",f"模拟请求:{path}")
            return {"dryRun":True}
        res = http_post_binary(full_url,self.headers(),enc_body)
        if res["status"] != 200:
            log_print("warn",f"http状态码 {res['status']}")
            return {"json":{"code":-112,"msg":"http error"}}
        try:
            raw_text = aes_decrypt(res["body"],self.use_pre)
            json_data = json.loads(raw_text)
            return {"json":json_data}
        except Exception as e:
            log_print("error",f"解密失败 {e}")
            return {"json":{"code":-110,"msg":"decode fail"}}

    async def credit(self):
        return await self.api("/user/credit",{})

    async def kingkongExtraAdReport(self):
        body = {
            "category":COIN_CATEGORY,
            "ecpm":ecpm,
            "adSdkType":adSdkType,
            "pkgName":pkgName,
            "appName":appName
        }
        return await self.api("/task/kingkongExtraAdReport",body)

    async def downPlayComplete(self,taskid):
        body = {
            "taskId":taskid,
            "backType":backType,
            "businessType":businessType,
            "pkgName":pkgName,
            "appName":appName,
            "adSdkType":adSdkType,
            "ecpm":ecpm
        }
        return await self.api("/task/downPlayComplete",body)

    async def taskReport(self,taskid):
        body = {
            "taskId":taskid,
            "step":step,
            "adSdkType":adSdkType,
            "ecpm":ecpm
        }
        return await self.api("/task/taskReport",body)

async def main():
    import asyncio
    token_list = [t.strip() for t in wifitoken.split("&") if t.strip()]
    if len(token_list) ==0:
        log_print("error","请填写 wifitoken！")
        return
    for idx,tk in enumerate(token_list):
        print(f"\n=====账号 {idx+1}/{len(token_list)}=====")
        client = CoinClient(tk)
        if not COIN_SKIP_CREDIT and not COIN_DRY_RUN:
            bal = await client.credit()
            if bal.get("json") and bal["json"].get("data"):
                coin = bal["json"]["data"]["item"].get("coinBalance","未知")
                print(f"当前余额：{coin} 金币")
        i = 0
        while True:
            i +=1
            log_print("info",f"第{i}轮开始执行")
            try:
                if COIN_MODE in ["kingkong","both","all"]:
                    ret = await client.kingkongExtraAdReport()
                    if ret.get("dryRun"):
                        print(f"第{i}轮 kingkong 模拟上报成功")
                    else:
                        j = ret["json"]
                        if j.get("code") ==0:
                            reward = j.get("data",{}).get("item",{}).get("rewards",0)
                            print(f"✅第{i}轮 kingkong成功，+{reward}金币")
                        else:
                            print(f"❌第{i}轮 kingkong失败 code:{j.get('code')} msg:{j.get('msg')}")
                if COIN_MODE in ["downPlay","both","all"]:
                    tid = COIN_TASK_ID
                    ret = await client.downPlayComplete(tid)
                    j = ret["json"]
                    if j.get("code") ==0:
                        reward = j.get("data",{}).get("item",{}).get("rewards",0)
                        print(f"✅第{i}轮 downPlay成功，+{reward}金币")
                    else:
                        print(f"❌第{i}轮 downPlay失败 code:{j.get('code')}")
                if COIN_MODE in ["taskReport","both","all"]:
                    tid = COIN_TASK_ID
                    ret = await client.taskReport(tid)
                    j = ret["json"]
                    if j.get("code") ==0:
                        reward = j.get("data",{}).get("item",{}).get("rewards",0)
                        print(f"✅第{i}轮 taskReport成功，+{reward}金币")
                    else:
                        print(f"❌第{i}轮 taskReport失败 code:{j.get('code')}")
            except Exception as e:
                log_print("error",f"第{i}轮异常：{str(e)}")
            if COIN_COUNT>0 and i >= COIN_COUNT:
                break
            sleep_ms(COIN_INTERVAL_MS)
    print("\n====全部任务执行结束====")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


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