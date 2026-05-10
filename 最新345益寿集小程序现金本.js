// 当前脚本来自于 http://script.345yun.cn 脚本库下载！
// 当前脚本来自于 http://2.345yun.cn 脚本库下载！
// 当前脚本来自于 http://2.345yun.cc 脚本库下载！
// 脚本库官方QQ群1群: 429274456
// 脚本库官方QQ群2群: 1077801222
// 脚本库官方QQ群3群: 433030897
// 脚本库中的所有脚本文件均来自热心网友上传和互联网收集。
// 脚本库仅提供文件上传和下载服务，不提供脚本文件的审核。
// 您在使用脚本库下载的脚本时自行检查判断风险。
// 所涉及到的 账号安全、数据泄露、设备故障、软件违规封禁、财产损失等问题及法律风险，与脚本库无关！均由开发者、上传者、使用者自行承担。

//到小程序底部 我的 → 提现 进行抓包！
//或者小程序底部 赚钱 进行抓包！
//抓小程序wxashopapi.heliang.cc
//请求中的stoken x-web-id x-cdn-relay-etag这三个值
//请创建环境变量名称: kyh
//环境变量值格式: 备注&stoken&x-web-id&x-cdn-relay-etag
//变量值使用&拼接 多账号使用@隔开或换行
//支持以下小程序:
//康养汇
//省心购
//益寿集
//康乐坊
//省乐拼甄选
//雅梦精选
//知秋惠选
//康养汇良品
//桑榆集市
//六六顺选
//胡同优选
//康选商城
//康宁堂
//九九严选
//夕阳红购
//八八质选
//安龄好物
//康养汇质选
//二三良作良选
//闲庭集市
//金龄优品
//康养汇慧购
//安心买
//暖心市集
//岁悦良品
//辉悦良品
//康养汇优购

class Env {
  constructor(name) {
    this.name = name;
  }

  log(...args) {
    console.log(...args);
  }

  async post(options) {
    const { url, body, headers } = options;
    const response = await fetch(url, {
      method: 'POST',
      headers: headers,
      body: body,
    });
    const responseText = await response.text();
    return { body: responseText, status: response.status };
  }

  done() {
    console.log('任务结束');
  }
}

const $ = new Env("福利中心提现任务");
console.log("🔗 更多脚本资源：https://2.345yun.cn");
const kyh = process.env.kyh;

if (!kyh) {
    $.log("❌ 请设置环境变量 kyh");
    $.log("格式：备注&stoken&x-web-id&x-cdn-relay-etag （多账号用@或换行分隔）");
    process.exit(0);
}


const lines = kyh.split(/\r?\n/).filter(line => line.trim() !== '');
let accountStrings = [];
lines.forEach(line => {
    accountStrings.push(...line.split('@').filter(Boolean));
});

const accounts = accountStrings.map(accStr => {
    const parts = accStr.split('&');
    if (parts.length === 4) {
        return {
            remark: parts[0],
            stoken: parts[1],
            xWebId: parts[2],
            xCdnRelayEtag: parts[3]
        };
    }

    if (parts.length === 3) {
        return {
            remark: '未知备注',
            stoken: parts[0],
            xWebId: parts[1],
            xCdnRelayEtag: parts[2]
        };
    }
    return null;
}).filter(Boolean);

