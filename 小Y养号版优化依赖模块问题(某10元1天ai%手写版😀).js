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
 * 快手极速版自动化任务脚本
 * 用于自动完成观看广告、搜索等任务以获取金币奖励
 */

// 导入所需模块
const qs = require("querystring");
const axios = require("axios");
const querystring = require("querystring");
const { SocksProxyAgent } = require("socks-proxy-agent");
const { config } = require('dotenv');
const { log } = require("console");
config();

// 移动端品牌列表
const MOBILE_BRANDS = [
  { brand: "Xiaomi", models: ["Mi 10", "Mi 11", "Mi 12", "Mi 13", "Redmi Note 8", "Redmi Note 9", "Redmi Note 10", "Redmi Note 11", "Redmi Note 12", "POCO X3", "POCO X4", "POCO F3", "POCO F4"] },
  { brand: "Samsung", models: ["Galaxy S20", "Galaxy S21", "Galaxy S22", "Galaxy S23", "Galaxy Note 10", "Galaxy Note 20", "Galaxy A50", "Galaxy A51", "Galaxy A52", "Galaxy A53"] },
  { brand: "OPPO", models: ["Find X2", "Find X3", "Find X5", "Reno 4", "Reno 5", "Reno 6", "Reno 7", "A92s", "A93", "A94"] },
  { brand: "vivo", models: ["X50", "X60", "X70", "X80", "Y51", "Y52", "Y53", "Y70", "Y71", "Y72"] },
  { brand: "OnePlus", models: ["8", "8 Pro", "9", "9 Pro", "10", "10 Pro", "Nord", "Nord 2", "Nord 3"] },
  { brand: "Realme", models: ["GT", "GT Neo", "GT 2", "GT 2 Pro", "C15", "C17", "C19", "X7", "X7 Pro", "X9"] },
  { brand: "Huawei", models: ["P30", "P40", "P50", "Mate 30", "Mate 40", "Mate 50", "Nova 5", "Nova 6", "Nova 7", "Nova 8"] },
  { brand: "Honor", models: ["30", "30 Pro", "50", "50 Pro", "60", "60 Pro", "X10", "X20", "X30", "Magic3"] },
  { brand: "Google", models: ["Pixel 5", "Pixel 6", "Pixel 6 Pro", "Pixel 7", "Pixel 7 Pro", "Pixel 8", "Pixel 8 Pro"] },
  { brand: "ASUS", models: ["ROG Phone 3", "ROG Phone 5", "ROG Phone 6", "ZenFone 7", "ZenFone 8", "ZenFone 9"] },
  { brand: "Lenovo", models: ["Legion Phone Duel", "Legion Phone Duel 2", "Legion Phone Duel 3", "K12 Pro", "K13 Pro", "K14 Pro"] },
  { brand: "Nubia", models: ["Red Magic 5G", "Red Magic 6", "Red Magic 7", "Red Magic 8", "Z30 Pro", "Z40 Pro"] },
  { brand: "ZTE", models: ["Axon 20", "Axon 30", "Axon 40", "Blade V2020", "Blade V2021", "Blade V2022"] },
  { brand: "Meizu", models: ["17", "17 Pro", "18", "18 Pro", "18s", "18s Pro", "19", "19 Pro"] },
  { brand: "Black Shark", models: ["3", "3 Pro", "4", "4 Pro", "5", "5 Pro", "6", "6 Pro"] }
];

// 生成随机的Android版本
function generateAndroidVersion() {
  const versions = [10, 11, 12, 13, 14];
  return versions[Math.floor(Math.random() * versions.length)];
}

// 生成随机的Build版本
function generateBuildVersion(androidVersion) {
  const prefixes = {
    10: ["QKQ1", "QP1A"],
    11: ["RKQ1", "RQ3A"],
    12: ["SKQ1", "SP2A"],
    13: ["TP1A", "TS1A"],
    14: ["UP1A", "US1A"]
  };
  const prefix = prefixes[androidVersion][Math.floor(Math.random() * prefixes[androidVersion].length)];
  const year = Math.floor(Math.random() * 3) + 19;
  const month = String(Math.floor(Math.random() * 12) + 1).padStart(2, '0');
  const day = String(Math.floor(Math.random() * 28) + 1).padStart(2, '0');
  const suffix = String(Math.floor(Math.random() * 1000)).padStart(3, '0');
  return `${prefix}.${year}${month}${day}.${suffix}`;
}

// 生成随机的Chrome版本
function generateChromeVersion() {
  const major = Math.floor(Math.random() * 15) + 85;
  const minor = Math.floor(Math.random() * 1000);
  const build = Math.floor(Math.random() * 1000);
  const patch = Math.floor(Math.random() * 100);
  return `${major}.0.${minor}.${patch}`;
}

// 生成随机的快手App版本
function generateKwaiVersion() {
  const major = 13;
  const minor = Math.floor(Math.random() * 10) + 5;
  const patch = Math.floor(Math.random() * 50) + 20;
  const build = Math.floor(Math.random() * 10000) + 10000;
  return `${major}.${minor}.${patch}.${build}`;
}

// 生成随机的移动端UA
function generateRandomUA() {
  const brandInfo = MOBILE_BRANDS[Math.floor(Math.random() * MOBILE_BRANDS.length)];
  const brand = brandInfo.brand;
  const model = brandInfo.models[Math.floor(Math.random() * brandInfo.models.length)];
  const androidVersion = generateAndroidVersion();
  const buildVersion = generateBuildVersion(androidVersion);
  const chromeVersion = generateChromeVersion();
  const kwaiVersion = generateKwaiVersion();
  
  return `Mozilla/5.0 (Linux; Android ${androidVersion}; ${brand} ${model} Build/${buildVersion}; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/${chromeVersion} Mobile Safari/537.36 kwai-android/${kwaiVersion}`;
}

// 移动端UA管理池
const MOBILE_UA_POOL = Array.from({ length: 100 }, () => generateRandomUA());

