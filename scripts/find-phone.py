#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
find-phone.py —— 在当前局域网里找出开着无线 adb 端口（默认 5555）的设备。

为什么需要它：
    adb 只在手机插着 USB 时才知道手机在哪。纯无线模式下必须先知道 IP，
    而手机 IP 是路由器 DHCP 分的，换个网络（公司 <-> 家里）就会变。
    与其让人手动改 config.ini，不如扫一遍。

用法：
    python find-phone.py [端口] [输出文件]
    默认端口 5555，默认输出 phone_ip.txt（一行一个候选 IP）。

设计取舍：
    - 只扫 /24，不扫 /16。/24 最多 253 个地址，1~2 秒扫完；
      /16 要 6 万多个，扫完人都凉了。家里/公司基本都够用。
    - 超时 0.45s 是试出来的：再短会漏掉响应慢的手机，再长整体变慢。
    - 结果写文件而不是只打印，方便 .bat 直接读。
    - 扫到的只是「端口开着」，不代表是 Android！局域网里的电视盒子、NAS、
      路由器、IoT 也可能在 5555 上跑 adbd，甚至能 adb connect 成功。
      必须由调用方再验一次（见 launch.bat 的 accept_if_android）。
"""
import socket
import ipaddress
import concurrent.futures
import sys
import os

DEFAULT_PORT = 5555
TIMEOUT = 0.45
WORKERS = 128
DEFAULT_OUT = "phone_ip.txt"

# 控制台中文兜底：调用方会设 PYTHONIOENCODING=gbk，
# 直接运行时没有这个变量则按 UTF-8 输出。
# 若控制台代码页不匹配，宁可把个别字显示成 '?' 也不要抛异常中断扫描 ——
# 这里只是提示文字，不是数据，所以 errors="replace" 可以接受。
try:
    sys.stdout.reconfigure(errors="replace")
except (AttributeError, OSError):
    pass


def local_ip_and_net():
    """
    拿本机 IP 并推出 /24 网段。
    用 UDP connect 而不是 gethostbyname：前者让内核按路由表选出真正的出口网卡，
    多网卡（有线 + 无线 + 虚拟网卡）时不会选错。
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # 不发包，只为拿路由决策
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip, ipaddress.IPv4Network(ip + "/24", strict=False)


def probe(host, port):
    """只做 TCP 握手：连得上说明端口在监听，不需要真的说 adb 协议。"""
    try:
        with socket.create_connection((str(host), port), timeout=TIMEOUT):
            return str(host)
    except OSError:
        return None


def main():
    port = DEFAULT_PORT
    out_path = DEFAULT_OUT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"[find-phone] 端口参数不是数字: {sys.argv[1]}")
            return 2
    if len(sys.argv) > 2:
        out_path = sys.argv[2]

    try:
        my_ip, net = local_ip_and_net()
    except OSError as e:
        print(f"[find-phone] 拿不到本机 IP，网络可能没连上：{e}")
        return 2

    hosts = [str(h) for h in net.hosts() if str(h) != my_ip]
    print(f"[find-phone] 本机 {my_ip}，扫描 {net}:{port}（{len(hosts)} 个地址）...")

    found = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for r in ex.map(lambda h: probe(h, port), hosts):
            if r:
                found.append(r)

    if not found:
        print(f"[find-phone] 没找到开着 {port} 的设备。")
        print("")
        print("  常见原因：")
        print("    1. 手机重启过或拔过线 —— 无线调试已关闭")
        print("       解决：插数据线，双击 setup.bat 重新初始化")
        print("    2. 手机没连和电脑相同的 WiFi")
        print("    3. 路由器开了 AP 隔离 / 访客网络，设备之间不能互通")
        # 清掉旧结果，避免下次又拿一个死 IP 去试
        try:
            os.remove(out_path)
        except OSError:
            pass
        return 1

    print(f"[find-phone] 找到 {len(found)} 个候选：{', '.join(found)}")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(found) + "\n")
    print(f"[find-phone] 已写入 {out_path}，交给启动器逐个验证。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
