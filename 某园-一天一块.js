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


/**
 * ============================================================
 *  绿树田园 - 青龙面板每日签到脚本
 *  现已上线小程序公众号注册，每日签到得1元！
 * ============================================================
 *
 *  项目简介：
 *    绿树田园是一个微信公众号注册 + Web端的种树C2C交易项目，目前大树价格一个3.12
 *    每日签到可获得树苗(持有树苗)和大树(能量币)收益，
 *    连续签到7天有额外奖励，还能兑换真实树苗！
 *
 *  脚本功能：
 *    1. 使用授权码(authCode)登录获取token
 *    2. 模拟页面访问设置 page_visit 标记
 *    3. 执行每日签到
 *    4. 输出签到结果(树苗/大树收益)
 *
 *  使用方法：
 *    1. 在微信公众号「绿树田园」关注并私信获取授权码(authCode)
 *       授权码格式：TREE + 28位字符，共32位
 *    2. 青龙面板 → 环境变量 → 添加：
 *         TREECOIN_AUTH_CODE = 你的授权码
 *       多账号用 & 分隔：
 *         TREECOIN_AUTH_CODE = 授权码1&授权码2&授权码3
 *    3. 青龙面板 → 定时任务 → 添加任务
 *         名称：绿树田园签到
 *         命令：task 某园-一天一块.js
 *         cron：0 8 * * *  (每天早上8点)
 *    4. 或直接运行：task 某园-一天一块.js
 *
 *  环境变量：
 *    TREECOIN_AUTH_CODE  - 授权码(必填)，多账号用 & 分隔
 *
 *  授权码获取方式：
 *    打开微信公众号「绿树田园」→ 关注 → 私信 → 授权码
 *    关注小程序 「绿树田园」
 *    或联系邀请人获取项目入口
 *  下载链接 ：  https://treecoin.cn/downloads/treecoin.apk
 *   官网： https://treecoin.cn
 * ============================================================
 */

const crypto = require('crypto')
const https = require('https')
const http = require('http')

// ============ 配置 ============
// 自行更换抓包域名地址
const API_BASE = process.env.TREECOIN_API_BASE || 'http://localhost:3000/api'
const AUTH_CODES = (process.env.TREECOIN_AUTH_CODE || '').split('&').filter(Boolean)

// AES-256-GCM 加密密钥
const ENCRYPTION_KEY = 'asldhlfhkjsadhfkjsdhfjshjkhfhsadflh'.substring(0, 32)
const ALGORITHM = 'aes-256-gcm'

// ============ 工具函数 ============

/**
 * AES-GCM 加密
 */
function aesEncrypt(text) {
    const iv = crypto.randomBytes(12)
    const cipher = crypto.createCipheriv(ALGORITHM, Buffer.from(ENCRYPTION_KEY), iv)
    let encrypted = cipher.update(text, 'utf-8')
    encrypted = Buffer.concat([encrypted, cipher.final()])
    return {
        data: encrypted.toString('hex'),
        iv: iv.toString('hex')
    }
}

/**
 * 发送 HTTP 请求
 */