if (accounts.length === 0) {
    $.log("❌ 没有有效的账号配置");
    process.exit(0);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function getRandomDelay() {
    return Math.floor(Math.random() * 15000) + 30000;
}

const APPID_MAP = {
    "wx0d2e210f1d434209": "康养汇",
    "wxa2df7b857150d2c5": "省心购",
    "wx253b08ac367c0899": "益寿集",
    "wxabbf498691473ebe": "康乐坊",
    "wx82736291ea03fd55": "省乐拼甄选",
    "wxa3cd42389b902f7b": "雅梦精选",
    "wx179c621b90c5c38c": "知秋惠选",
    "wx380d3cb5e63efd9d": "康养汇良品",
    "wxb2723191ba256104": "桑榆集市",
    "wxc592c174c95a6ea1": "六六顺选",
    "wxae694777f03cd5e9": "胡同优选",
    "wx25cdd44834385f86": "康选商城",
    "wxe80678a60dfe3838": "康宁堂",
    "wxf4aa8fdd02222364": "九九严选",
    "wx1e7323dce5cb821a": "夕阳红购",
    "wxdb81d5d2a0d721a1": "八八质选",
    "wxcae99c0c6fdde557": "安龄好物",
    "wx71574461895514ca": "康养汇质选",
    "wx4ebdc253ea240ecc": "二三良作良选",
    "wxba43b4907f729fa9": "闲庭集市",
    "wx643c90d115e82e66": "金龄优品",
    "wx991a604969e1efbc": "康养汇慧购",
    "wx492c0fa8bde204da": "安心买",
    "wx13606bc072bc29e9": "暖心市集",
    "wx90a4ea1ba0c92a4a": "岁悦良品",
    "wx7e98f4035bfd2eba": "辉悦良品",
    "wx7510d9e7c5aa3886": "康养汇优购"
};

const APPID_LIST = Object.keys(APPID_MAP);

function buildHeaders(account, now) {
    const appid = account.currentAppid || "wx253b08ac367c0899";
    return {
        'User-Agent': "Mozilla/5.0 (Linux; Android 15; 23013RK75C Build/AQ3A.250226.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/142.0.7444.173 Mobile Safari/537.36 XWEB/3330229 MMWEBSDK/20260101 MMWEBID/1813 MicroMessenger/8.0.69.3040(0x2800453F) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 MiniProgramEnv/android",
        'Accept': "application/json, text/plain, */*",
        'Content-Type': "application/json",
        'stoken': account.stoken,
        'x-web-id': account.xWebId,
        'x-cdn-relay-etag': account.xCdnRelayEtag,
        'pageurl': `pages/member/welfareCollect/index?from_appid=${appid}&$taroTimestamp=${now}`,
        'pageurl-pre': `pages/member/adEarnRecord/index?from=welfare&$taroTimestamp=${now}`,
        'version': "1.3.124",
        'mp-version': "3.14.2",
        'mp-platform': "weapp",
        'appid': appid,
        'self-invest': "",
        'scene': "1005",
        'charset': "utf-8",
        'referer': `https://servicewechat.com/${appid}/88/page-frame.html`
    };
}

async function withAppidFallback(account, taskFn, taskName) {
    let result;
    if (!account.failedAppids) {
        account.failedAppids = new Set();
    }
    const current = account.currentAppid || "wx253b08ac367c0899";
    const candidates = [current, ...APPID_LIST.filter(a => a !== current && !account.failedAppids.has(a))];

    for (const appid of candidates) {
        if (account.failedAppids.has(appid)) continue;
        account.currentAppid = appid;
        try {
            result = await taskFn();
        } catch (e) {
            $.log(`❌ ${taskName} 请求异常 (appid: ${appid}): ${e.message}`);
            result = null;
        }
        if (result && result.error_code === 700 && (result.msg || '').includes('不符')) {
            account.failedAppids.add(appid);
            $.log(`⚠️ AppID 不符，自动尝试中...`);
            continue;
        }
        return result;
    }
    $.log(`❌ ${taskName} 所有 AppID 尝试均失败`);
    return null;
}

async function getConfig(account) {
    const url = "https://wxashopapi.heliang.cc/wxa/WelfareCenter/config";
    const now = Date.now();
    const payload = { "$taro_timestamp": now };
    const headers = buildHeaders(account, now);
    const response = await $.post({ url, body: JSON.stringify(payload), headers });
    return JSON.parse(response.body || response);
}

async function doTask(account, taskType) {
    const url = "https://wxashopapi.heliang.cc/wxa/WelfareCenter/doTask";
    const now = Date.now();
    const payload = { "task": taskType };
    const headers = buildHeaders(account, now);
    const response = await $.post({ url, body: JSON.stringify(payload), headers });
    return JSON.parse(response.body || response);
}

async function doAttendTask(account) {
    return doTask(account, "attend");
}

async function doVideoTask(account) {
    return doTask(account, "video");
}

async function getAttendInfo(account) {
    const url = "https://wxashopapi.heliang.cc/wxa/WelfareCenter/getAttendInfo";
    const now = Date.now();
    const payload = { "task": "" };
    const headers = buildHeaders(account, now);
    const response = await $.post({ url, body: JSON.stringify(payload), headers });
    return JSON.parse(response.body || response);
}

async function getCashRecord(account) {
    const url = "https://wxashopapi.heliang.cc/wxa/welfareCenter/getCashRecord";
    const now = Date.now();
    const payload = { "pagesize": 12, "offset": 0, "from": "welfare", "$taro_timestamp": now };
    const headers = {
        ...buildHeaders(account, now),
        'pageurl': `pages/member/adEarnRecord/index?from=welfare&$taroTimestamp=${now}`,
        'pageurl-pre': `pages/member/welfareCollect/index?from_appid=${account.currentAppid}&$taroTimestamp=${now}`
    };
    const response = await $.post({ url, body: JSON.stringify(payload), headers });
    return JSON.parse(response.body || response);
}


function hasWithdrawnToday(cashRecordData) {
    if (!cashRecordData || cashRecordData.error_code !== 0 || !cashRecordData.data) return false;

    const d = new Date();
    const today = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

    const list = cashRecordData.data.list || [];
    if (list.length === 0) return false;
    const firstRecord = list[0];
    return firstRecord.exchange_time && firstRecord.exchange_time.startsWith(today);
}

async function addCashOutVideoLog(account) {
    const url = "https://wxashopapi.heliang.cc/wxa/welfareCenter/addCashOutVideoLog";
    const now = Date.now();
    const payload = { "action_str": "" };
    const headers = buildHeaders(account, now);
    const response = await $.post({ url, body: JSON.stringify(payload), headers });
    return JSON.parse(response.body || response);
}

async function addCashOut(account) {
    const url = "https://wxashopapi.heliang.cc/wxa/welfareCenter/addCashOut";
    const now = Date.now();
    const payload = { "cash_key": 1 };
    const headers = buildHeaders(account, now);
    const response = await $.post({ url, body: JSON.stringify(payload), headers });
    return JSON.parse(response.body || response);
}

async function handleAccount(account) {
    account.currentAppid = account.currentAppid || "wx253b08ac367c0899";
    account.failedAppids = new Set();

    $.log(`🚀 开始处理账号 [${account.remark}] ...`);

    
    $.log("📌 开始签到任务...");
    const attendRes = await withAppidFallback(account, () => doAttendTask(account), "签到");
    if (attendRes && attendRes.error_code === 0) {
        const appName = APPID_MAP[account.currentAppid] || account.currentAppid;
        $.log(`✅ 小程序: ${appName}→签到成功！`);

        const attendInfoRes = await withAppidFallback(account, () => getAttendInfo(account), "查询连续签到");
        if (attendInfoRes && attendInfoRes.error_code === 0 && attendInfoRes.data) {
            const afterStr = attendInfoRes.data.sub_title?.after;
            if (afterStr) {
                $.log(`✅ 小程序: ${appName}→${afterStr}`);
            }
        }
    } else {
        $.log("⚠️ 签到失败或已签到: " + JSON.stringify(attendRes));
    }

    const configRes = await withAppidFallback(account, () => getConfig(account), "获取配置");
    if (configRes && configRes.error_code === 0) {
        const data = configRes.data;
        $.log(`💰 当前账号金币数量：${data.coin}`);
        const videoTask = data.task.video;
        if (videoTask) {
            const subMsg = videoTask.sub_msg || '';
            if (subMsg.includes('12/12')) {
                $.log('📺 今日看视频任务已完成！');
            } else {
                const list = videoTask.list || [];
                const undoneCount = list.filter(item => item.status !== 1).length;
                if (undoneCount > 0) {
                    $.log(`📺 开始看视频任务，剩余${undoneCount}次`);
                    for (let i = 0; i < undoneCount; i++) {
                        $.log(`📹 执行第${i + 1}次视频任务`);
                        await sleep(3000);
                        const taskRes = await withAppidFallback(account, () => doVideoTask(account), "看视频任务");
                        if (taskRes && taskRes.error_code === 0) {
                            $.log(`✅ 看视频赚超多钱任务成功`);
                        } else {
                            $.log(`❌ 视频任务失败：${JSON.stringify(taskRes)}`);
                        }
                        await sleep(2000);
                    }
                } else {
                    $.log('📺 视频任务列表全部已完成，无需执行');
                }
            }
        } else {
            $.log('⚠️ 未找到视频任务配置');
        }
    } else {
        $.log('⚠️ 获取配置失败，跳过视频任务检查');
    }

    const cashRecordRes = await withAppidFallback(account, () => getCashRecord(account), "查询提现记录");
    if (hasWithdrawnToday(cashRecordRes)) {
        $.log("📅 今天已经提现过了！");
        const appName = APPID_MAP[account.currentAppid] || account.currentAppid;
        $.log(`📱 [${account.remark}]小程序: ${appName}`);
        $.log("🎉 任务完成！");
        return;
    }

    for (let i = 1; i <= 3; i++) {
        $.log(`📹 第${i}次观看广告视频...`);
        const videoLogRes = await withAppidFallback(account, () => addCashOutVideoLog(account), "观看广告视频");
        if (videoLogRes && videoLogRes.error_code === 0 && videoLogRes.msg === "success") {
            $.log("✅ 视频观看成功！");
        } else {
            $.log("❌ 视频观看失败！ - 数据: " + JSON.stringify(videoLogRes));
        }
        if (i < 3) {
            const delay = getRandomDelay();
            $.log(`⏳ 等待${Math.round(delay / 1000)}秒...`);
            await sleep(delay);
        }
    }

    const appName = APPID_MAP[account.currentAppid] || account.currentAppid;
    $.log(`📱 [${account.remark}]小程序: ${appName}`);
    $.log("🎉 该账号任务完成，请到小程序手动发起提现！");
}

(async () => {
    for (const account of accounts) {
        await handleAccount(account);
        $.log('-----------------------------------');
    }
    $.log('所有账号处理完毕');
    process.exit(0);
})();

// 当前脚本来自于 http://script.345yun.cn 脚本库下载！
// 当前脚本来自于 http://2.345yun.cn 脚本库下载！
// 当前脚本来自于 http://2.345yun.cc 脚本库下载！
// 脚本库官方QQ群1群: 429274456
// 脚本库官方QQ群2群: 1077801222
// 脚本库官方QQ群3群: 433030897
// 脚本库中的所有脚本文件均来自热心网友上传和互联网收集。
// 脚本库仅提供文件上传和下载服务，不提供脚本文件的审核。
// 您在使用脚本库下载的脚本时自行检查判断风险。
// 所涉及到的 账号安全、数据泄露、设备故障、软件违规封禁、财产损失等问题及法律风险，与脚本库无关！均由开发者、上传者、使用者自行承担。