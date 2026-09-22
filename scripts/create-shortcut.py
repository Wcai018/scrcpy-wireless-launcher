#!/usr/bin/env python3
"""
scrcpy-wireless-launcher :: 桌面快捷方式创建工具（跨平台）

Windows   -> 生成 .lnk（需要 pywin32）
macOS     -> 生成 .command 可执行脚本
Linux     -> 生成 .desktop 桌面项

用法：
    python create-shortcut.py
"""
from __future__ import annotations

import os
import platform
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAUNCH_BAT = ROOT / "launch.bat"
LAUNCH_SH = ROOT / "launch.sh"
ICON = ROOT / "assets" / "icon.ico"
ICON_PNG = ROOT / "assets" / "icon.png"

APP_NAME = "手机无线投屏"


def desktop_dir() -> Path:
    d = Path.home() / "Desktop"
    return d if d.exists() else Path.home()


def make_windows() -> int:
    lnk_path = desktop_dir() / f"{APP_NAME}.lnk"
    try:
        import win32com.client  # type: ignore
    except ImportError:
        print("  [X] Windows 下需要 pywin32，请先执行： pip install pywin32")
        return 1

    if not LAUNCH_BAT.exists():
        print(f"  [X] 找不到 {LAUNCH_BAT}")
        return 1

    shell = win32com.client.Dispatch("WScript.Shell")
    sc = shell.CreateShortCut(str(lnk_path))
    sc.TargetPath = str(LAUNCH_BAT)
    sc.WorkingDirectory = str(ROOT)
    if ICON.exists():
        sc.IconLocation = f"{ICON},0"
    sc.Description = "scrcpy 无线投屏 - 双击启动"
    sc.Save()
    print(f"  [OK] 已创建：{lnk_path}")
    return 0


def make_macos() -> int:
    target = desktop_dir() / f"{APP_NAME}.command"
    if not LAUNCH_SH.exists():
        print(f"  [X] 找不到 {LAUNCH_SH}")
        return 1
    target.write_text(
        "#!/bin/bash\n"
        f'cd "{ROOT}"\n'
        f'exec "{LAUNCH_SH}"\n',
        encoding="utf-8",
    )
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"  [OK] 已创建：{target}")
    print("  [i] 首次运行如被 Gatekeeper 拦截，右键 -> 打开 即可放行")
    return 0


def make_linux() -> int:
    apps = Path.home() / ".local" / "share" / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    desktop_file = apps / "scrcpy-wireless-launcher.desktop"

    if not LAUNCH_SH.exists():
        print(f"  [X] 找不到 {LAUNCH_SH}")
        return 1
    LAUNCH_SH.chmod(LAUNCH_SH.stat().st_mode | stat.S_IXUSR)

    icon_line = f"Icon={ICON_PNG}\n" if ICON_PNG.exists() else "Icon=phone\n"
    desktop_file.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=scrcpy 无线投屏\n"
        "Comment=通过 WiFi 启动 scrcpy 投屏\n"
        f"Exec={LAUNCH_SH}\n"
        f"{icon_line}"
        "Terminal=true\n"
        "Categories=Utility;\n",
        encoding="utf-8",
    )
    desktop_file.chmod(0o755)
    print(f"  [OK] 已创建：{desktop_file}")
    print(f"  [i] 如需显示在应用菜单，可复制到 {desktop_dir()}")
    return 0


def main() -> int:
    system = platform.system()
    print()
    print("  创建桌面快捷方式 ...")
    print(f"    平台 : {system}")
    print(f"    根目录 : {ROOT}")
    print()

    if system == "Windows":
        return make_windows()
    if system == "Darwin":
        return make_macos()
    if system == "Linux":
        return make_linux()

    print(f"  [X] 不支持的平台：{system}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
