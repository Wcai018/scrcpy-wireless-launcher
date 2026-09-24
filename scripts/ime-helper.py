#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
输入法助手 —— 诊断投屏时的输入法状态。

⚠️ 2026-09-25 勘误：本脚本的 `guard` 子命令**基于已被证伪的前提**。
------------------------------------------------------------------
本脚本最初假设：「电脑输入法处于中文态 → 中文被丢弃 → 必须把电脑输入法
自动切成英文（直接输入）才能打字」。

**后续真机实测推翻了这个前提。** 正确做法是给 scrcpy 加 `--keyboard=uhid`
（v1.2.0 起启动器已默认加），此时：
  - 电脑按键以「物理键盘」身份进手机，走按键通路，不经过 INJECT_TEXT
  - 中文由**手机输入法**照着拼音组词，电脑输入法保持英文即可，**不需要改它**
  - 实测：B 站搜索框用「电脑英文 + 敲拼音」成功打出中文

所以 `guard`（自动改你的输入法状态）**不再需要，也不建议使用** ——
它会去改用户的输入法，而问题其实不需要那样解决。

保留本文件的原因：`check` 子命令的诊断输出（电脑键盘布局、手机输入法列表）
仍然有用，可用于排查环境问题。`guard` 保留仅为历史记录。

官方说明以根目录 README.md 的「键盘输入：电脑上直接打中文」一节为准。

---- 以下为原文（含已被证伪的假设），保留作过程记录 ----
"""
"""
输入法助手 —— 解决「投屏后电脑打字进不了手机」的输入法问题。

背景（这是本脚本存在的唯一理由）
--------------------------------
scrcpy 在电脑上敲键盘时，会走两条不同的通路：

  1. 按键通路 INJECT_KEYCODE —— 单个按键的 keycode 发给手机。
     手机自己的输入法收到 n-i-h-a-o，组词成「你好」。中文能出。

  2. 文字通路 INJECT_TEXT —— 一段已经组好的文字发给手机。
     服务端用 KeyCharacterMap.getEvents() 转按键，而这张表只覆盖 ASCII。
     中文字符返回 null，代码里直接 continue 跳过，只留一行 warning。

哪条通路会被用到，取决于**电脑输入法当前是中文模式还是直接输入模式**：

  - 电脑输入法处于「中文」→ 输入法先把字组好 → 走通路 2 → 中文被丢弃
  - 电脑输入法处于「直接输入」→ 原始按键透传 → 走通路 1 → 中文正常

所以「输入法不同会影响能否打字」这个用户反馈是对的，而且根因很具体。

本脚本做两件事
--------------
  check  诊断：报告电脑和手机两侧的输入法状态，给出结论和建议
  guard  守护：投屏期间自动把电脑输入法切到「直接输入」，退出时还原

用法
----
    python 输入法助手.py check
    python 输入法助手.py check --adb D:\\Wcai\\scrcpy\\adb.exe
    python 输入法助手.py guard
    python 输入法助手.py guard --process scrcpy.exe --poll 0.3
    python 输入法助手.py guard --dry-run      ← 只看会做什么，不改输入法状态

验证建议：先用 `guard --dry-run` 跑一遍，确认它认得出投屏窗口、
也读得到输入法状态，再正式启用。这样不会出现「莫名其妙输入法被改了」。

诚实说明（别当成一定能用）
--------------------------
自动切换依赖 IME 响应 WM_IME_CONTROL / IMC_SETCONVERSIONMODE。
微软拼音、微软五笔这类系统 IME 支持；部分第三方输入法（搜狗、QQ 拼音等）
可能不响应。本脚本的做法是：**切换后一定回读验证**，切不动就明确告诉你
「这个输入法不支持自动切换」，而不是假装成功。