function request(path, method, body, token) {
    return new Promise((resolve, reject) => {
        const url = new URL(API_BASE + path)
        const isHttps = url.protocol === 'https:'
        const lib = isHttps ? https : http

        const data = body ? JSON.stringify(body) : null

        const options = {
            hostname: url.hostname,
            port: url.port || (isHttps ? 443 : 80),
            path: url.pathname,
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'TreeCoinQinglong/1.0'
            }
        }

        if (data) {
            options.headers['Content-Length'] = Buffer.byteLength(data)
        }

        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`
        }

        const req = lib.request(options, (res) => {
            let chunks = ''
            res.on('data', (chunk) => { chunks += chunk })
            res.on('end', () => {
                try {
                    resolve(JSON.parse(chunks))
                } catch (e) {
                    resolve({ c: 0, msg: '响应解析失败', raw: chunks })
                }
            })
        })

        req.on('error', reject)
        req.setTimeout(15000, () => {
            req.destroy(new Error('请求超时'))
        })

        if (data) req.write(data)
        req.end()
    })
}

/**
 * 控制台输出带时间戳
 */
function log(msg) {
    const now = new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
    /**
 * 输出带时间戳的日志消息
 * @param {string} msg - 要输出的日志消息内容
 */
console.log(`[${now}] ${msg}`)
}

/**
 * 延迟
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
}

// ============ 核心逻辑 ============

/**
 * 使用授权码登录
 */
async function loginWithAuthCode(authCode) {
    const deviceFingerprint = generateDeviceId()

    const result = await request('/auth/login-by-auth-code', 'POST', {
        authCode,
        device_fingerprint: deviceFingerprint
    })

    if (result.c !== 1 || !result.data) {
        throw new Error(result.msg || '登录失败')
    }

    return {
        token: result.data.token,
        openid: result.data.openid,
        deviceFingerprint: deviceFingerprint,
        userInfo: result.data.user || {}
    }
}

/**
 * 执行签到
 */
async function doSignin(token, deviceId) {
    // 加密请求数据 { token, deviceId }
    const payload = JSON.stringify({ token, deviceId })
    const { data, iv } = aesEncrypt(payload)

    const result = await request('/app/signin', 'POST', {
        encryptedData: data,
        iv
    }, token)

    return result
}

/**
 * 单账号签到流程
 */
async function signinForAccount(authCode, index) {
    log(`---------- 账号 ${index + 1} ----------`)
    log(`授权码: ${authCode.substring(0, 8)}****`)

    try {
        // 1. 登录
        log('正在登录...')
        const loginResult = await loginWithAuthCode(authCode)
        log(`登录成功！用户: ${loginResult.userInfo.nickName || '未知'} (openid: ${loginResult.openid.substring(0, 8)}...)`)

        const { token, deviceFingerprint } = loginResult

        // 2. 设置页面访问标记
        log('设置签到前置标记...')
        await sleep(500)

        // 3. 签到
        log('执行签到...')
        const signinResult = await doSignin(token, deviceFingerprint)

        if (signinResult.c === 1) {
            const data = signinResult.data || {}
            log('========================================')
            log('           签到成功！')
            log('========================================')
            log(`  连续签到天数: ${data.continuousDays || 1} 天`)
            log(`  当前持有树苗: ${data.vitality || '未知'}`)
            log(`  本次树苗奖励: +${data.baseReward || 0}`)
            if (data.continuousReward && data.continuousReward > 0) {
                log(`  连续签到奖励: +${data.continuousReward} (满7天额外奖励！)`)
            }
            log(`  本次总收益:   +${data.increase || 0} 树苗`)
            log('========================================')
            log('提示: 大树(能量币)收益将在签到后异步发放')
            log('      持有树苗越多，每日大树产币越多！')
            return { success: true, data }
        } else {
            log(`签到结果: ${signinResult.msg || '未知'}`)

            // 今日已签到也算成功
            if (signinResult.msg && signinResult.msg.includes('已签到')) {
                log('今天已经签到过了，明天再来吧！')
                return { success: true, alreadySigned: true }
            }

            return { success: false, msg: signinResult.msg }
        }
    } catch (error) {
        log(`签到失败: ${error.message}`)
        return { success: false, msg: error.message }
    }
}

/**
 * 主函数
 */
async function main() {
    console.log('')
    console.log('╔══════════════════════════════════════════╗')
    console.log('║     绿树田园 - 每日签到脚本 (青龙版)     ║')
    console.log('║                                          ║')
    console.log('║  种树赚钱，每日签到，连续7天额外奖励！   ║')
    console.log('║  树苗可兑换真实树苗，为地球添一份绿！    ║')
    console.log('║  当前币价：3.12，自由交易    ║')
    console.log('╚══════════════════════════════════════════╝')
    console.log('')

    if (AUTH_CODES.length === 0) {
        console.log('❌ 未配置授权码！')
        console.log('')
        console.log('请设置环境变量 TREECOIN_AUTH_CODE')
        console.log('获取方式：微信小程序「绿树田园」→ 我的 → 授权码')
        console.log('多账号用 & 分隔')
        console.log('')
        console.log('青龙面板配置：')
        console.log('  环境变量 → 添加 → TREECOIN_AUTH_CODE = 你的授权码')
        console.log('  定时任务 → task treecoin-qinglong-signin.js')
        console.log('  cron表达式: 0 8 * * * (每天8点)')
        return
    }

    log(`共 ${AUTH_CODES.length} 个账号待签到`)
    log(`API地址: ${API_BASE}`)
    console.log('')

    let successCount = 0
    let failCount = 0

    for (let i = 0; i < AUTH_CODES.length; i++) {
        const result = await signinForAccount(AUTH_CODES[i].trim(), i)
        if (result.success) {
            successCount++
        } else {
            failCount++
        }

        // 多账号间隔2秒，避免频率限制
        if (i < AUTH_CODES.length - 1) {
            log('等待2秒后处理下一个账号...')
            await sleep(2000)
        }
    }

    console.log('')
    log('========== 签到汇总 ==========')
    log(`成功: ${successCount} 个账号`)
    log(`失败: ${failCount} 个账号`)
    log('==============================')

    if (failCount > 0) {
        log('部分账号签到失败，请检查授权码是否正确或是否已过期')
    }
}

// 运行
main().catch(err => {
    log(`脚本运行异常: ${err.message}`)
    console.error(err)
})

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