import httpx
import json
import os
from typing import Optional

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Star
from astrbot.api import logger, AstrBotConfig
from astrbot.core.utils.session_waiter import session_waiter, SessionController

from .ql_client import QinglongClient
from .storage import Storage

WAIT_TIMEOUT = 120

SEPARATOR_ITEMS = [
    ("newline", "\n", "换行拼接为同一个变量"),
    ("single", "single", "每个账号存为独立变量"),
    ("#", "#", "用 # 拼接"),
    ("@", "@", "用 @ 拼接"),
    ("&", "&", "用 & 拼接"),
]
SEPARATOR_MAP = {k: v for k, v, _ in SEPARATOR_ITEMS}

MAIN_MENU = (
    "1.项目列表\n"
    "2.查询\n"
    "3.管理项目\n"
    "4.新增项目（管理员使用）\n"
    "5.更新项目（管理员使用）\n"
    "6.删除项目（管理员使用）\n"
    "7.项目帮助\n"
    "输入序号（输入q退出）"
)


class QinglongEnvPlugin(Star):
    def __init__(self, context, config: AstrBotConfig = None):
        super().__init__(context)
        plugin_root = os.path.dirname(os.path.abspath(__file__))
        try:
            base = self.context.data_dir
        except AttributeError:
            base = os.path.abspath(os.path.join(plugin_root, "..", ".."))
        self.data_dir = os.path.join(base, "plugin_data", "astrbot_plugin_qinglong_env")
        self._migrate_old_data(plugin_root)
        self.storage = Storage(self.data_dir)
        self.plugin_config = config or {}
        self.ql_clients: dict[str, QinglongClient] = {}
        self._session_states: dict[str, dict] = {}
        self._init_ql_clients()

    def _init_ql_clients(self):
        instances = self.plugin_config.get("instances", [])
        if not instances:
            raw = self.plugin_config.get("instances_json", "")
            if raw:
                try:
                    instances = json.loads(raw)
                except json.JSONDecodeError:
                    instances = []
            if not isinstance(instances, list):
                instances = []

        if not instances:
            ql_url = self.plugin_config.get("ql_url", "")
            cid = self.plugin_config.get("client_id", "")
            csec = self.plugin_config.get("client_secret", "")
            if ql_url and cid and csec:
                self.ql_clients["default"] = QinglongClient(ql_url, cid, csec)
            else:
                logger.warning("青龙配置不完整，请在 WebUI 插件设置中配置")
            return

        for inst in instances:
            if not isinstance(inst, dict):
                logger.warning(f"实例配置格式异常: {inst}")
                continue
            name = inst.get("name", "default")
            ql_url = inst.get("ql_url", "")
            cid = inst.get("client_id", "")
            csec = inst.get("client_secret", "")
            if ql_url and cid and csec:
                self.ql_clients[name] = QinglongClient(ql_url, cid, csec)
            else:
                logger.warning(f"青龙实例「{name}」配置不完整")

    def _migrate_old_data(self, plugin_root: str):
        old_dir = os.path.join(plugin_root, "plugin_data")
        if not os.path.exists(old_dir):
            return
        if os.path.exists(self.data_dir):
            return
        import shutil
        shutil.copytree(old_dir, self.data_dir)
        logger.info(f"已迁移旧数据从 {old_dir} 到 {self.data_dir}")

    def _get_client(self, project_name: str = "") -> Optional[QinglongClient]:
        if not self.ql_clients:
            return None
        if project_name:
            proj = self.storage.get_project(project_name)
            if proj:
                inst = proj.get("instance_name", "")
                if inst and inst in self.ql_clients:
                    return self.ql_clients[inst]
        return next(iter(self.ql_clients.values()))

    def _get_state(self, event) -> dict:
        sid = event.get_session_id()
        if sid not in self._session_states:
            self._session_states[sid] = {"step": 0}
        return self._session_states[sid]

    def _format_project_list(self, projs: list[str]) -> str:
        grouped = {}
        for p in projs:
            proj = self.storage.get_project(p)
            inst = proj.get("instance_name", "") if proj else ""
            grouped.setdefault(inst, []).append(p)
        lines = []
        idx = 1
        for inst in sorted(grouped, key=lambda x: x or ""):
            lines.append(f"【{inst}】" if inst else "【未分配】")
            for p in grouped[inst]:
                lines.append(f" {idx}.{p}")
                idx += 1
        return "\n".join(lines)

    def _collect_all_remarks(self) -> dict:
        projs = self.storage.list_projects()
        all_remarks = {}
        for pname in projs:
            proj = self.storage.get_project(pname)
            accs = proj.get("accounts", {}) if proj else {}
            for remark in accs:
                all_remarks.setdefault(remark, []).append(pname)
        return all_remarks

    async def _sync_to_qinglong(self, project_name: str) -> bool:
        proj = self.storage.get_project(project_name)
        if not proj:
            return False
        client = self._get_client(project_name)
        if not client:
            return False

        var_name = proj["variable_name"]
        sep = proj["separator"]
        accounts = proj.get("accounts", {})
        sep_char = SEPARATOR_MAP.get(sep, sep)

        await client.delete_envs_by_name(var_name)

        if sep == "single":
            for remark, val in accounts.items():
                await client.create_env(
                    var_name, val, f"{project_name}｜{remark}"
                )
        else:
            joined = sep_char.join(accounts.values())
            if joined:
                await client.create_env(var_name, joined, f"项目：{project_name}")
        return True

    # ── 主菜单 /项目 ─────────────────────────────────────────

    @filter.command("项目")
    async def hub(self, event: AstrMessageEvent):
        self._session_states.pop(event.get_session_id(), None)
        yield event.plain_result(MAIN_MENU)

        @session_waiter(timeout=WAIT_TIMEOUT)
        async def wait(ctl, e):
            s = self._get_state(e)

            if s["step"] == 0:
                msg = e.message_str.strip()
                if msg.lower() == "q":
                    await e.send(e.plain_result("已退出"))
                    ctl.stop()
                    return
                c = {"1": 10, "2": 20, "3": 30, "4": 40, "5": 50, "6": 60, "7": 70}.get(msg)
                if c is None:
                    await e.send(e.plain_result("序号无效"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                    return
                s["step"] = c
                if c == 10:
                    projs = self.storage.list_projects()
                    if not projs:
                        await e.send(e.plain_result("暂无项目，请先使用「新增项目」创建"))
                        s["step"] = 0
                        await e.send(e.plain_result(MAIN_MENU))
                        ctl.keep(timeout=WAIT_TIMEOUT)
                        return
                    lines = self._format_project_list(projs)
                    await e.send(e.plain_result(f"项目列表：\n{lines}\n输入序号添加账号（q退出）"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                elif c == 20:
                    await e.send(e.plain_result("1.查询项目\n2.查询账号\n输入序号（q退出）"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                elif c == 30:
                    await e.send(e.plain_result("1.删除项目中的账号\n2.删除账号中的项目\n输入序号（q退出）"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                elif c == 40:
                    inst_names = list(self.ql_clients.keys())
                    if not inst_names:
                        await e.send(e.plain_result("请先在 WebUI 中配置青龙实例"))
                        s["step"] = 0
                        await e.send(e.plain_result(MAIN_MENU))
                        ctl.keep(timeout=WAIT_TIMEOUT)
                        return
                    s["inst_names"] = inst_names
                    await e.send(e.plain_result("请输入项目名称（q退出）"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                elif c == 50:
                    projs = self.storage.list_projects()
                    if not projs:
                        await e.send(e.plain_result("暂无项目"))
                        s["step"] = 0
                        await e.send(e.plain_result(MAIN_MENU))
                        ctl.keep(timeout=WAIT_TIMEOUT)
                        return
                    s["uprojs"] = projs
                    lines = self._format_project_list(projs)
                    await e.send(e.plain_result(f"选择需要更新脚本的项目：\n{lines}\n输入序号（q退出）"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                elif c == 60:
                    projs = self.storage.list_projects()
                    if not projs:
                        await e.send(e.plain_result("暂无项目"))
                        s["step"] = 0
                        await e.send(e.plain_result(MAIN_MENU))
                        ctl.keep(timeout=WAIT_TIMEOUT)
                        return
                    s["projs"] = projs
                    lines = self._format_project_list(projs)
                    await e.send(e.plain_result(f"选择要删除的项目：\n{lines}\n输入序号（0全选，q退出）"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                elif c == 70:
                    lines = "\n".join(f"{i+1}.{name} - {desc}" for i, (name, desc) in enumerate(self.HELP_ITEMS))
                    await e.send(e.plain_result(f"📖 命令列表：\n{lines}\n\n输入序号查看详细说明（q退出）"))
                    ctl.keep(timeout=WAIT_TIMEOUT)

            # ── 1.项目列表 ──
            elif s["step"] == 10:
                msg = e.message_str.strip()
                if msg.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                try:
                    s["pname"] = self.storage.list_projects()[int(msg) - 1]
                except (IndexError, ValueError):
                    await e.send(e.plain_result("序号错误")); ctl.keep(timeout=WAIT_TIMEOUT); return
                s["step"] = 11
                await e.send(e.plain_result("请输入账号备注名（q退出）"))
                ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 11:
                remark = e.message_str.strip()
                if remark.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                s["remark"] = remark; s["step"] = 12
                proj = self.storage.get_project(s["pname"])
                desc = proj.get("variable_description", "") if proj else ""
                hint = f"（{desc}）" if desc else ""
                await e.send(e.plain_result(f"请输入变量值{hint}（q退出）"))
                ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 12:
                val = e.message_str.strip()
                if val.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                self.storage.add_or_update_account(s["pname"], s["remark"], val)
                ok = await self._sync_to_qinglong(s["pname"])
                msg = "✅ 保存成功" + ("并同步青龙" if ok else "，同步青龙失败请检查配置")
                await e.send(e.plain_result(msg))
                s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT)

            # ── 2.查询 ──
            elif s["step"] == 20:
                sub = e.message_str.strip()
                if sub.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                if sub == "1":
                    projs = self.storage.list_projects()
                    if not projs:
                        await e.send(e.plain_result("暂无项目"))
                        s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                    s["qprojs"] = projs; s["step"] = 21
                    lines = self._format_project_list(projs)
                    await e.send(e.plain_result(f"选择项目：\n{lines}\n输入序号查看账号（0全部，q退出）"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                elif sub == "2":
                    all_remarks = self._collect_all_remarks()
                    if not all_remarks:
                        await e.send(e.plain_result("暂无账号"))
                        s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                    names = list(all_remarks.keys())
                    s["qremarks"] = all_remarks; s["qrnames"] = names; s["step"] = 23
                    lines = "\n".join(f"{i+1}.{r}" for i, r in enumerate(names))
                    await e.send(e.plain_result(f"账号列表：\n{lines}\n输入序号查看所属项目（0全部，q退出）"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                else:
                    await e.send(e.plain_result("序号无效")); ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 21:
                msg = e.message_str.strip()
                if msg.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                projs = s.get("qprojs", [])
                if msg == "0":
                    names = projs
                else:
                    try:
                        names = [projs[int(msg) - 1]]
                    except (IndexError, ValueError):
                        await e.send(e.plain_result("序号错误")); ctl.keep(timeout=WAIT_TIMEOUT); return
                s["step"] = 22
                parts = []
                for pname in names:
                    proj = self.storage.get_project(pname)
                    inst = proj.get("instance_name", "") if proj else ""
                    accs = proj.get("accounts", {}) if proj else {}
                    header = f"📁 {pname}" + (f"（{inst}）" if inst else "")
                    if not accs:
                        parts.append(f"{header}\n  无账号")
                    else:
                        for remark, val in accs.items():
                            parts.append(f"{header} 账号「{remark}」: {val}")
                await e.send(e.plain_result("\n".join(parts) if parts else "无数据"))
                s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 23:
                msg = e.message_str.strip()
                if msg.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                all_remarks = s.get("qremarks", {}); names = s.get("qrnames", [])
                if msg == "0":
                    selected = names
                else:
                    try:
                        selected = [names[int(msg) - 1]]
                    except (IndexError, ValueError):
                        await e.send(e.plain_result("序号错误")); ctl.keep(timeout=WAIT_TIMEOUT); return
                parts = []
                for remark in selected:
                    projects = all_remarks.get(remark, [])
                    proj_lines = "\n".join(f"  - {p}" for p in projects)
                    parts.append(f"账号「{remark}」所属项目：\n{proj_lines}")
                await e.send(e.plain_result("\n\n".join(parts)))
                s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT)

            # ── 3.管理项目 ──
            elif s["step"] == 30:
                sub = e.message_str.strip()
                if sub.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                if sub == "1":
                    projs = self.storage.list_projects()
                    if not projs:
                        await e.send(e.plain_result("暂无项目"))
                        s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                    s["mprojs"] = projs; s["step"] = 31
                    lines = self._format_project_list(projs)
                    await e.send(e.plain_result(f"选择项目：\n{lines}\n输入序号（q退出）"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                elif sub == "2":
                    all_remarks = self._collect_all_remarks()
                    if not all_remarks:
                        await e.send(e.plain_result("暂无账号"))
                        s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                    names = list(all_remarks.keys())
                    s["mremarks"] = all_remarks; s["mrnames"] = names; s["step"] = 34
                    lines = "\n".join(f"{i+1}.{r}" for i, r in enumerate(names))
                    await e.send(e.plain_result(f"账号列表：\n{lines}\n输入要删除的序号（0全选，q退出）"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                else:
                    await e.send(e.plain_result("序号无效")); ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 31:
                msg = e.message_str.strip()
                if msg.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                projs = s.get("mprojs", [])
                try:
                    s["pname"] = projs[int(msg) - 1]
                except (IndexError, ValueError):
                    await e.send(e.plain_result("序号错误")); ctl.keep(timeout=WAIT_TIMEOUT); return
                proj = self.storage.get_project(s["pname"])
                accs = proj.get("accounts", {})
                if not accs:
                    await e.send(e.plain_result("该项目无账号"))
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                s["keys"] = list(accs.keys()); s["step"] = 32
                lines = "\n".join(f"{i+1}.{k}" for i, k in enumerate(s["keys"]))
                await e.send(e.plain_result(f"账号列表：\n{lines}\n输入要删除的序号（0全选，q退出）"))
                ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 32:
                msg = e.message_str.strip()
                if msg.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                if msg == "0":
                    dkeys = list(s["keys"])
                else:
                    try:
                        dkeys = [s["keys"][int(msg) - 1]]
                    except (IndexError, ValueError):
                        await e.send(e.plain_result("序号错误")); ctl.keep(timeout=WAIT_TIMEOUT); return
                for k in dkeys:
                    self.storage.delete_account(s["pname"], k)
                await self._sync_to_qinglong(s["pname"])
                await e.send(e.plain_result(f"✅ 已删除 {len(dkeys)} 个账号并同步青龙"))
                s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 34:
                msg = e.message_str.strip()
                if msg.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                all_remarks = s.get("mremarks", {}); names = s.get("mrnames", [])
                if msg == "0":
                    selected = names
                else:
                    try:
                        selected = [names[int(msg) - 1]]
                    except (IndexError, ValueError):
                        await e.send(e.plain_result("序号错误")); ctl.keep(timeout=WAIT_TIMEOUT); return
                affected = set(); total = 0
                for remark in selected:
                    for pname in all_remarks.get(remark, []):
                        self.storage.delete_account(pname, remark)
                        affected.add(pname); total += 1
                for pname in affected:
                    await self._sync_to_qinglong(pname)
                await e.send(e.plain_result(f"✅ 已从 {len(affected)} 个项目中删除 {total} 个账号并同步青龙"))
                s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT)

            # ── 4.新增项目 ──
            elif s["step"] == 40:
                name = e.message_str.strip()
                if name.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                s["proj"] = name
                inst_names = s.get("inst_names", [])
                if len(inst_names) == 1:
                    s["inst"] = inst_names[0]; s["step"] = 42
                    await e.send(e.plain_result("请输入青龙环境变量名（如 JD_COOKIE，q退出）"))
                else:
                    s["step"] = 41
                    lines = "\n".join(f"{i+1}.{n}" for i, n in enumerate(inst_names))
                    await e.send(e.plain_result(f"选择青龙实例：\n{lines}\n输入序号（q退出）"))
                ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 41:
                msg = e.message_str.strip()
                if msg.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                inst_names = s.get("inst_names", [])
                try:
                    s["inst"] = inst_names[int(msg) - 1]
                except (IndexError, ValueError):
                    await e.send(e.plain_result("序号错误")); ctl.keep(timeout=WAIT_TIMEOUT); return
                s["step"] = 42
                await e.send(e.plain_result("请输入青龙环境变量名（如 JD_COOKIE，q退出）"))
                ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 42:
                var = e.message_str.strip()
                if var.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                s["var"] = var; s["step"] = 43
                await e.send(e.plain_result("请输入变量描述，如「抓 authorization 里的值」（q退出）"))
                ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 43:
                desc = e.message_str.strip()
                if desc.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                s["desc"] = desc; s["step"] = 44
                lines = "\n".join(f"{i+1}.{name} - {desc}" for i, (name, _, desc) in enumerate(SEPARATOR_ITEMS))
                await e.send(e.plain_result(f"选择分隔符：\n{lines}\n输入序号（q退出）"))
                ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 44:
                msg = e.message_str.strip()
                if msg.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                try:
                    sep = SEPARATOR_ITEMS[int(msg) - 1][0]
                except (IndexError, ValueError):
                    await e.send(e.plain_result("序号无效")); ctl.keep(timeout=WAIT_TIMEOUT); return
                self.storage.save_project(s["proj"], s["var"], sep, s["inst"], s.get("desc", ""))
                await e.send(e.plain_result(f"✅ 项目「{s['proj']}」创建成功"))
                s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT)

            # ── 5.更新项目 ──
            elif s["step"] == 50:
                msg = e.message_str.strip()
                if msg.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                projs = s.get("uprojs", [])
                try:
                    s["upname"] = projs[int(msg) - 1]
                except (IndexError, ValueError):
                    await e.send(e.plain_result("序号错误")); ctl.keep(timeout=WAIT_TIMEOUT); return
                s["step"] = 51
                await e.send(e.plain_result("请输入脚本内容或 GitHub raw URL\n发 raw URL 自动下载，直接贴代码也行\n（输入q退出）"))
                ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 51:
                inp = e.message_str.strip()
                if inp.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                pname = s.get("upname", "")
                proj = self.storage.get_project(pname)
                if not proj:
                    await e.send(e.plain_result(f"项目「{pname}」不存在"))
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                var_name = proj.get("variable_name", pname)
                if inp.startswith(("http://", "https://")):
                    try:
                        async with httpx.AsyncClient(timeout=30) as http_client:
                            resp = await http_client.get(inp)
                            if resp.status_code != 200:
                                await e.send(e.plain_result(f"下载失败，HTTP {resp.status_code}"))
                                s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                            content = resp.text
                    except Exception as exc:
                        await e.send(e.plain_result(f"下载失败：{exc}"))
                        s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                else:
                    content = inp
                filename = var_name + self._detect_extension(content)
                client = self._get_client(pname)
                if not client:
                    await e.send(e.plain_result("青龙实例不可用"))
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                ok = await client.create_or_update_script(filename, content)
                if ok:
                    await e.send(e.plain_result(f"✅ 脚本「{filename}」已更新到青龙"))
                else:
                    await e.send(e.plain_result("❌ 脚本上传失败，请检查青龙面板状态"))
                s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT)

            # ── 6.删除项目 ──
            elif s["step"] == 60:
                msg = e.message_str.strip()
                if msg.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                projs = s.get("projs", [])
                if msg == "0":
                    dprojs = list(projs)
                else:
                    try:
                        dprojs = [projs[int(msg) - 1]]
                    except (IndexError, ValueError):
                        await e.send(e.plain_result("序号错误")); ctl.keep(timeout=WAIT_TIMEOUT); return
                for pname in dprojs:
                    self.storage.delete_project(pname)
                names = "、".join(dprojs)
                await e.send(e.plain_result(f"✅ 已删除项目「{names}」"))
                s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT)

            # ── 7.项目帮助 ──
            elif s["step"] == 70:
                msg = e.message_str.strip()
                if msg.lower() == "q":
                    s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT); return
                try:
                    idx = int(msg) - 1
                    name = self.HELP_ITEMS[idx][0]
                except (IndexError, ValueError):
                    await e.send(e.plain_result("序号错误")); ctl.keep(timeout=WAIT_TIMEOUT); return
                detail = self._get_help_detail(name)
                await e.send(e.plain_result(f"📘 {name}\n{detail}"))
                s["step"] = 0; await e.send(e.plain_result(MAIN_MENU)); ctl.keep(timeout=WAIT_TIMEOUT)

        try:
            await wait(event)
        except TimeoutError:
            yield event.plain_result("输入超时，已退出")

    HELP_ITEMS = [
        ("新增项目", "创建一个新的环境变量项目，包含项目名称、变量名、分隔符"),
        ("项目列表", "查看已有项目及其所属青龙实例，并添加账号"),
        ("查询", "查询项目下的账号、或账号所属的项目"),
        ("管理项目", "删除项目中的账号，或从所有项目中删除指定账号（支持全选）"),
        ("更新项目", "更新青龙面板中对应项目的脚本，支持 URL 下载和直接贴代码"),
        ("删除项目", "删除整个项目及其所有账号数据（支持全选）"),
    ]

    async def _hub_help_menu(self, ctl, e):
        s = self._get_state(e)
        msg = e.message_str.strip() if s["step"] == 70 else None
        if msg is None:
            lines = "\n".join(f"{i + 1}.{name} - {desc}" for i, (name, desc) in enumerate(self.HELP_ITEMS))
            await e.send(e.plain_result(f"📖 命令列表：\n{lines}\n\n输入序号查看详细说明（q退出）"))
            s["step"] = 70
            ctl.keep(timeout=WAIT_TIMEOUT)
            return
        if msg.lower() == "q":
            await self._back_to_menu(ctl, e)
            return
        try:
            idx = int(msg) - 1
            name = self.HELP_ITEMS[idx][0]
        except (IndexError, ValueError):
            await e.send(e.plain_result("序号错误"))
            ctl.keep(timeout=WAIT_TIMEOUT)
            return
        s["step"] = 71
        detail = self._get_help_detail(name)
        await e.send(e.plain_result(f"📘 {name}\n{detail}"))
        await self._back_to_menu(ctl, e)

    async def _hub_help_detail(self, ctl, e):
        # handled in _hub_help_menu
        pass

    @staticmethod
    def _detect_extension(content: str) -> str:
        s = content.strip()
        if s.startswith(("import ", "from ", "def ", "class ", "#!", "#!/")) or "if __name__" in s:
            return ".py"
        return ".js"

    @staticmethod
    def _get_help_detail(name: str) -> str:
        details = {
            "新增项目":
                "创建一个青龙环境变量项目。\n"
                "交互流程：\n"
                " 1. 输入项目名称\n"
                " 2. 选择青龙实例（多实例时）\n"
                " 3. 输入青龙环境变量名（如 JD_COOKIE）\n"
                " 4. 输入变量描述（如「抓 authorization 里的值」）\n"
                " 5. 选择分隔符（输入序号）\n"
                "   1.newline - 换行拼接\n"
                "   2.single - 独立变量\n"
                "   3.# - 用 # 拼接\n"
                "   4.@ - 用 @ 拼接\n"
                "   5.& - 用 & 拼接",
            "项目列表":
                "查看所有项目（按青龙实例分组显示）。\n"
                "选中项目后可添加账号：\n"
                " 1. 输入项目序号\n"
                " 2. 输入账号备注名（如 账号1）\n"
                " 3. 输入变量值（提示中会附带变量描述）\n\n"
                "保存后自动同步到青龙面板",
            "查询":
                "包含两种查询方式：\n"
                " 1.查询项目 — 查看项目下所有的账号及变量值\n"
                " 2.查询账号 — 查看某个账号备注名出现在哪些项目中\n\n"
                "支持输入 0 查看全部",
            "管理项目":
                "包含两种删除方式：\n"
                " 1.删除项目中的账号 — 进入项目后选择要删除的账号\n"
                " 2.删除账号中的项目 — 从所有项目中删除指定备注名的账号\n\n"
                "支持输入 0 全选，删除后自动同步青龙面板",
            "更新项目":
                "更新青龙面板中对应项目的脚本。\n"
                "交互流程：\n"
                " 1. 选择需要更新脚本的项目\n"
                " 2. 输入脚本内容（直接贴代码）或 GitHub raw URL\n"
                " 3. 插件自动上传/更新到青龙面板\n\n"
                "URL 模式：发 https://raw.githubusercontent.com/... 链接\n"
                "代码模式：直接粘贴脚本代码（注意 QQ 有 2000 字限制）",
            "删除项目":
                "删除整个项目及其所有账号数据。\n"
                "交互流程：\n"
                " 1. 选择要删除的项目序号（或输入 0 全选）\n"
                " 2. 确认后项目及所有账号被永久删除\n\n"
                "输入 q 退出，输入 0 全选",
        }
        return details.get(name, "暂无详细说明")

    # ── 直接指令（Option B：无需经过主菜单） ─────────────────

    @filter.command("新增项目")
    async def add_project(self, event: AstrMessageEvent):
        self._session_states.pop(event.get_session_id(), None)
        inst_names = list(self.ql_clients.keys())
        if not inst_names:
            yield event.plain_result("请先在 WebUI 中配置青龙实例")
            return
        yield event.plain_result("请输入项目名称（输入q退出）")

        @session_waiter(timeout=WAIT_TIMEOUT)
        async def wait(ctl, e):
            s = self._get_state(e)

            if s["step"] == 0:
                name = e.message_str.strip()
                if name.lower() == "q":
                    await e.send(e.plain_result("已退出"))
                    ctl.stop()
                    return
                s["proj"] = name
                if len(inst_names) == 1:
                    s["inst"] = inst_names[0]
                    s["step"] = 2
                    await e.send(e.plain_result("请输入青龙环境变量名（如 JD_COOKIE，输入q退出）"))
                else:
                    s["step"] = 1
                    lines = "\n".join(f"{i+1}.{n}" for i, n in enumerate(inst_names))
                    await e.send(e.plain_result(f"选择青龙实例：\n{lines}\n输入序号（输入q退出）"))
                ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 1:
                msg = e.message_str.strip()
                if msg.lower() == "q":
                    await e.send(e.plain_result("已退出"))
                    ctl.stop()
                    return
                try:
                    s["inst"] = inst_names[int(msg) - 1]
                except (IndexError, ValueError):
                    await e.send(e.plain_result("序号错误"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                    return
                s["step"] = 2
                await e.send(e.plain_result("请输入青龙环境变量名（如 JD_COOKIE，输入q退出）"))
                ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 2:
                var = e.message_str.strip()
                if var.lower() == "q":
                    await e.send(e.plain_result("已退出"))
                    ctl.stop()
                    return
                s["var"] = var
                s["step"] = 3
                await e.send(e.plain_result("请输入变量描述，如「抓 authorization 里的值」（输入q退出）"))
                ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 3:
                desc = e.message_str.strip()
                if desc.lower() == "q":
                    await e.send(e.plain_result("已退出"))
                    ctl.stop()
                    return
                s["desc"] = desc
                s["step"] = 4
                lines = "\n".join(f"{i+1}.{name} - {desc}" for i, (name, _, desc) in enumerate(SEPARATOR_ITEMS))
                await e.send(e.plain_result(f"选择分隔符：\n{lines}\n输入序号（q退出）"))
                ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 4:
                msg = e.message_str.strip()
                if msg.lower() == "q":
                    await e.send(e.plain_result("已退出"))
                    ctl.stop()
                    return
                try:
                    sep = SEPARATOR_ITEMS[int(msg) - 1][0]
                except (IndexError, ValueError):
                    await e.send(e.plain_result("序号无效"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                    return
                self.storage.save_project(s["proj"], s["var"], sep, s["inst"], s.get("desc", ""))
                await e.send(e.plain_result(f"✅ 项目「{s['proj']}」创建成功"))
                ctl.stop()

        try:
            await wait(event)
        except TimeoutError:
            yield event.plain_result("输入超时，已退出")

    @filter.command("删除项目")
    async def delete_project(self, event: AstrMessageEvent):
        self._session_states.pop(event.get_session_id(), None)
        projs = self.storage.list_projects()
        if not projs:
            yield event.plain_result("暂无项目")
            return
        lines = self._format_project_list(projs)
        yield event.plain_result(f"项目列表：\n{lines}\n输入要删除的项目序号（0全选，q退出）")

        @session_waiter(timeout=WAIT_TIMEOUT)
        async def wait(ctl, e):
            msg = e.message_str.strip()
            if msg.lower() == "q":
                await e.send(e.plain_result("已退出"))
                ctl.stop()
                return
            if msg == "0":
                for p in projs:
                    self.storage.delete_project(p)
                await e.send(e.plain_result("✅ 已删除全部项目"))
                ctl.stop()
                return
            try:
                pname = projs[int(msg) - 1]
            except (IndexError, ValueError):
                await e.send(e.plain_result("序号错误"))
                ctl.keep(timeout=WAIT_TIMEOUT)
                return
            self.storage.delete_project(pname)
            await e.send(e.plain_result(f"✅ 项目「{pname}」已删除"))
            ctl.stop()

        try:
            await wait(event)
        except TimeoutError:
            yield event.plain_result("输入超时，已退出")

    @filter.command("更新项目")
    async def update_project(self, event: AstrMessageEvent):
        self._session_states.pop(event.get_session_id(), None)
        projs = self.storage.list_projects()
        if not projs:
            yield event.plain_result("暂无项目")
            return
        lines = self._format_project_list(projs)
        yield event.plain_result(f"选择需要更新脚本的项目：\n{lines}\n输入序号（q退出）")

        @session_waiter(timeout=WAIT_TIMEOUT)
        async def wait(ctl, e):
            s = self._get_state(e)

            if s["step"] == 0:
                msg = e.message_str.strip()
                if msg.lower() == "q":
                    await e.send(e.plain_result("已退出"))
                    ctl.stop()
                    return
                try:
                    s["upname"] = projs[int(msg) - 1]
                except (IndexError, ValueError):
                    await e.send(e.plain_result("序号错误"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                    return
                s["step"] = 10
                await e.send(e.plain_result("请输入脚本内容或 GitHub raw URL\n发 raw URL 自动下载，直接贴代码也行\n（输入q退出）"))
                ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 10:
                inp = e.message_str.strip()
                if inp.lower() == "q":
                    await e.send(e.plain_result("已退出"))
                    ctl.stop()
                    return
                pname = s.get("upname", "")
                proj = self.storage.get_project(pname)
                if not proj:
                    await e.send(e.plain_result(f"项目「{pname}」不存在"))
                    ctl.stop()
                    return
                var_name = proj.get("variable_name", pname)
                if inp.startswith(("http://", "https://")):
                    try:
                        async with httpx.AsyncClient(timeout=30) as http_client:
                            resp = await http_client.get(inp)
                            if resp.status_code != 200:
                                await e.send(e.plain_result(f"下载失败，HTTP {resp.status_code}"))
                                ctl.stop()
                                return
                            content = resp.text
                    except Exception as exc:
                        await e.send(e.plain_result(f"下载失败：{exc}"))
                        ctl.stop()
                        return
                else:
                    content = inp
                filename = var_name + self._detect_extension(content)
                client = self._get_client(pname)
                if not client:
                    await e.send(e.plain_result("青龙实例不可用"))
                    ctl.stop()
                    return
                ok = await client.create_or_update_script(filename, content)
                if ok:
                    await e.send(e.plain_result(f"✅ 脚本「{filename}」已更新到青龙"))
                else:
                    await e.send(e.plain_result("❌ 脚本上传失败，请检查青龙面板状态"))
                ctl.stop()

        try:
            await wait(event)
        except TimeoutError:
            yield event.plain_result("输入超时，已退出")

    @filter.command("项目帮助")
    async def project_help(self, event: AstrMessageEvent):
        lines = "\n".join(f"{i + 1}.{name} - {desc}" for i, (name, desc) in enumerate(self.HELP_ITEMS))
        yield event.plain_result(f"📖 命令列表：\n{lines}\n\n输入序号查看详细说明（输入q退出）")

        @session_waiter(timeout=WAIT_TIMEOUT)
        async def wait(ctl, e):
            msg = e.message_str.strip()
            if msg.lower() == "q":
                await e.send(e.plain_result("已退出"))
                ctl.stop()
                return
            try:
                idx = int(msg) - 1
                name = self.HELP_ITEMS[idx][0]
            except (IndexError, ValueError):
                await e.send(e.plain_result("序号错误"))
                ctl.keep(timeout=WAIT_TIMEOUT)
                return
            detail = self._get_help_detail(name)
            await e.send(e.plain_result(f"📘 {name}\n{detail}"))
            ctl.stop()

        try:
            await wait(event)
        except TimeoutError:
            yield event.plain_result("输入超时，已退出")

    @filter.command("管理项目")
    async def manage_project(self, event: AstrMessageEvent):
        self._session_states.pop(event.get_session_id(), None)
        yield event.plain_result("1.删除项目中的账号\n2.删除账号中的项目\n输入序号（q退出）")

        @session_waiter(timeout=WAIT_TIMEOUT)
        async def wait(ctl, e):
            s = self._get_state(e)
            msg = e.message_str.strip()

            # ── 子菜单 ──
            if s["step"] == 0:
                if msg.lower() == "q":
                    await e.send(e.plain_result("已退出"))
                    ctl.stop()
                    return
                if msg == "1":
                    projs = self.storage.list_projects()
                    if not projs:
                        await e.send(e.plain_result("暂无项目"))
                        ctl.stop()
                        return
                    s["m_projs"] = projs
                    s["step"] = 10
                    lines = self._format_project_list(projs)
                    await e.send(e.plain_result(f"选择项目：\n{lines}\n输入序号（q退出）"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                elif msg == "2":
                    all_remarks = self._collect_all_remarks()
                    if not all_remarks:
                        await e.send(e.plain_result("暂无账号"))
                        ctl.stop()
                        return
                    names = list(all_remarks.keys())
                    s["m_remarks"] = all_remarks
                    s["m_rnames"] = names
                    s["step"] = 20
                    lines = "\n".join(f"{i + 1}.{r}" for i, r in enumerate(names))
                    await e.send(e.plain_result(f"账号列表：\n{lines}\n输入要删除的序号（0全选，q退出）"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                else:
                    await e.send(e.plain_result("序号无效"))
                    ctl.keep(timeout=WAIT_TIMEOUT)

            # ── 1.删除项目中的账号 ──
            elif s["step"] == 10:
                if msg.lower() == "q":
                    await e.send(e.plain_result("已退出"))
                    ctl.stop()
                    return
                projs = s.get("m_projs", [])
                try:
                    s["m_pname"] = projs[int(msg) - 1]
                except (IndexError, ValueError):
                    await e.send(e.plain_result("序号错误"))
                    ctl.keep(timeout=WAIT_TIMEOUT)
                    return
                proj = self.storage.get_project(s["m_pname"])
                accs = proj.get("accounts", {})
                if not accs:
                    await e.send(e.plain_result("该项目无账号"))
                    ctl.stop()
                    return
                s["m_keys"] = list(accs.keys())
                s["step"] = 11
                lines = "\n".join(f"{i + 1}.{k}" for i, k in enumerate(s["m_keys"]))
                await e.send(e.plain_result(f"账号列表：\n{lines}\n输入要删除的序号（0全选，q退出）"))
                ctl.keep(timeout=WAIT_TIMEOUT)

            elif s["step"] == 11:
                if msg.lower() == "q":
                    await e.send(e.plain_result("已退出"))
                    ctl.stop()
                    return
                if msg == "0":
                    dkeys = list(s["m_keys"])
                else:
                    try:
                        dkeys = [s["m_keys"][int(msg) - 1]]
                    except (IndexError, ValueError):
                        await e.send(e.plain_result("序号错误"))
                        ctl.keep(timeout=WAIT_TIMEOUT)
                        return
                for k in dkeys:
                    self.storage.delete_account(s["m_pname"], k)
                await self._sync_to_qinglong(s["m_pname"])
                await e.send(e.plain_result(f"✅ 已删除 {len(dkeys)} 个账号并同步青龙"))
                ctl.stop()

            # ── 2.删除账号中的项目 ──
            elif s["step"] == 20:
                if msg.lower() == "q":
                    await e.send(e.plain_result("已退出"))
                    ctl.stop()
                    return
                all_remarks = s.get("m_remarks", {})
                names = s.get("m_rnames", [])
                if msg == "0":
                    selected = names
                else:
                    try:
                        selected = [names[int(msg) - 1]]
                    except (IndexError, ValueError):
                        await e.send(e.plain_result("序号错误"))
                        ctl.keep(timeout=WAIT_TIMEOUT)
                        return
                affected = set()
                total = 0
                for remark in selected:
                    projects = all_remarks.get(remark, [])
                    for pname in projects:
                        self.storage.delete_account(pname, remark)
                        affected.add(pname)
                        total += 1
                for pname in affected:
                    await self._sync_to_qinglong(pname)
                await e.send(e.plain_result(f"✅ 已从 {len(affected)} 个项目中删除 {total} 个账号并同步青龙"))
                ctl.stop()

        try:
            await wait(event)
        except TimeoutError:
            yield event.plain_result("输入超时，已退出")

    @filter.command("项目列表")
    async def list_projects(self, event: AstrMessageEvent):
        projs = self.storage.list_projects()
        if not projs:
            yield event.plain_result("暂无项目")
            return
        yield event.plain_result(self._format_project_list(projs))

    @filter.command("查询")
    async def query(self, event: AstrMessageEvent):
        self._session_states.pop(event.get_session_id(), None)
        yield event.plain_result("1.查询项目\n2.查询账号\n输入序号（q退出）")

        @session_waiter(timeout=WAIT_TIMEOUT)
        async def wait(ctl, e):
            msg = e.message_str.strip()
            if msg.lower() == "q":
                await e.send(e.plain_result("已退出"))
                ctl.stop()
                return
            if msg == "1":
                projs = self.storage.list_projects()
                if not projs:
                    await e.send(e.plain_result("暂无项目"))
                    ctl.stop()
                    return
                lines = self._format_project_list(projs)
                await e.send(e.plain_result(f"选择项目：\n{lines}\n输入序号查看账号（0全部，q退出）"))
                ctl.keep(timeout=WAIT_TIMEOUT)

                @session_waiter(timeout=WAIT_TIMEOUT)
                async def qproj(ctl2, e2):
                    m = e2.message_str.strip()
                    if m.lower() == "q":
                        await e2.send(e2.plain_result("已退出"))
                        ctl2.stop()
                        return
                    if m == "0":
                        names = projs
                    else:
                        try:
                            names = [projs[int(m) - 1]]
                        except (IndexError, ValueError):
                            await e2.send(e2.plain_result("序号错误"))
                            ctl2.keep(timeout=WAIT_TIMEOUT)
                            return
                    parts = []
                    for pname in names:
                        proj = self.storage.get_project(pname)
                        inst = proj.get("instance_name", "") if proj else ""
                        accs = proj.get("accounts", {}) if proj else {}
                        header = f"📁 {pname}" + (f"（{inst}）" if inst else "")
                        if not accs:
                            parts.append(f"{header}\n  无账号")
                        else:
                            for remark, val in accs.items():
                                parts.append(f"{header} 账号「{remark}」: {val}")
                    await e2.send(e2.plain_result("\n".join(parts) if parts else "无数据"))
                    ctl2.stop()

                try:
                    await qproj(e)
                except TimeoutError:
                    await e.send(e.plain_result("输入超时，已退出"))

            elif msg == "2":
                all_remarks = self._collect_all_remarks()
                if not all_remarks:
                    await e.send(e.plain_result("暂无账号"))
                    ctl.stop()
                    return
                names = list(all_remarks.keys())
                lines = "\n".join(f"{i + 1}.{r}" for i, r in enumerate(names))
                await e.send(e.plain_result(f"账号列表：\n{lines}\n输入序号查看所属项目（0全部，q退出）"))
                ctl.keep(timeout=WAIT_TIMEOUT)

                @session_waiter(timeout=WAIT_TIMEOUT)
                async def qacct(ctl2, e2):
                    m = e2.message_str.strip()
                    if m.lower() == "q":
                        await e2.send(e2.plain_result("已退出"))
                        ctl2.stop()
                        return
                    if m == "0":
                        selected = names
                    else:
                        try:
                            selected = [names[int(m) - 1]]
                        except (IndexError, ValueError):
                            await e2.send(e2.plain_result("序号错误"))
                            ctl2.keep(timeout=WAIT_TIMEOUT)
                            return
                    parts = []
                    for remark in selected:
                        projects = all_remarks[remark]
                        proj_lines = "\n".join(f"  - {p}" for p in projects)
                        parts.append(f"账号「{remark}」所属项目：\n{proj_lines}")
                    await e2.send(e2.plain_result("\n\n".join(parts)))
                    ctl2.stop()

                try:
                    await qacct(e)
                except TimeoutError:
                    await e.send(e.plain_result("输入超时，已退出"))

            else:
                await e.send(e.plain_result("序号无效"))
                ctl.keep(timeout=WAIT_TIMEOUT)

        try:
            await wait(event)
        except TimeoutError:
            yield event.plain_result("输入超时，已退出")