注意：本脚本仅在 Windows + 简体中文环境实测过，其他环境未验证。
"""
from __future__ import annotations

import argparse
import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes

# ---------------------------------------------------------------------------
# 控制台编码兜底
# ---------------------------------------------------------------------------
# 调用方（启动器.bat）会设 PYTHONIOENCODING=gbk 对齐 cmd 控制台；
# 直接运行本脚本时没有这个变量，则按 UTF-8 输出。
# 若代码页不匹配，宁可把个别字显示成 '?' 也不抛异常中断诊断 ——
# 这里只是提示文字，不是数据。
try:
    sys.stdout.reconfigure(errors="replace")
except (AttributeError, OSError):
    pass

IS_WINDOWS = os.name == "nt"


# ---------------------------------------------------------------------------
# Windows IME 常量
# ---------------------------------------------------------------------------
WM_IME_CONTROL = 0x0283
IMC_GETCONVERSIONMODE = 0x0001
IMC_SETCONVERSIONMODE = 0x0002

# IME 转换模式位
IME_CMODE_NATIVE = 0x0001        # 母语输入（中文/日文/韩文）—— 关键位
IME_CMODE_KATAKANA = 0x0002
IME_CMODE_FULLSHAPE = 0x0008     # 全角
IME_CMODE_ROMAN = 0x0010

# 低字为 LANGID。列出会影响打字结果的 CJK 语言。
CJK_LANGIDS = {
    0x0804: "中文（简体，中国）",
    0x0404: "中文（中国台湾）",
    0x0C04: "中文（中国香港）",
    0x1004: "中文（新加坡）",
    0x0411: "日语",
    0x0412: "韩语",
}

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


class WinIME:
    """把用到的 Win32 调用收在一处，顺便把签名写对（64 位下 HWND 是指针）。"""

    def __init__(self) -> None:
        if not IS_WINDOWS:
            raise RuntimeError("本模块仅支持 Windows")
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        try:
            self.imm32 = ctypes.WinDLL("imm32", use_last_error=True)
        except OSError as e:  # 极少数精简系统没有 imm32
            raise RuntimeError(f"加载 imm32.dll 失败：{e}") from e

        u, k, i = self.user32, self.kernel32, self.imm32

        u.GetForegroundWindow.restype = wintypes.HWND
        u.GetForegroundWindow.argtypes = []

        u.GetWindowThreadProcessId.restype = wintypes.DWORD
        u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]

        u.GetKeyboardLayout.restype = wintypes.HKL
        u.GetKeyboardLayout.argtypes = [wintypes.DWORD]

        u.GetKeyboardLayoutList.restype = ctypes.c_int
        u.GetKeyboardLayoutList.argtypes = [ctypes.c_int, ctypes.POINTER(wintypes.HKL)]

        u.GetKeyboardLayoutNameW.restype = wintypes.BOOL
        u.GetKeyboardLayoutNameW.argtypes = [wintypes.LPWSTR]

        u.SendMessageW.restype = ctypes.c_ulong
        u.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]

        u.EnumWindows.restype = wintypes.BOOL
        u.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]

        u.IsWindowVisible.restype = wintypes.BOOL
        u.IsWindowVisible.argtypes = [wintypes.HWND]

        u.IsWindow.restype = wintypes.BOOL
        u.IsWindow.argtypes = [wintypes.HWND]

        i.ImmGetDefaultIMEWnd.restype = wintypes.HWND
        i.ImmGetDefaultIMEWnd.argtypes = [wintypes.HWND]

        k.OpenProcess.restype = wintypes.HANDLE
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]

        k.QueryFullProcessImageNameW.restype = wintypes.BOOL
        k.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
        ]

        k.CloseHandle.restype = wintypes.BOOL
        k.CloseHandle.argtypes = [wintypes.HANDLE]

    # ---- 窗口 ----------------------------------------------------------

    def foreground_window(self):
        return self.user32.GetForegroundWindow()

    def is_window(self, hwnd) -> bool:
        return bool(hwnd) and bool(self.user32.IsWindow(hwnd))

    def enum_visible_windows(self):
        out = []

        def cb(hwnd, _):
            if self.user32.IsWindowVisible(hwnd):
                out.append(hwnd)
            return True

        self.user32.EnumWindows(WNDENUMPROC(cb), 0)
        return out

    def window_pid(self, hwnd):
        pid = wintypes.DWORD()
        self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value or None

    def process_name(self, pid):
        """返回进程可执行文件名（小写），拿不到返回 None。"""
        if not pid:
            return None
        h = self.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h:
            return None
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(len(buf))
            if self.kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                return os.path.basename(buf.value).lower()
        finally:
            self.kernel32.CloseHandle(h)
        return None

    # ---- 键盘布局 ------------------------------------------------------

    def layout_langid(self, hwnd=None):
        """取窗口所属线程的键盘布局语言 ID。hwnd 为空则取调用线程。"""
        if hwnd:
            tid = self.user32.GetWindowThreadProcessId(hwnd, None)
        else:
            tid = 0
        hkl = self.user32.GetKeyboardLayout(tid)
        return hkl & 0xFFFF, hkl

    def installed_layouts(self):
        n = self.user32.GetKeyboardLayoutList(0, None)
        if n <= 0:
            return []
        arr = (wintypes.HKL * n)()
        self.user32.GetKeyboardLayoutList(n, arr)
        return [(h & 0xFFFF, h) for h in arr]

    # ---- IME 转换模式 --------------------------------------------------

    def ime_window(self, hwnd):
        return self.imm32.ImmGetDefaultIMEWnd(hwnd)

    def get_conversion_mode(self, hwnd):
        """返回 (mode, 是否中文模式)；拿不到返回 (None, None)。"""
        wnd = self.ime_window(hwnd)
        if not wnd:
            return None, None
        mode = self.user32.SendMessageW(wnd, WM_IME_CONTROL, IMC_GETCONVERSIONMODE, 0)
        return mode, bool(mode & IME_CMODE_NATIVE)

    def set_conversion_mode(self, hwnd, mode) -> bool:
        wnd = self.ime_window(hwnd)
        if not wnd:
            return False
        self.user32.SendMessageW(wnd, WM_IME_CONTROL, IMC_SETCONVERSIONMODE, mode)
        return True


# ---------------------------------------------------------------------------
# 手机侧：通过 adb 读输入法状态
# ---------------------------------------------------------------------------
def run_adb(adb, args, timeout=8):
    """返回 (ok, stdout)。adb 的输出可能是 UTF-8 也可能是 GBK，统一宽松解码。"""
    try:
        r = subprocess.run(
            [adb] + list(args),
            capture_output=True, timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except FileNotFoundError:
        return False, f"找不到 adb：{adb}"
    except subprocess.TimeoutExpired:
        return False, "adb 命令超时"
    out = (r.stdout or b"").decode("utf-8", "replace")
    err = (r.stderr or b"").decode("utf-8", "replace")
    if r.returncode != 0 and not out.strip():
        return False, err.strip() or f"adb 退出码 {r.returncode}"
    return True, out


def find_connected_device(adb):
    """返回第一个状态为 device 的设备序列号。"""
    ok, out = run_adb(adb, ["devices"])
    if not ok:
        return None, out
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            return parts[0], None
    return None, "没有已连接（状态为 device）的设备"


def probe_phone(adb, serial):
    """读手机的输入法信息。全部失败不抛异常，如实返回。"""
    info = {}

    ok, out = run_adb(adb, ["-s", serial, "shell", "settings", "get", "secure", "default_input_method"])
    info["default_ime"] = out.strip() if ok else None

    ok, out = run_adb(adb, ["-s", serial, "shell", "ime", "list", "-s"])
    if ok:
        info["available"] = [l.strip() for l in out.splitlines() if l.strip()]
    else:
        info["available"] = []

    # 系统里有没有启用的输入法：没有的话按键收到了也出不了字
    ok, out = run_adb(adb, ["-s", serial, "shell", "ime", "list", "-s", "--user", "0"])
    info["enabled"] = [l.strip() for l in out.splitlines() if l.strip()] if ok else []

    return info


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------
def cmd_check(args):
    print()
    print("  ==========================================")
    print("     输入法诊断")
    print("  ==========================================")
    print()

    if not IS_WINDOWS:
        print("  [X] 本脚本目前只支持 Windows。")
        print()
        return 2

    ime = WinIME()
    verdict = []       # 结论行
    problems = []      # 需要用户处理的问题

    # ---------- 电脑侧 ----------
    print("  ---- 电脑侧 ----")
    print()

    hwnd = ime.foreground_window()
    langid, hkl = ime.layout_langid(hwnd) if hwnd else ime.layout_langid()
    lang_name = CJK_LANGIDS.get(langid, f"非 CJK（{langid:#06x}）")
    print(f"    当前键盘布局 : {langid:#06x}  {lang_name}")

    buf = ctypes.create_unicode_buffer(9)
    if ime.user32.GetKeyboardLayoutNameW(buf):
        print(f"    布局标识     : {buf.value}")

    layouts = ime.installed_layouts()
    print(f"    已安装布局   : {len(layouts)} 个")
    for lid, _ in layouts:
        print(f"        {lid:#06x}  {CJK_LANGIDS.get(lid, '其他')}")

    mode = native = None
    if hwnd:
        mode, native = ime.get_conversion_mode(hwnd)
        if mode is None:
            print("    IME 转换模式 : 读不到（前台窗口没有 IME 上下文）")
        else:
            state = "中文输入" if native else "直接输入（英文）"
            print(f"    IME 转换模式 : {mode:#06x}  →  {state}")
    else:
        print("    IME 转换模式 : 没有前台窗口，跳过")

    print()
    if native is True:
        problems.append(
            "电脑输入法现在处于「中文输入」模式 —— 用电脑输入法打出的中文会被丢弃。\n"
            "       处理：按 Shift（或 Ctrl+Space）切到英文/直接输入，再敲拼音让手机输入法组词；\n"
            "             或者直接按 MOD+v 粘贴剪贴板。\n"
            "       也可以让本脚本自动切：启动器里开 IME_GUARD=1（见 README）。"
        )
    elif native is False:
        verdict.append("电脑输入法是「直接输入」—— 按键会透传到手机，中文由手机输入法组词。这是正确状态。")
    elif langid in CJK_LANGIDS:
        problems.append(
            "电脑键盘布局是中文，但读不到输入法的中文/英文模式。\n"
            "       处理：手动确认输入法状态栏显示的是「英」而不是「中」。"
        )
    else:
        verdict.append("电脑键盘布局不是 CJK —— 按键会透传，中文请用手机输入法组词。")

    # ---------- 手机侧 ----------
    print("  ---- 手机侧 ----")
    print()

    adb = args.adb
    if not adb or not os.path.exists(adb):
        adb = "adb"     # 退回到 PATH

    serial, why = find_connected_device(adb)
    if not serial:
        print(f"    [跳过] 手机未连接：{why}")
        print("           插数据线跑一次初始化，或先连上无线 adb 再来看这一节。")
        print()
    else:
        print(f"    设备          : {serial}")
        info = probe_phone(adb, serial)

        d = info.get("default_ime")
        print(f"    默认输入法    : {d if d else '读不到'}")

        avail = info.get("available") or []
        if avail:
            print(f"    可用输入法    : {len(avail)} 个")
            for a in avail:
                mark = " ← 当前" if a == d else ""
                print(f"        {a}{mark}")
        else:
            print("    可用输入法    : 一个都没读到")

        if not d:
            problems.append(
                "手机没有设置默认输入法 —— 按键收到了也出不了字。\n"
                "       处理：手机上 设置 → 系统 → 语言和输入法，启用并选中一个输入法。"
            )
        elif d and avail and d not in avail:
            problems.append(
                f"手机默认输入法 {d} 不在启用列表里，可能已被停用。\n"
                "       处理：手机上重新启用它。"
            )
        else:
            verdict.append(f"手机输入法正常（{d}）—— 敲拼音可以由它组词。")
        print()

    # ---------- 结论 ----------
    print("  ==========================================")
    print("     结论")
    print("  ==========================================")
    print()
    if verdict:
        for v in verdict:
            print(f"    [OK] {v}")
        print()
    if problems:
        for p in problems:
            print(f"    [!] {p}")
        print()
    if not verdict and not problems:
        print("    信息不足，无法给出结论。")
        print()
    print("  记住两条可用路径：")
    print("    1. 电脑输入法切到英文 → 敲拼音 → 手机输入法组词")
    print("    2. 电脑上打好中文 → 按 MOD+v 粘贴到手机")
    print()
    return 0


# ---------------------------------------------------------------------------
# guard
# ---------------------------------------------------------------------------
def cmd_guard(args):
    """
    守护进程：投屏窗口在前台时，把电脑输入法切成「直接输入」；
    窗口消失时还原并退出。

    为什么不是「切一次就完事」：
      输入法的转换模式是跟窗口/线程走的。用户 alt-tab 出去再回来，
      或者输入法自己重置了状态，都可能变回中文模式，所以必须持续盯着。
    """
    if not IS_WINDOWS:
        print("[guard] 仅支持 Windows")
        return 2

    ime = WinIME()

    target = args.process.lower()
    saved = None          # (hwnd, 原始 mode)，只在需要还原时记录
    announced = False
    missing_rounds = 0
    switch_ok = None      # 自动切换到底能不能用，只报一次

    def log(msg):
        if not args.quiet:
            print(f"[输入法守护] {msg}", flush=True)

    log(f"启动，盯着进程 {target}（每 {args.poll}s 检查一次）")

    try:
        while True:
            # ---- 找到投屏窗口 ----
            win = None
            for h in ime.enum_visible_windows():
                if ime.process_name(ime.window_pid(h)) == target:
                    win = h
                    break

            if win is None:
                missing_rounds += 1
                if missing_rounds >= args.exit_after:
                    log(f"目标进程已消失（连续 {missing_rounds} 次没找到），退出")
                    break
                time.sleep(args.poll)
                continue
            missing_rounds = 0

            if not announced:
                log("已找到投屏窗口")
                announced = True

            # ---- 投屏窗口在前台吗 ----
            fg = ime.foreground_window()
            fg_pid = ime.window_pid(fg) if fg else None
            win_pid = ime.window_pid(win)
            in_focus = bool(fg and fg_pid and win_pid and fg_pid == win_pid)

            if in_focus:
                mode, native = ime.get_conversion_mode(fg)
                if mode is None:
                    if switch_ok is None:
                        log("读不到 IME 状态，本输入法可能不支持自动切换 —— 请手动按 Shift 切英文")
                        switch_ok = False
                elif native:
                    if args.dry_run:
                        if switch_ok is not True:
                            log("[dry-run] 检测到中文输入模式 —— 正式运行时会切到直接输入")
                            switch_ok = True
                    else:
                        # 记录原始状态，只在第一次切之前记
                        if saved is None:
                            saved = (fg, mode)
                        ime.set_conversion_mode(fg, 0)
                        # 回读验证：切不动就明确说，不要假装成功
                        back, back_native = ime.get_conversion_mode(fg)
                        if back_native:
                            if switch_ok is not False:
                                log("切换失败：这个输入法不响应自动切换 —— 请手动按 Shift 切到英文")
                                switch_ok = False
                        else:
                            if switch_ok is not True:
                                log("已切到直接输入（英文），拼音会透传给手机输入法组词")
                                switch_ok = True
                else:
                    if switch_ok is None:
                        log("输入法已经是直接输入状态，无需处理")
                        switch_ok = True
            time.sleep(args.poll)

    except KeyboardInterrupt:
        log("收到中断")
    finally:
        # 还原：别把用户其他窗口的输入法状态改了
        if saved is not None and args.restore:
            hwnd, old_mode = saved
            if ime.is_window(hwnd):
                ime.set_conversion_mode(hwnd, old_mode)
                log(f"已还原输入法状态（{old_mode:#06x}）")
        elif saved is not None:
            log("输入法状态未还原（用 --restore 可开启还原）")

    return 0


# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(
        description="输入法助手：诊断并修复「投屏后电脑打字进不了手机」",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd")

    pc = sub.add_parser("check", help="诊断电脑与手机的输入法状态")
    pc.add_argument("--adb", default=None, help="adb.exe 路径（默认从 PATH 找）")
    pc.set_defaults(func=cmd_check)

    pg = sub.add_parser("guard", help="投屏期间自动把电脑输入法切到直接输入")
    pg.add_argument("--process", default="scrcpy.exe", help="目标进程名（默认 scrcpy.exe）")
    pg.add_argument("--poll", type=float, default=0.4, help="检查间隔秒数（默认 0.4）")
    pg.add_argument("--exit-after", type=int, default=10,
                    help="连续多少次找不到目标进程后退出（默认 10）")
    pg.add_argument("--restore", action="store_true",
                    help="退出时还原输入法状态（默认不还原）")
    pg.add_argument("--dry-run", action="store_true",
                    help="只观察并打印将要做什么，不实际切换输入法（验证用）")
    pg.add_argument("--quiet", action="store_true", help="不打印日志")
    pg.set_defaults(func=cmd_guard)

    args = p.parse_args()
    if not getattr(args, "func", None):
        p.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
