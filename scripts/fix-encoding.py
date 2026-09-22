"""
把 .bat 脚本转成 GBK (CP936) + CRLF。

Windows 批处理在 chcp 生效前就按系统代码页解析文件，
存成 UTF-8 会导致中文注释被拆碎当命令执行。

用法： python scripts/fix-encoding.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = [ROOT / "setup.bat", ROOT / "launch.bat"]


def main() -> int:
    rc = 0
    for path in TARGETS:
        if not path.exists():
            print(f"  [skip] 不存在: {path.name}")
            continue

        raw = path.read_bytes()
        text = None
        src = None
        for enc in ("utf-8-sig", "utf-8", "gbk"):
            try:
                text = raw.decode(enc)
                src = enc
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            print(f"  [X] 无法解码: {path.name}")
            rc = 1
            continue

        # 统一 CRLF
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")

        try:
            encoded = text.encode("gbk")
        except UnicodeEncodeError as e:
            print(f"  [X] {path.name} 含 GBK 无法表示的字符: {e}")
            rc = 1
            continue

        before = len(raw)
        path.write_bytes(encoded)
        print(f"  [OK] {path.name}: {src} -> gbk ...")
        print(f"       {before} -> {len(encoded)} bytes, CRLF 行尾")
    return rc


if __name__ == "__main__":
    print()
    print("  转换批处理脚本编码为 GBK ...")
    print()
    sys.exit(main())