// 定义颜色代码
const colors = {
  reset: "\x1b[0m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  magenta: "\x1b[35m",
  cyan: "\x1b[36m",
  white: "\x1b[37m",
  gray: "\x1b[90m",
  bold: "\x1b[1m",
  black: "\x1b[30m",
  lightBlue: "\x1b[36m" 
};

// 日志函数
function coloredLog(color, message) {
  console.log(`${color}${message}${colors.reset}`);
}

function red(message) { coloredLog(colors.red, message); }
function green(message) { coloredLog(colors.green, message); }
function yellow(message) { coloredLog(colors.yellow, message); }
function blue(message) { coloredLog(colors.blue, message); }
function magenta(message) { coloredLog(colors.magenta, message); }
function cyan(message) { coloredLog(colors.cyan, message); }
function gray(message) { coloredLog(colors.gray, message); }
function white(message) { coloredLog(colors.white, message); }
function black(message) { coloredLog(colors.black, message); }
function lightBlue(message) { coloredLog(colors.lightBlue, message); }

// 设置签名API地址
const KS_SIGN_API_URL = process.env.KS_SIGN_API_URL || "http://8.137.57.111:3888";

// 模拟下载配置
const ENABLE_APP_DOWNLOAD = process.env.ENABLE_APP_DOWNLOAD === 'true';
const APP_DOWNLOAD_PROBABILITY = parseInt(process.env.APP_DOWNLOAD_PROBABILITY) || 30;
console.log(colors.blue + `💡 模拟下载配置: 开启=${ENABLE_APP_DOWNLOAD}, 概率=${APP_DOWNLOAD_PROBABILITY}%` + colors.reset);

/**
 * 生成随机的用户行为消息
 */
function generateRandomInteractionMessage() {
  const messages = [
    "正在观看广告",
    "认真观看中...",
    "浏览广告内容",
    "模拟用户行为",
    "观看视频广告",
    "保持活跃状态",
    "广告浏览中",
    "正常观看时长",
  ];
  return messages[Math.floor(Math.random() * messages.length)];
}

/**
 * 生成热门搜索关键词
 */
function generateHotKeywords() {
  const keywords = [
    "短剧小说", "AI聊天", "电影", "电视剧", "综艺", "动漫", "游戏", "音乐", "新闻", "小说",
    "漫画", "教育", "娱乐", "财经", "科技", "健康", "生活", "旅游", "美食", "时尚",
    "游戏", "电影", "电视剧", "综艺"
  ];
  return keywords[Math.floor(Math.random() * keywords.length)];
}

/**
 * 从环境变量中获取数字类型的配置值
 */
function getEnvNumber(envKey, defaultValue) {
  const value = parseInt(process.env[envKey], 10);
  return isNaN(value) ? defaultValue : value;
}

// 从环境变量读取各项配置参数
const KSLOW_REWARD_THRESHOLD = getEnvNumber("KSLOW_REWARD_THRESHOLD", 200);
const KSROUNDS = getEnvNumber("KSROUNDS", 200);
const KSCOIN_LIMIT = getEnvNumber("KSCOIN_LIMIT", 150000);
const KSLOW_REWARD_LIMIT = getEnvNumber("KSLOW_REWARD_LIMIT", 1);
const KS_ONE_COIN_RETRY_LIMIT = getEnvNumber("KS_ONE_COIN_RETRY_LIMIT", 10);
const KS_RETRY_COUNT = getEnvNumber("KS_RETRY_COUNT", 3);
const KSFOLLOW_COUNT = getEnvNumber("KSFOLLOW_COUNT", 1);
const KSSEARCHFOLLOW_COUNT = getEnvNumber("KSSEARCHFOLLOW_COUNT", 100);
const KSLOOK_COUNT = getEnvNumber("KSLOOK_COUNT", 5);
const KSSEARCH_COUNT = getEnvNumber("KSSEARCH_COUNT", 5);
const KS_MIN_WAIT_TIME = getEnvNumber("KS_MIN_WAIT_TIME", 12000);
const KS_MAX_WAIT_TIME = getEnvNumber("KS_MAX_WAIT_TIME", 35000);
const KS_MIN_WATCH_TIME = getEnvNumber("KS_MIN_WATCH_TIME", 40000);
const KS_MAX_WATCH_TIME = getEnvNumber("KS_MAX_WATCH_TIME", 55000);

/**
 * 获取需要执行的任务列表
 */
function getTasksToExecute() {
  const taskEnv = process.env.Task;
  const validTasks = ["food", "box", "look", "search"];
  
  if (!taskEnv) {
    console.log(colors.yellow + "未设置Task环境变量，将执行所有任务 (food, box, look, search)" + colors.reset);
    return ["food", "box", "look", "search"];
  }

  const tasks = taskEnv.split(",").map(task => task.trim().toLowerCase()).filter(Boolean);
  const filteredTasks = tasks.filter(task => validTasks.includes(task));

  if (filteredTasks.length === 0) {
    console.log(colors.yellow + "Task环境变量中没有有效任务，将执行所有任务 (food, box, look, search)" + colors.reset);
    return ["food", "box", "look", "search"];
  }

  console.log(colors.green + "从Task环境变量中解析到要执行的任务: " + filteredTasks.join(", ") + colors.reset);
  return filteredTasks;
}

function getAccountConfigsFromEnv() {
  const configs = [];
  const seenConfigs = new Set();

  if (process.env.ksck) {
    const ksckValue = process.env.ksck;
    const configStrings = ksckValue.split("&").map(config => config.trim()).filter(Boolean);
    configs.push(...configStrings);
  }

  for (let i = 1; i <= 666; i++) {
    const ksckKey = `ksck${i}`;
    if (process.env[ksckKey]) {
      const ksckValue = process.env[ksckKey];
      const configStrings = ksckValue.split("&").map(config => config.trim()).filter(Boolean);
      configs.push(...configStrings);
    }
  }

  const uniqueConfigs = [];
  for (const config of configs) {
    if (!seenConfigs.has(config)) {
      seenConfigs.add(config);
      uniqueConfigs.push(config);
    }
  }

  console.log(colors.cyan + `从ksck及ksck1到ksck666环境变量中解析到 ${uniqueConfigs.length} 个唯一配置` + colors.reset);
  return uniqueConfigs;
}

const accountConfigs = getAccountConfigsFromEnv();
const accountCount = accountConfigs.length;
const tasksToExecute = getTasksToExecute();

// 清空download目录
function clearDownloadDir() {
  const fs = require('fs');
  const path = require('path');
  const downloadDir = path.join(__dirname, 'download');
  
  if (fs.existsSync(downloadDir)) {
    try {
      const files = fs.readdirSync(downloadDir);
      files.forEach(file => {
        const filePath = path.join(downloadDir, file);
        if (fs.statSync(filePath).isFile()) {
          fs.unlinkSync(filePath);
        }
      });
      console.log(colors.green + `✅ 清空download目录成功，删除了 ${files.length} 个文件` + colors.reset);
    } catch (error) {
      console.log(colors.red + `❌ 清空download目录失败: ${error.message}` + colors.reset);
    }
  }
}

clearDownloadDir();

// 输出配置信息
console.log(colors.gray + "================================================================================" + colors.reset);
console.log(colors.bold + colors.blue + "您可以根据需求设置以下环境变量来自定义任务行为：" + colors.reset);
console.log(colors.gray + "----------------------------------------------------------------" + colors.reset);
console.log(colors.bold + "账号/任务控制 (必填/常用):" + colors.reset);
console.log("  - ksck/ksckX: 账号信息 (cookie#salt#proxy) - 必填项");
console.log("  - Task: 指定任务 (如 food,box,look,search)");
console.log("  - KSROUNDS: 总执行轮数 (默认 200轮)");
console.log(colors.gray + "----------------------------------------------------------------" + colors.reset);
console.log(colors.bold + "频率/追加次数 (已支持自定义):" + colors.reset);
console.log("  - KSLOOK_COUNT: 每轮 look (主任务) 次数 (默认 5)");
console.log("  - KSFOLLOW_COUNT: 每次 look 成功后 follow (追加) 次数 (默认 1)");
console.log("  - KSSEARCH_COUNT: 每轮 search (主任务) 次数 (默认 5)");
console.log("  - KSSEARCHFOLLOW_COUNT: 每次 search 成功后 search_follow (追加) 次数 (默认 100)");
console.log(colors.gray + "----------------------------------------------------------------" + colors.reset);
console.log(colors.bold + "任务间隔等待时间设置 (毫秒):" + colors.reset);
console.log("  - KS_MIN_WAIT_TIME: 任务间隔最小等待时间 (默认 12000)");
console.log("  - KS_MAX_WAIT_TIME: 任务间隔最大等待时间 (默认 35000)");
console.log(colors.gray + "----------------------------------------------------------------" + colors.reset);
console.log(colors.bold + "广告观看时间设置 (毫秒):" + colors.reset);
console.log("  - KS_MIN_WATCH_TIME: 广告观看最小时间 (默认 30000)");
console.log("  - KS_MAX_WATCH_TIME: 广告观看最大时间 (默认 40000)");
console.log(colors.gray + "----------------------------------------------------------------" + colors.reset);
console.log(colors.bold + "风控/限制设置:" + colors.reset);
console.log("  - KSCOIN_LIMIT: 金币上限 (超过停止, 默认 150000)");
console.log("  - KSLOW_REWARD_LIMIT: 连续低奖励停止次数 (默认 1)");
console.log("  - KS_ONE_COIN_RETRY_LIMIT: 1金币奖励重试次数限制 (默认 10)");
console.log("  - MAX_CONCURRENCY: 最大并发账号数 (默认 3)");
console.log("  - KS_SIGN_API_URL: 签名服务 API 地址 (默认 http://47.102.101.227:18888)");
console.log(colors.gray + "================================================================" + colors.reset);

console.log(colors.magenta + "💎 检测到环境变量配置:" + colors.reset);
console.log(colors.lightBlue + `  账号数量: ${accountCount}个` + colors.reset);
console.log(colors.lightBlue + `  执行任务: ${tasksToExecute.join(", ")}` + colors.reset);

console.log(colors.magenta + "\n🎯 配置参数:" + colors.reset);
console.log(colors.lightBlue + `  轮数: ${KSROUNDS}` + colors.reset);
console.log(colors.lightBlue + `  look次数/轮: ${KSLOOK_COUNT}` + colors.reset);
console.log(colors.lightBlue + `  search次数/轮: ${KSSEARCH_COUNT}` + colors.reset);
console.log(colors.lightBlue + `  follow次数/look: ${KSFOLLOW_COUNT}` + colors.reset);
console.log(colors.lightBlue + `  search_follow次数/search: ${KSSEARCHFOLLOW_COUNT}` + colors.reset);
console.log(colors.lightBlue + `  金币上限: ${KSCOIN_LIMIT}` + colors.reset);
console.log(colors.lightBlue + `  低奖励阈值: ${KSLOW_REWARD_THRESHOLD}` + colors.reset);
console.log(colors.lightBlue + `  连续低奖励上限: ${KSLOW_REWARD_LIMIT}` + colors.reset);

const maxConcurrency = getEnvNumber("MAX_CONCURRENCY", 3);

console.log(colors.blue + "\n⚙️ 执行配置:" + colors.reset);
console.log(colors.lightBlue + `  防黑并发: ${maxConcurrency}` + colors.reset);
console.log(colors.lightBlue + `  防黑轮数: ${KSROUNDS}` + colors.reset);
console.log(colors.lightBlue + `  look次数/轮: ${KSLOOK_COUNT}` + colors.reset);
console.log(colors.lightBlue + `  search次数/轮: ${KSSEARCH_COUNT}` + colors.reset);
console.log(colors.lightBlue + `  follow次数/look: ${KSFOLLOW_COUNT}` + colors.reset);
console.log(colors.lightBlue + `  search_follow次数/search: ${KSSEARCHFOLLOW_COUNT}` + colors.reset);

const results = [];

if (accountCount > (process.env.MAX_CONCURRENCY || 999)) {
  console.log(colors.red + ("错误: 检测到 " + accountCount + " 个账号配置，最多只允许" + (process.env.MAX_CONCURRENCY || 999) + "个"));
  process.exit(1);
}

/**
 * 生成快手设备ID
 */
function generateKuaishouDid() {
  try {
    const generateRandomHexString = (length) => {
      const hexChars = "0123456789abcdef";
      let result = "";
      for (let i = 0; i < length; i++) {
        result += hexChars.charAt(Math.floor(Math.random() * hexChars.length));
      }
      return result;
    };
    const randomId = generateRandomHexString(16);
    return "ANDROID_" + randomId;
  } catch (error) {
    const timestamp = Date.now().toString(16).toUpperCase();
    return "ANDROID_" + timestamp.substring(0, 16);
  }
}

/**
 * 发送HTTP请求的通用方法
 */
async function sendRequest(requestOptions, proxyUrl = null, description = "Unknown Request") {
  const finalOptions = { ...requestOptions };
  let agent = null;

  if (proxyUrl) {
    try {
      agent = new SocksProxyAgent(proxyUrl);
    } catch (proxyError) {
      console.log(colors.red + ("[错误] " + description + " 代理URL无效(" + proxyError.message + ")，尝试直连模式"));
    }
  }

  try {
    const axiosConfig = {
      method: finalOptions.method || "GET",
      url: finalOptions.url,
      headers: finalOptions.headers || {},
      data: finalOptions.body || finalOptions.form,
      timeout: finalOptions.timeout || 30000,
      ...(agent && { httpAgent: agent, httpsAgent: agent }),
    };
    const response = await axios(axiosConfig);
    return { response: response, body: response.data };
  } catch (error) {
    if (error.response) {
      return { response: error.response, body: null };
    }
    return { response: null, body: null };
  }
}

/**
 * 验证IP地址格式是否有效
 */
function isValidIP(ip) {
  if (!ip || typeof ip !== 'string') return false;
  if (ip.includes('<html>') || ip.includes('503 Service Temporarily Unavailable') || ip.includes('502 Bad Gateway') || ip.includes('504 Gateway Timeout')) {
    return false;
  }
  const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
  const ipv6Regex = /^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;
  if (ipv4Regex.test(ip)) {
    const parts = ip.split('.');
    for (const part of parts) {
      const num = parseInt(part, 10);
      if (num < 0 || num > 255 || isNaN(num)) return false;
    }
    return true;
  }
  return ipv6Regex.test(ip);
}

/**
 * 测试代理连接性
 */
async function testProxyConnectivity(proxyUrl, description = "代理连通性检测", maxRetries = 3) {
  if (!proxyUrl) {
    return { ok: true, msg: colors.green + "✅ 未配置代理（直连模式）", ip: "localhost" };
  }

  let lastError = null;
  const testEndpoints = ["https://httpbin.org/ip", "https://api.ipify.org?format=json"];
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    console.log(colors.blue + (`🔌 ${description} 测试代理连接中... (尝试 ${attempt}/${maxRetries})`));
    
    for (const endpoint of testEndpoints) {
      try {
        const { response: ipResponse, body: ipResult } = await sendRequest(
          { method: "GET", url: endpoint, headers: { "User-Agent": "ProxyTester/1.0" }, timeout: 15000 },
          proxyUrl,
          description + " → " + new URL(endpoint).hostname
        );
        
        if (typeof ipResult === 'string' && (ipResult.includes('<html>') || ipResult.includes('503 Service Temporarily Unavailable') || ipResult.includes('502 Bad Gateway') || ipResult.includes('504 Gateway Timeout'))) {
          continue;
        }
        
        if (ipResult) {
          let ip = null;
          if (endpoint.includes('httpbin.org') && ipResult.origin) ip = ipResult.origin;
          else if (endpoint.includes('ipify.org') && ipResult.ip) ip = ipResult.ip;
          else if (typeof ipResult === 'string' && !ipResult.includes('<')) ip = ipResult.trim();
          
          if (ip && isValidIP(ip)) {
            console.log(colors.green + (`✅ ${description} 代理测试成功，出口IP: ${ip}`));
            return { ok: true, msg: colors.green + (`✅ SOCKS5代理正常，出口IP: ${ip}`), ip: ip };
          }
        }
      } catch (error) {
        lastError = error;
        continue;
      }
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    if (attempt < maxRetries) {
      const waitTime = attempt * 2000;
      console.log(colors.yellow + (`⏱️ ${description} 所有端点测试失败，${waitTime/1000}秒后重试...`));
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
  }

  try {
    const proxyUrlRegex = /^(socks5|http|https):\/\/([^:@]+:[^@]+@)?[^:]+:\d+$/;
    if (!proxyUrlRegex.test(proxyUrl)) throw new Error('无效的代理URL格式');
    if (proxyUrl.startsWith('http://') || proxyUrl.startsWith('https://')) new URL(proxyUrl);
  } catch (error) {
    return { ok: false, msg: colors.red + (`❌ 代理URL格式错误: ${proxyUrl}`), ip: null };
  }

  return { ok: false, msg: colors.red + (`❌ 代理测试失败: ${lastError?.message || "所有测试端点均无法访问"}`), ip: null };
}

const usedProxies = new Set();

/**
 * 获取账号基本信息
 */
async function getAccountBasicInfo(cookie, proxyUrl, accountId = "?") {
  const url = "https://nebula.kuaishou.com/rest/n/nebula/activity/earn/overview/basicInfo?source=bottom_guide_first";
  const { body: result } = await sendRequest(
    { method: "GET", url: url, headers: { Host: "nebula.kuaishou.com", "User-Agent": this.userAgent, Cookie: cookie, "Content-Type": "application/x-www-form-urlencoded" }, timeout: 12000 },
    proxyUrl,
    "账号[" + accountId + "] 获取基本信息"
  );
  if (result && result.result === 1 && result.data) {
    return { nickname: result.data.userData?.nickname || null, totalCoin: result.data.totalCoin ?? null, allCash: result.data.allCash ?? null };
  }
  return null;
}

function centerAlign(text, width) {
  text = String(text);
  if (text.length >= width) return text.substring(0, width);
  const padding = width - text.length;
  const leftPadding = Math.floor(padding / 2);
  const rightPadding = padding - leftPadding;
  return " ".repeat(leftPadding) + text + " ".repeat(rightPadding);
}

class KuaishouAdTask {
  constructor({ index, salt, cookie, nickname = "", proxyUrl = null, tasksToExecute = ["food", "box", "look", "search"], remark = "" }) {
    this.index = index;
    this.salt = salt;
    this.cookie = cookie;
    this.nickname = nickname || remark || "账号" + index;
    this.remark = remark;
    this.proxyUrl = proxyUrl;
    this.coinLimit = KSCOIN_LIMIT;
    this.coinExceeded = false;
    this.tasksToExecute = tasksToExecute;
    this.adaddnum = 0;
    this.retryCount = KS_RETRY_COUNT;
    this.taskFailedCount = 1;
    this.stopAllTasks = false;
    this.oneCoinRetryCount = 0;
    this.userAgent = MOBILE_UA_POOL[index % MOBILE_UA_POOL.length];
    console.log(colors.blue + `💡 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 分配UA: ${this.userAgent.substring(0, 100)}...` + colors.reset);
    this.extractCookieInfo();
    
    this.headers = {
      Host: "nebula.kuaishou.com",
      Connection: "keep-alive",
      "User-Agent": this.userAgent,
      Cookie: this.cookie,
      "content-type": "application/json",
    };

    this.taskReportPath = "/rest/r/ad/task/report";
    this.startTime = Date.now();
    this.endTime = this.startTime - 30000;
    this.queryParams = "mod=Xiaomi(MI 11)&appver=" + this.appver + "&egid=" + this.egid + "&did=" + this.did;
      
    this.taskConfigs = {
      box: { name: "宝箱广告", pageId: 11101, businessId: 606, posId: 20346, subPageId: 100024064, requestSceneType: 1, taskType: 1 },
      look: { name: "看广告得金币", pageId: 11101, businessId: 672, posId: 24067, subPageId: 100026367, requestSceneType: 1, taskType: 1 },
      food: { name: "饭补广告", pageId: 11101, businessId: 9362, posId: 24067, subPageId: 100026367, requestSceneType: 7, taskType: 2 },
      follow: { name: "追加看广告得金币", pageId: 11101, businessId: 672, posId: 24067, subPageId: 100026367, requestSceneType: 2, taskType: 1 },
      search: { name: "搜索任务", pageId: 11014, businessId: 7076, posId: 216268, subPageId: 100161537, requestSceneType: 1, taskType: 1 },
      search_follow: { name: "搜索任务追加", pageId: 11014, businessId: 7076, posId: 216268, subPageId: 100161537, requestSceneType: 7, taskType: 2 },
    };

    this.taskStats = {};
    const allTaskKeys = new Set(this.tasksToExecute);
    allTaskKeys.add('follow'); 
    allTaskKeys.add('search');
    allTaskKeys.add('search_follow');
    
    allTaskKeys.forEach((taskKey) => {
      if (this.taskConfigs[taskKey]) {
        this.taskStats[taskKey] = { success: 0, failed: 0, totalReward: 0 };
      }
    });

    this.lowRewardStreak = 0;
    this.lowRewardThreshold = KSLOW_REWARD_THRESHOLD;
    this.lowRewardLimit = KSLOW_REWARD_LIMIT;
    this.stopAllTasks = false;

    this.taskLimitReached = {};
    this.tasksToExecute.forEach((taskKey) => {
      if (this.taskConfigs[taskKey]) this.taskLimitReached[taskKey] = false;
    });
    this.taskLimitReached.follow = false;
    this.taskLimitReached.search = false;
    this.taskLimitReached.search_follow = false;
  }

  async checkCoinLimit() {
    try {
      const accountInfo = await getAccountBasicInfo(this.cookie, this.proxyUrl, this.index);
      if (accountInfo && accountInfo.totalCoin) {
        const currentCoin = parseInt(accountInfo.totalCoin);
        if (currentCoin >= this.coinLimit) {
          console.log(colors.yellow + `⚠️ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 金币已达 ${currentCoin}，超过 ${this.coinLimit} 阈值，将停止任务` + colors.reset);
          this.coinExceeded = true;
          this.stopAllTasks = true;
          return true;
        }
      }
      return false;
    } catch (error) {
      console.log(colors.red + `账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 金币检查异常: ${error.message}` + colors.reset);
      return false;
    }
  }

  generateRandomHexString(length) {
    const hexChars = "0123456789abcdef";
    let result = "";
    for (let i = 0; i < length; i++) result += hexChars.charAt(Math.floor(Math.random() * hexChars.length));
    return result;
  }

  extractCookieInfo() {
    try {
      const egidMatch = this.cookie.match(/egid=([^;]+)/);
      const didMatch = this.cookie.match(/did=([^;]+)/);
      const userIdMatch = this.cookie.match(/userId=([^;]+)/);
      const apiStMatch = this.cookie.match(/kuaishou\.api_st=([^;]+)/);
      const appverMatch = this.cookie.match(/appver=([^;]+)/);
      this.egid = egidMatch ? egidMatch[1] : "";
      this.did = didMatch ? didMatch[1] : "";
      this.userId = userIdMatch ? userIdMatch[1] : "";
      this.kuaishouApiSt = apiStMatch ? apiStMatch[1] : "";
      this.appver = appverMatch ? appverMatch[1] : "13.8.40.10657";
      if (!this.egid || !this.did) {
        console.log(colors.yellow + (`账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} cookie格式可能无 egid 或 did，但继续尝试...`));
      }
    } catch (error) {
      console.log(colors.red + (`账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 解析cookie失败: ${error.message}`));
    }
  }

  getTaskStats() { return this.taskStats; }

  printTaskStats() {
    console.log(colors.cyan + (`\n账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 任务执行统计:`));
    const printOrder = ['box', 'look', 'follow', 'food', 'search', 'search_follow'];
    printOrder.forEach(taskKey => {
      const stats = this.taskStats[taskKey];
      const taskConfig = this.taskConfigs[taskKey];
      if (stats && taskConfig) {
        console.log(colors.lightBlue + (`  ${taskConfig.name} - 成功: ${stats.success}, 失败: ${stats.failed}, 总奖励: ${stats.totalReward}金币`));
      }
    });
  }

  async retryOperation(operation, description, maxRetries = 3, delay = 2000) {
    let attempts = 0;
    let lastError = null;
    while (attempts < maxRetries) {
      if (this.stopAllTasks) {
        console.log(colors.red + `账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 任务已停止，取消重试` + colors.reset);
        return null;
      }
      try {
        const result = await operation();
        if (this.stopAllTasks) {
          console.log(colors.red + `账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 任务已停止，取消重试` + colors.reset);
          return null;
        }
        if (result) return result;
        lastError = new Error(description + " 返回空结果");
      } catch (error) {
        lastError = error;
        console.log(colors.red + `账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} ${description} 异常: ${error.message}` + colors.reset);
      }
      attempts++;
      if (attempts < maxRetries) {
        console.log(colors.yellow + `账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} ${description} 失败，重试 ${attempts}/${maxRetries}` + colors.reset);
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }
    return null;
  }

  async getAdInfo(taskConfig) {
    try {
      const adPath = "/rest/e/reward/mixed/ad";
      const formData = {
        encData: "|encData|", sign: "|sign|", cs: "false", client_key: "2ac2a76d", videoModelCrowdTag: "1_23", os: "android",
        "kuaishou.api_st": this.kuaishouApiSt, uQaTag: "1##swLdgl:99#ecPp:-9#cmNt:-0#cmHs:-3#cmMnsl:-0",
      };
      const queryData = {
        earphoneMode: "1", mod: "Xiaomi(24129PN74C)", appver: this.appver, isp: "CUCC", language: "zh-cn", ud: this.userId, did_tag: "0",
        net: "WIFI", kcv: "1599", app: "0", kpf: "ANDROID_PHONE", ver: "11.6", android_os: "0", boardPlatform: "pineapple", kpn: "NEBULA",
        androidApiLevel: "35", country_code: "cn", sys: "ANDROID_16", sw: "1080", sh: "2400", abi: "arm64", userRecoBit: "0",
      };

      let impExtDataString = "{}";
      if (taskConfig.businessId === 7076) {
        const neoParamsBase64 = "eyJwYWdlSWQiOiAxMTAxNCwgInN1YlBhZ2VJZCI6IDEwMDE2MTUzNywgInBvc0lkIjogMjE2MjY4LCAiYnVzaW5lc3NJZCI6IDcwNzYsICJleHRQYXJhbXMiOiAiIiwgImN1c3RvbURhdGEiOiB7ImV4aXRJbmZvIjogeyJ0b2FzdERlc2MiOiBudWxsLCAidG9hc3RJbWdVcmwiOiBudWxsfX0sICJwZW5kYW50VHlwZSI6IDEsICJkaXNwbGF5VHlwZSI6IDIsICJzaW5nbGVQYWdlSWQiOiAwLCAic2luZ2xlU3ViUGFnZUlkIjogMCwgImNoYW5uZWwiOiAwLCAiY291bnRkb3duUmVwb3J0IjogZmFsc2UsICJ0aGVtZVR5cGUiOiAwLCAibWl4ZWRBZCI6IHRydWUsICJmdWxsTWl4ZWQiOiB0cnVlLCAiYXV0b1JlcG9ydCI6IHRydWUsICJmcm9tVGFza0NlbnRlciI6IHRydWUsICJzZWFyY2hJbnNwaXJlU2NoZW1lSW5mbyI6IG51bGwsICJhbW91bnQiOiAwfQ==";
        const impExtDataObject = {
          openH5AdCount: 0, sessionLookedCompletedCount: this.adaddnum, sessionType: (taskConfig.requestSceneType === 2 ? "2" : "1"),
          searchKey: generateHotKeywords(), triggerType: "2", disableReportToast: true, businessEnterAction: "7", neoParams: neoParamsBase64,
        };
        impExtDataString = JSON.stringify(impExtDataObject);
      }
      
      const requestBody = {
        appInfo: { appId: "kuaishou_nebula", name: "快手极速版", packageName: "com.kuaishou.nebula", version: this.appver, versionCode: -1 },
        deviceInfo: { osType: 1, osVersion: "15", deviceId: this.did, screenSize: { width: 1080, height: 2249 }, ftt: "" },
        userInfo: { userId: this.userId, age: 0, gender: "" },
        impInfo: [{ pageId: taskConfig.pageId || 11101, subPageId: taskConfig.subPageId, action: 0, browseType: 3, impExtData: impExtDataString, mediaExtData: "{}" }],
      };

      const encodedBody = Buffer.from(JSON.stringify(requestBody)).toString("base64");
      let encsign = await this.getSign(encodedBody);
      if (!encsign) {
        console.log(colors.red + `❌ 账号[${this.nickname}] 获取 encsign 失败，无法获取广告` + colors.reset);
        return null;
      }

      formData.encData = encsign.encdata;
      formData.sign = encsign.sign;

      let nesig = await this.requestSignService({
        urlpath: adPath, reqdata: qs.stringify(formData) + "&" + qs.stringify(queryData), api_client_salt: this.salt,
      });

      if (!nesig) {
        console.log(colors.red + `❌ 账号[${this.nickname}] 获取 nesig 失败，无法获取广告` + colors.reset);
        return null;
      }

      const finalQueryData = { ...queryData, sig: nesig.sig, __NS_sig3: nesig.__NS_sig3, __NS_xfalcon: nesig.__NS_xfalcon, __NStokensig: nesig.__NStokensig };
      const url = "https://api.e.kuaishou.com" + adPath + "?" + querystring.stringify(finalQueryData);

      const { response, body: result } = await sendRequest(
        { method: "POST", url: url, headers: { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", Host: "api.e.kuaishou.com", "User-Agent": this.userAgent, Cookie: "kuaishou_api_st=" + this.kuaishouApiSt }, form: formData, timeout: 12000 },
        this.proxyUrl,
        `账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 获取广告`
      );
      
      if (!result) return null;
      if (!result.feeds || !result.feeds[0]) {
        console.log(colors.red + `❌ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 未获取到广告信息，请检查cookie是否过期` + colors.reset);
        this.stopAllTasks = true;
        return null;
      }
      
      const ad = result.feeds[0].ad;
      const awardValue = ad?.adDataV2?.inspirePersonalize?.awardValue || 0;
      console.log(colors.yellow + `🏷️ 预计获得奖励: ${awardValue}金币` + colors.reset);
      
      const numericAwardValue = Number(awardValue);
      if (numericAwardValue === 1) {
        this.oneCoinRetryCount++;
        if (this.oneCoinRetryCount >= KS_ONE_COIN_RETRY_LIMIT) {
          console.log(colors.red + `⚠️ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 该账号已经获得今日最大金币收益，请勿再执行任务避免黑号` + colors.reset);
          this.stopAllTasks = true;
          return null;
        }
        console.log(colors.yellow + `🔄 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 预计获得奖励为1金币，更换did后重新执行（${this.oneCoinRetryCount}/${KS_ONE_COIN_RETRY_LIMIT}）` + colors.reset);
        const newDid = generateKuaishouDid();
        this.cookie = this.cookie.replace(/did=([^;]+)/, `did=${newDid}`);
        this.did = newDid;
        console.log(colors.green + `✅ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 已更新did: ${newDid}` + colors.reset);
        return await this.getAdInfo(taskConfig);
      }
      
      if (numericAwardValue === 0) {
        console.log(colors.yellow + `🔄 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 预计获得奖励为0金币，重新获取广告` + colors.reset);
        return await this.getAdInfo(taskConfig);
      }
      
      if (numericAwardValue > 1) this.oneCoinRetryCount = 0;
      
      if (result.result === 6001) {
        console.log(colors.red + `🔒 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} Cookie已过期，请重新抓取Cookie` + colors.reset);
        this.stopAllTasks = true;
        return null;
      }
      if (result.result === 500) {
        console.log(colors.red + `❌ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""}💀 系统繁忙，请稍活跃账号或者明日重试` + colors.reset);
        this.stopAllTasks = true;
        return null;
      }
      
      if (result.errorMsg === "OK" && result.feeds && result.feeds[0] && result.feeds[0].ad) {
        const caption = result.feeds[0].caption || result.feeds[0].ad?.caption || "";
        if (caption) console.log(colors.green + `✅ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 成功获取到广告信息：${caption.substring(0, 10)}...` + colors.reset);
        const expTag = result.feeds[0].exp_tag || "";
        const llsid = expTag.split("/")[1]?.split("_")?.[0] || "";
        
        let isAppAd = false;
        let shouldDownload = false;
        let filePath = null;
        
        if (ENABLE_APP_DOWNLOAD) {
          const appName = ad.appName || ad.adDataV2?.originStyleInfo?.appName || ad.adDataV2?.appInfo?.appName || "";
          const packageName = ad.packageName || ad.adDataV2?.appInfo?.packageName || "";
          const appUrl = ad.url || ad.adDataV2?.appInfo?.url || "";
          isAppAd = appName && packageName && appUrl;
          if (isAppAd) {
            shouldDownload = Math.random() * 100 < APP_DOWNLOAD_PROBABILITY;
            if (shouldDownload) {
              console.log(colors.yellow + `📱 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 开始下载app: ${appName} (${packageName})` + colors.reset);
              const fs = require('fs');
              const path = require('path');
              const downloadDir = path.join(__dirname, 'download');
              if (!fs.existsSync(downloadDir)) fs.mkdirSync(downloadDir, { recursive: true });
              const fileName = `${appName.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}.apk`;
              filePath = path.join(downloadDir, fileName);
              try {
                const response = await axios({ method: 'GET', url: appUrl, responseType: 'stream', timeout: 60000 });
                const writer = fs.createWriteStream(filePath);
                response.data.pipe(writer);
                await new Promise((resolve, reject) => { writer.on('finish', resolve); writer.on('error', reject); });
                console.log(colors.green + `✅ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 下载完成: ${appName} 保存到 ${filePath}` + colors.reset);
              } catch (error) {
                console.log(colors.red + `❌ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 下载失败: ${error.message}` + colors.reset);
                filePath = null;
              }
            } else {
              console.log(colors.gray + `📱 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 跳过下载app: ${appName} (概率未触发)` + colors.reset);
            }
          }
        }
        return { cid: ad.creativeId, llsid: llsid, adInfo: ad, filePath: filePath, isZeroAward: awardValue === 0 };
      }
      
      console.log(colors.yellow + `⚠️ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 获取广告失败: ${result.errorMsg || JSON.stringify(result).substring(0, 50)}...` + colors.reset);
      return null;
    } catch (error) {
      console.log(colors.red + `❌ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 获取广告异常: ${error.message}` + colors.reset);
      return null;
    }
  }

  async generateSignature(creativeId, llsid, taskKey, taskConfig) {
    try {
      const bizData = JSON.stringify({
        businessId: taskConfig.businessId, endTime: this.endTime, extParams: "", mediaScene: "video",
        neoInfos: [{ creativeId: creativeId, extInfo: "", llsid: llsid, requestSceneType: taskConfig.requestSceneType, taskType: taskConfig.taskType, watchExpId: "", watchStage: 0 }],
        pageId: taskConfig.pageId, posId: taskConfig.posId, reportType: 0, sessionId: "", startTime: this.startTime, subPageId: taskConfig.subPageId,
      });
      const postData = "bizStr=" + encodeURIComponent(bizData) + "&cs=false&client_key=2ac2a76d&kuaishou.api_st=" + this.kuaishouApiSt;
      const urlData = this.queryParams + "&" + postData;
      const signResult = await this.requestSignService({ urlpath: this.taskReportPath, reqdata: urlData, api_client_salt: this.salt }, `账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 生成报告签名`);
      if (!signResult) return null;
      return { sig: signResult.sig, sig3: signResult.__NS_sig3, sigtoken: signResult.__NStokensig, xfalcon: signResult.__NS_xfalcon, post: postData };
    } catch (error) {
      console.log(colors.red + (`❌ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 生成签名异常: ${error.message}`));
      return null;
    }
  }

  async submitReport(sig, sig3, sigtoken, xfalcon, postData, taskKey, taskConfig, adInfo) {
    try {
      const currentQueryParams = "mod=Xiaomi(MI 11)&appver=" + this.appver + "&egid=" + this.egid + "&did=" + this.did;
      const url = "https://api.e.kuaishou.com" + this.taskReportPath + "?" + (currentQueryParams + "&sig=" + sig + "&__NS_sig3=" + sig3 + "&__NS_xfalcon=" + xfalcon + "&__NStokensig=" + sigtoken);
      const { response, body: result } = await sendRequest(
        { method: "POST", url: url, headers: { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", Host: "api.e.kuaishou.cn", "User-Agent": this.userAgent }, body: postData, timeout: 12000 },
        this.proxyUrl,
        `账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 提交任务`
      );
      
      if (!result) { this.deleteDownloadedApp(adInfo); return { success: false, reward: 0 }; }
      if (result.result === 1) {
        const reward = result.data?.neoAmount || 0;
        console.log(colors.green + `💰 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} ${taskConfig.name}获得${reward}金币奖励！` + colors.reset);
        let accountInfo = await getAccountBasicInfo(this.cookie, this.proxyUrl, this.userId);
        accountInfo = accountInfo || {};
        if (accountInfo && accountInfo.totalCoin !== undefined) console.log(colors.green + `账户${this.nickname}现有金币：${accountInfo.totalCoin}` + colors.reset);
        else console.log(colors.yellow + `账户${this.nickname}现有金币：获取失败` + colors.reset);
        
        if (reward <= this.lowRewardThreshold && reward !== 5) {
          this.lowRewardStreak++;
          this.did = generateKuaishouDid();
          console.log(colors.yellow + `⚠️ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 金币奖励(${reward})低于阈值(${this.lowRewardThreshold})，当前连续低奖励次数：${this.lowRewardStreak}/${this.lowRewardLimit}` + colors.reset);
          if (this.lowRewardStreak >= this.lowRewardLimit) {
            console.log(colors.red + `🏁 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 连续${this.lowRewardLimit}次奖励≤${this.lowRewardThreshold}，停止全部任务` + colors.reset);
            this.stopAllTasks = true;
          }
        } else if (reward === 5) {
          console.log(colors.blue + `💡 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 5金币可能为直播广告` + colors.reset);
        } else {
          this.lowRewardStreak = 0;
        }
        
        if (ENABLE_APP_DOWNLOAD && adInfo && adInfo.filePath) {
          const fs = require('fs');
          const filePath = adInfo.filePath;
          console.log(colors.yellow + `📱 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 开始删除app文件: ${filePath}` + colors.reset);
          try {
            if (fs.existsSync(filePath)) { fs.unlinkSync(filePath); console.log(colors.green + `✅ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 删除完成: ${filePath}` + colors.reset); }
            else console.log(colors.gray + `📱 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 文件不存在，跳过删除: ${filePath}` + colors.reset);
          } catch (error) { console.log(colors.red + `❌ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 删除失败: ${error.message}` + colors.reset); }
        }
        return { success: true, reward: reward };
      }

      if ([20107, 20108, 1003, 415].includes(result.result)) {
        console.log(colors.yellow + `⚠️ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} ${taskConfig.name} 已达上限` + colors.reset);
        this.taskLimitReached[taskKey] = true;
        this.deleteDownloadedApp(adInfo);
        return { success: false, reward: 0 };
      }

      if (result.result === 500) {
        console.log(colors.red + `❌ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} ${taskConfig.name} 任务失败，当前重试次数：${this.taskFailedCount}/${this.retryCount}` + colors.reset);
        this.taskFailedCount++;
        if (this.taskFailedCount >= this.retryCount) this.stopAllTasks = true;
      }
      
      this.deleteDownloadedApp(adInfo);
      return { success: false, reward: 0 };
    } catch (error) {
      console.log(colors.red + `❌ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 提交任务异常: ${error.message}` + colors.reset);
      this.deleteDownloadedApp(adInfo);
      return { success: false, reward: 0 };
    }
  }
  
  deleteDownloadedApp(adInfo) {
    if (ENABLE_APP_DOWNLOAD && adInfo && adInfo.filePath) {
      const fs = require('fs');
      const filePath = adInfo.filePath;
      console.log(colors.yellow + `📱 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 开始删除app文件: ${filePath}` + colors.reset);
      try {
        if (fs.existsSync(filePath)) { fs.unlinkSync(filePath); console.log(colors.green + `✅ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 删除完成: ${filePath}` + colors.reset); }
        else console.log(colors.gray + `📱 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 文件不存在，跳过删除: ${filePath}` + colors.reset);
      } catch (error) { console.log(colors.red + `❌ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 删除失败: ${error.message}` + colors.reset); }
    }
  }

  async getSign(requestData) {
    try {
      const { response, body: result } = await sendRequest({
        method: "POST", url: `${KS_SIGN_API_URL}/encsign`, body: JSON.stringify({ data: requestData }), headers: { "Content-Type": "application/json" },
      });
      if (result && result.status) return result.data;
      console.log(colors.red + `❌ 账号[${this.nickname}] encsign 签名服务失败: ${result?.message || '无响应'}` + colors.reset);
      return null;
    } catch (error) {
      console.log(colors.red + `❌ 账号[${this.nickname}] encsign 签名请求异常: ${error.message}` + colors.reset);
      return null;
    }
  }

  async requestSignService(requestData, description) {
    let returnData = {};
    let newreqdata = { path: requestData.urlpath, data: requestData.reqdata, salt: requestData.api_client_salt };
    const { response, body: result } = await sendRequest(
      { method: "POST", url: `${KS_SIGN_API_URL}/nssig`, headers: { "Content-Type": "application/json", "User-Agent": "Mozilla/5.0" }, body: JSON.stringify(newreqdata), timeout: 15000 },
      null, description + "（签名服务）"
    );
    if (result && result.data) {
      let __NS_sig3 = result.data.nssig3;
      let __NStokensig = result.data.nstokensig;
      let __NS_xfalcon = result.data.nssig4;
      Object.assign(returnData, { __NS_sig3, __NStokensig, sig: result.data.sig, __NS_xfalcon });
      return returnData;
    }
    console.log(colors.red + `❌ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 签名服务失败: ${result?.error || result?.message || "无响应"}` + colors.reset);
    return null;
  }

  async executeTask(taskKey) {
    const taskConfig = this.taskConfigs[taskKey];
    if (!taskConfig) return false;
    if (this.taskLimitReached[taskKey]) return false;

    try {
      const adInfo = await this.retryOperation(() => this.getAdInfo(taskConfig), `获取${taskConfig.name}信息`, 3);
      if (!adInfo) { this.taskStats[taskKey].failed++; return false; }

      if (adInfo.isZeroAward) {
        const skipTime = 2000;
        console.log(colors.blue + `🔍 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} ==>${taskConfig.name} 检测到直播广告，等待 ${skipTime/1000} 秒后跳过` + colors.reset);
        await new Promise((resolve) => setTimeout(resolve, skipTime));
        console.log(colors.green + `✅ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 跳过直播广告，执行下一个广告` + colors.reset);
        return false;
      }

      const watchTime = Math.floor(Math.random() * (KS_MAX_WATCH_TIME - KS_MIN_WATCH_TIME + 1)) + KS_MIN_WATCH_TIME;
      console.log(colors.blue + `🔍 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} ==>${taskConfig.name} ${generateRandomInteractionMessage()} ${Math.round(watchTime / 1000)} 秒` + colors.reset);
      await new Promise((resolve) => setTimeout(resolve, watchTime));

      const signature = await this.retryOperation(() => this.generateSignature(adInfo.cid, adInfo.llsid, taskKey, taskConfig), `生成${taskConfig.name}签名`);
      if (!signature) { this.taskStats[taskKey].failed++; return false; }

      const submitResult = await this.retryOperation(() => this.submitReport(signature.sig, signature.sig3, signature.sigtoken, signature.xfalcon, signature.post, taskKey, taskConfig, adInfo), `提交${taskConfig.name}报告`, 3);
      if (submitResult?.success) { this.taskStats[taskKey].success++; this.taskStats[taskKey].totalReward += submitResult.reward || 0; return true; }
      this.taskStats[taskKey].failed++;
      return false;
    } catch (error) {
      console.log(colors.red + `❌ 账号[${this.nickname}]${this.remark ? "（" + this.remark + "）" : ""} 任务异常(${taskKey}): ${error.message}` + colors.reset);
      this.taskStats[taskKey].failed++;
      return false;
    }
  }

  async executeAllTasksByPriority() {
    for (let round = 0; round < KSROUNDS; round++) {
      if (this.stopAllTasks) break;
      console.log(colors.magenta + `\n============================== 🚀 账号[${this.nickname}] 第${round + 1}/${KSROUNDS}轮开始 ==============================` + colors.reset);

      for (const taskKey of this.tasksToExecute) {
        if (this.stopAllTasks) break;
        const taskConfig = this.taskConfigs[taskKey];
        if (this.taskLimitReached[taskKey]) { console.log(colors.yellow + `⚠️ 账号[${this.nickname}] ${taskConfig.name} 已达上限，本轮跳过` + colors.reset); continue; }

        if (taskKey === 'look') {
          const lookConfig = this.taskConfigs.look;
          const followConfig = this.taskConfigs.follow;
          console.log(colors.cyan + `🎬 开始执行 ${lookConfig.name} (+${followConfig.name})，本轮共 ${KSLOOK_COUNT} 次` + colors.reset);
          for (let i = 0; i < KSLOOK_COUNT; i++) {
            if (this.stopAllTasks || this.taskLimitReached.look) break;
            console.log(colors.blue + `\n--- 账号[${this.nickname}] ${lookConfig.name} 第 ${i + 1}/${KSLOOK_COUNT} 次执行 ---` + colors.reset);
            const lookSuccess = await this.executeTask('look');
            if (lookSuccess && !this.stopAllTasks) {
              const followWaitTime = Math.floor(Math.random() * (KS_MAX_WAIT_TIME - KS_MIN_WAIT_TIME + 1)) + KS_MIN_WAIT_TIME;
              console.log(colors.yellow + `⏱ 账号[${this.nickname}] look 任务成功，随机等待 ${Math.round(followWaitTime / 1000)} 秒后执行 ${followConfig.name}` + colors.reset);
              await new Promise((resolve) => setTimeout(resolve, followWaitTime));
              const followTimes = KSFOLLOW_COUNT;
              for (let j = 0; j < followTimes; j++) {
                if (this.stopAllTasks || this.taskLimitReached.follow) break;
                console.log(colors.blue + `\n--- 账号[${this.nickname}] ${followConfig.name} (第 ${j + 1}/${followTimes} 次) 紧随 look 任务执行 ---` + colors.reset);
                await this.executeTask('follow');
              }
            }
            if (i < KSLOOK_COUNT - 1 && !this.stopAllTasks && !this.taskLimitReached.look) {
              const lookWaitTime = Math.floor(Math.random() * (KS_MAX_WAIT_TIME - KS_MIN_WAIT_TIME + 1)) + KS_MIN_WAIT_TIME;
              console.log(colors.yellow + `⏱ 账号[${this.nickname}] ${lookConfig.name} 任务间隔，随机等待 ${Math.round(lookWaitTime / 1000)} 秒` + colors.reset);
              await new Promise((resolve) => setTimeout(resolve, lookWaitTime));
            }
          }
        }

        if (taskKey === 'search') {
          const searchConfig = this.taskConfigs.search;
          const searchFollowConfig = this.taskConfigs.search_follow;
          console.log(colors.cyan + `\n🎬 开始执行 ${searchConfig.name} (+${searchFollowConfig.name})，本轮共 ${KSSEARCH_COUNT} 次` + colors.reset);
          for (let i = 0; i < KSSEARCH_COUNT; i++) {
            if (this.stopAllTasks || this.taskLimitReached.search) break;
            console.log(colors.blue + `\n--- 账号[${this.nickname}] ${searchConfig.name} 第 ${i + 1}/${KSSEARCH_COUNT} 次执行 ---` + colors.reset);
            const searchSuccess = await this.executeTask('search');
            if (searchSuccess && !this.stopAllTasks) {
              const searchFollowWaitTime = Math.floor(Math.random() * (KS_MAX_WAIT_TIME - KS_MIN_WAIT_TIME + 1)) + KS_MIN_WAIT_TIME;
              console.log(colors.yellow + `⏱ 账号[${this.nickname}] search 任务成功，随机等待 ${Math.round(searchFollowWaitTime / 1000)} 秒后执行 ${searchFollowConfig.name}` + colors.reset);
              await new Promise((resolve) => setTimeout(resolve, searchFollowWaitTime));
              const searchFollowTimes = KSSEARCHFOLLOW_COUNT;
              for (let j = 0; j < searchFollowTimes; j++) {
                if (this.stopAllTasks || this.taskLimitReached.search_follow) break;
                console.log(colors.blue + `\n--- 账号[${this.nickname}] ${searchFollowConfig.name} (第 ${j + 1}/${searchFollowTimes} 次) 紧随 search 任务执行 ---` + colors.reset);
                this.adaddnum++;
                await this.executeTask('search_follow');
                this.adaddnum = 0;
              }
            }
            if (i < KSSEARCH_COUNT - 1 && !this.stopAllTasks && !this.taskLimitReached.search) {
              const searchWaitTime = Math.floor(Math.random() * (KS_MAX_WAIT_TIME - KS_MIN_WAIT_TIME + 1)) + KS_MIN_WAIT_TIME;
              console.log(colors.yellow + `⏱ 账号[${this.nickname}] ${searchConfig.name} 任务间隔，随机等待 ${Math.round(searchWaitTime / 1000)} 秒` + colors.reset);
              await new Promise((resolve) => setTimeout(resolve, searchWaitTime));
            }
          }
        }
        
        if (taskKey === 'food' || taskKey === 'box') {
          console.log(colors.cyan + `\n🎬 开始执行 ${taskConfig.name}，本轮共 ${KSLOOK_COUNT} 次` + colors.reset);
          for (let i = 0; i < KSLOOK_COUNT; i++) {
            if (this.stopAllTasks || this.taskLimitReached[taskKey]) break;
            console.log(colors.blue + `\n--- 账号[${this.nickname}] ${taskConfig.name} 第 ${i + 1}/${KSLOOK_COUNT} 次执行 ---` + colors.reset);
            await this.executeTask(taskKey);
            if (i < KSLOOK_COUNT - 1 && !this.stopAllTasks && !this.taskLimitReached[taskKey]) {
              const waitTime = Math.floor(Math.random() * (KS_MAX_WAIT_TIME - KS_MIN_WAIT_TIME + 1)) + KS_MIN_WAIT_TIME;
              console.log(colors.yellow + `⏱ 账号[${this.nickname}] ${taskConfig.name} 任务间隔，随机等待 ${Math.round(waitTime / 1000)} 秒` + colors.reset);
              await new Promise((resolve) => setTimeout(resolve, waitTime));
            }
          }
        }
      }

      if (round < KSROUNDS - 1 && !this.stopAllTasks) {
        const roundWaitTime = Math.floor(Math.random() * 10000) + 60000;
        console.log(colors.magenta + `\n============================== ⏱ 账号[${this.nickname}] 第${round + 1}轮完成，等待 ${Math.round(roundWaitTime / 1000)} 秒进入下一轮 ==============================` + colors.reset);
        await new Promise((resolve) => setTimeout(resolve, roundWaitTime));
      }
    }
    return {};
  }
}

function parseAccountConfig(configString) {
  const parts = String(configString || "").trim().split("#");
  if (parts.length < 2) return null;
  let remark = "", cookie = "", salt = "", proxyUrl = null;
  if (parts.length === 2) { cookie = parts[0]; salt = parts[1]; }
  else if (parts.length === 3) {
    if (/socks5:\/\//i.test(parts[2])) { cookie = parts[0]; salt = parts[1]; proxyUrl = parts[2]; }
    else { remark = parts[0]; cookie = parts[1]; salt = parts[2]; }
  } else if (parts.length >= 4) {
    remark = parts[0]; cookie = parts[1]; salt = parts.slice(2, parts.length - 1).join("#"); proxyUrl = parts[parts.length - 1];
  }
  if (proxyUrl && !/^socks5:\/\//i.test(proxyUrl)) proxyUrl = null;
  return { remark: remark || "", salt: salt, cookie: cookie, proxyUrl: proxyUrl };
}

function loadAccountsFromEnv() {
  const accountConfigs = getAccountConfigsFromEnv();
  const accounts = [];
  for (const configString of accountConfigs) {
    const accountConfig = parseAccountConfig(configString);
    if (accountConfig) accounts.push(accountConfig);
    else console.log(colors.red + (`账号格式错误：${configString}`));
  }
  accounts.forEach((account, index) => account.index = index + 1);
  return accounts;
}

async function concurrentExecute(items, concurrency, processor) {
  const results = new Array(items.length);
  let currentIndex = 0;
  async function worker() {
    while (true) {
      const index = currentIndex++;
      if (index >= items.length) return;
      const item = items[index];
      try { results[index] = await processor(item, index); }
      catch (error) { console.log(colors.red + (`并发执行异常（index=${index + 1}）：${error.message}`)); results[index] = null; }
    }
  }
  const workers = Array.from({ length: Math.min(concurrency, items.length) }, worker);
  await Promise.all(workers);
  return results;
}

async function processAccount(accountConfig) {
  if (accountConfig.proxyUrl) {
    const proxyTest = await testProxyConnectivity(accountConfig.proxyUrl, `账号[${accountConfig.index}]${accountConfig.remark ? "（" + accountConfig.remark + "）" : ""}`);
    console.log(colors.blue + `  - ${proxyTest.ok ? "✅ 代理验证通过" : "❌ 代理验证失败"}: ${proxyTest.msg}` + colors.reset);
    if (proxyTest.ok && proxyTest.ip && proxyTest.ip !== "localhost") {
      if (!isValidIP(proxyTest.ip)) console.log(colors.yellow + `⚠️ 账号[${accountConfig.index}] 检测到无效IP格式，跳过重复检查` + colors.reset);
      else if (usedProxies.has(proxyTest.ip)) { console.log(colors.red + `\n⚠️ 存在相同代理IP（${proxyTest.ip}），请立即检查！` + colors.reset); process.exit(1); }
      else usedProxies.add(proxyTest.ip);
    } else if (!proxyTest.ok) {
      console.log(colors.red + `❌ 账号[${accountConfig.index}] 代理测试失败，跳过该账号` + colors.reset);
      return { index: accountConfig.index, remark: accountConfig.remark || "无备注", nickname: `账号${accountConfig.index}`, initialCoin: 0, finalCoin: 0, coinChange: 0, initialCash: 0, finalCash: 0, cashChange: 0, error: `代理测试失败: ${proxyTest.msg}`, skipped: true };
    }
  } else console.log(colors.blue + `账号[${accountConfig.index}]${accountConfig.remark ? "（" + accountConfig.remark + "）" : ""} 未配置代理，走直连` + colors.reset);

  console.log(colors.blue + `账号[${accountConfig.index}]${accountConfig.remark ? "（" + accountConfig.remark + "）" : ""} 🔍 获取账号信息中...` + colors.reset);
  let initialAccountInfo = await getAccountBasicInfo(accountConfig.cookie, accountConfig.proxyUrl, accountConfig.index);
  let nickname = initialAccountInfo?.nickname || "账号" + accountConfig.index;
  if (initialAccountInfo) {
    const totalCoin = initialAccountInfo.totalCoin != null ? initialAccountInfo.totalCoin : "未知";
    const allCash = initialAccountInfo.allCash != null ? initialAccountInfo.allCash : "未知";
    console.log(colors.green + `账号[${nickname}] ✅ 登录成功，💰 当前金币: ${totalCoin}，💸 当前余额: ${allCash}` + colors.reset);
  } else console.log(colors.red + `账号[${nickname}] ❌ 基本信息获取失败，但仍继续执行任务` + colors.reset);

  const adTask = new KuaishouAdTask({ ...accountConfig, nickname: nickname, tasksToExecute: tasksToExecute });
  if (initialAccountInfo) {
    await adTask.checkCoinLimit();
    if (adTask.coinExceeded) {
      console.log(colors.yellow + `账号[${adTask.nickname}]${accountConfig.remark ? "（" + accountConfig.remark + "）" : ""} 初始金币已超过阈值，不执行任务` + colors.reset);
      const finalAccountInfo = await getAccountBasicInfo(accountConfig.cookie, accountConfig.proxyUrl, accountConfig.index);
      const initialCoin = initialAccountInfo?.totalCoin || 0;
      const finalCoin = finalAccountInfo?.totalCoin || 0;
      const coinChange = finalCoin - initialCoin;
      const initialCash = initialAccountInfo?.allCash || 0;
      const finalCash = finalAccountInfo?.allCash || 0;
      const cashChange = finalCash - initialCash;
      return { index: accountConfig.index, remark: accountConfig.remark || "无备注", nickname: nickname, initialCoin, finalCoin, coinChange, initialCash, finalCash, cashChange, stats: adTask.getTaskStats(), coinLimitExceeded: true };
    }
  }

  console.log(colors.blue + `账号[${adTask.nickname}]${accountConfig.remark ? "（" + accountConfig.remark + "）" : ""} 🚀 开始执行所有任务` + colors.reset);
  await adTask.executeAllTasksByPriority();

  const finalAccountInfo = await getAccountBasicInfo(accountConfig.cookie, accountConfig.proxyUrl, accountConfig.index);
  const initialCoin = initialAccountInfo?.totalCoin || 0;
  const finalCoin = finalAccountInfo?.totalCoin || 0;
  const coinChange = finalCoin - initialCoin;
  const initialCash = initialAccountInfo?.allCash || 0;
  const finalCash = finalAccountInfo?.allCash || 0;
  const cashChange = finalCash - initialCash;
  adTask.printTaskStats();
  return { index: accountConfig.index, remark: accountConfig.remark || "无备注", nickname: nickname, initialCoin, finalCoin, coinChange, initialCash, finalCash, cashChange, stats: adTask.getTaskStats(), coinLimitExceeded: adTask.coinExceeded, infoFetchFailed: !initialAccountInfo };
}

function printAccountsSummary(accountResults) {
  if (!accountResults.length) { console.log(colors.red + "\n没有可显示的账号信息。" + colors.reset); return; }
  const totalInitialCoin = accountResults.reduce((sum, a) => sum + (parseInt(a.initialCoin) || 0), 0);
  const totalFinalCoin = accountResults.reduce((sum, a) => sum + (parseInt(a.finalCoin) || 0), 0);
  const totalCoinChange = totalFinalCoin - totalInitialCoin;
  const totalInitialCash = accountResults.reduce((sum, a) => sum + (parseFloat(a.initialCash) || 0), 0);
  const totalFinalCash = accountResults.reduce((sum, a) => sum + (parseFloat(a.finalCash) || 0), 0);
  const totalCashChange = totalFinalCash - totalInitialCash;
  let totalTasks = 0, totalSuccessTasks = 0, totalReward = 0;
  accountResults.forEach(a => {
    if (a.stats) Object.values(a.stats).forEach(s => { totalTasks += s.success + s.failed; totalSuccessTasks += s.success; totalReward += s.totalReward; });
  });
  const successRate = totalTasks > 0 ? ((totalSuccessTasks / totalTasks) * 100).toFixed(1) : "0.0";
  const skippedAccounts = accountResults.filter(a => a.skipped).length;
  console.log(colors.green + "\n========== 快手养号任务执行结果汇总 ==========" + colors.reset);
  console.log(colors.blue + "📊 总体统计:" + colors.reset);
  console.log(colors.lightBlue + `  总账号数: ${accountResults.length}` + colors.reset);
  console.log(colors.lightBlue + `  跳过账号: ${skippedAccounts}` + colors.reset);
  console.log(colors.lightBlue + `  总任务数: ${totalTasks}` + colors.reset);
  console.log(colors.lightBlue + `  任务成功率: ${successRate}%` + colors.reset);
  console.log(colors.lightBlue + `  总金币变化: ${totalCoinChange}` + colors.reset);
  console.log(colors.lightBlue + `  总金币奖励: ${totalReward}` + colors.reset);
  console.log(colors.lightBlue + `  总余额变化: ${totalCashChange.toFixed(2)}` + colors.reset);
  console.log(colors.blue + "\n📋 账号详情:" + colors.reset);
  accountResults.forEach((account, idx) => {
    console.log(colors.gray + "\n----------------------------------------" + colors.reset);
    console.log(colors.magenta + `账号 #${idx + 1}:` + colors.reset);
    console.log(colors.lightBlue + `  序号: ${account.index}` + colors.reset);
    console.log(colors.lightBlue + `  备注: ${account.remark}` + colors.reset);
    let statusSymbol = account.skipped ? "❌" : (account.coinLimitExceeded ? "⚠️" : (account.infoFetchFailed ? "🔶" : ""));
    console.log(colors.lightBlue + `  账号昵称: ${account.nickname} ${statusSymbol}` + colors.reset);
    console.log(colors.lightBlue + `  初始金币: ${account.initialCoin}` + colors.reset);
    console.log(colors.lightBlue + `  最终金币: ${account.finalCoin}` + colors.reset);
    console.log(colors.lightBlue + `  金币变化: ${account.coinChange >= 0 ? '+' + account.coinChange : account.coinChange}` + colors.reset);
    console.log(colors.lightBlue + `  初始余额: ${account.initialCash}` + colors.reset);
    console.log(colors.lightBlue + `  最终余额: ${account.finalCash}` + colors.reset);
    console.log(colors.lightBlue + `  余额变化: ${account.cashChange >= 0 ? '+' + account.cashChange.toFixed(2) : account.cashChange.toFixed(2)}` + colors.reset);
    let status = account.skipped ? "跳过" : (account.coinLimitExceeded ? "超限" : (account.infoFetchFailed ? "无信息" : "完成"));
    console.log(colors.lightBlue + `  状态: ${status}` + colors.reset);
    if (account.stats) {
      console.log(colors.cyan + "  任务详情:" + colors.reset);
      Object.keys(account.stats).forEach(k => console.log(colors.lightBlue + `    ${k}: 成功=${account.stats[k].success}, 失败=${account.stats[k].failed}, 奖励=${account.stats[k].totalReward}金币` + colors.reset));
    }
  });
  console.log(colors.green + "\n========== 汇总完成 ==========" + colors.reset);
}

if (module.parent) {
  module.exports = { KuaishouAdTask };
} else {
  (async () => {
    const accounts = loadAccountsFromEnv();
    console.log(colors.cyan + `共找到 ${accounts.length} 个有效账号` + colors.reset);
    if (!accounts.length) process.exit(1);
    const maxConcurrency = getEnvNumber("MAX_CONCURRENCY", 3);
    console.log(colors.blue + `\n防黑并发：${maxConcurrency}    防黑轮数：${KSROUNDS}    look次数/轮：${KSLOOK_COUNT}    search次数/轮：${KSSEARCH_COUNT}    follow次数/look：${KSFOLLOW_COUNT}    search_follow次数/search：${KSSEARCHFOLLOW_COUNT}\n` + colors.reset);
    const results = [];
    await concurrentExecute(accounts, maxConcurrency, async (account) => {
      console.log(colors.magenta + `\n—— 🚀 开始账号[${account.index}]${account.remark ? "（" + account.remark + "）" : ""} ——` + colors.reset);
      try {
        const result = await processAccount(account);
        results.push({
          index: account.index, remark: account.remark || "无备注", nickname: result?.nickname || `账号${account.index}`,
          initialCoin: result?.initialCoin || 0, finalCoin: result?.finalCoin || 0, coinChange: result?.coinChange || 0,
          initialCash: result?.initialCash || 0, finalCash: result?.finalCash || 0, cashChange: result?.cashChange || 0,
          stats: result?.stats || {}, coinLimitExceeded: result?.coinLimitExceeded || false,
          skipped: result?.skipped || false, infoFetchFailed: result?.infoFetchFailed || false, error: result?.error || null,
        });
      } catch (error) {
        console.log(colors.red + `账号[${account.index}]${account.remark ? "（" + account.remark + "）" : ""} ❌ 执行异常：${error.message}` + colors.reset);
        results.push({ index: account.index, remark: account.remark || "无备注", nickname: `账号${account.index}`, initialCoin: 0, finalCoin: 0, coinChange: 0, initialCash: 0, finalCash: 0, cashChange: 0, error: error.message, skipped: true });
      }
    });
    results.sort((a, b) => a.index - b.index);
    console.log(colors.green + "\n✅ 全部任务已完成" + colors.reset);
    console.log(colors.blue + "\n================================ 账号信息汇总 ================================" + colors.reset);
    printAccountsSummary(results);
  })();
}

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