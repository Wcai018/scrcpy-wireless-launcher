# -*- coding: utf-8 -*-
"""
找手机.py —— 在当前局域网里找出开着 5555 端口（adb 无线调试）的设备。

为什么需要它：
    adb 只在手机插着 USB 时才知道手机在哪。纯无线模式下必须先知道 IP，
    而手机 IP 是路由器 DHCP 分的，换网络（公司<->家里）就会变。
    与其让人手动改脚本，不如扫一遍。

设计取舍：
    - 不硬编码 /24！很多路由器（尤其是 mesh / 企业 AP）用的是 /20 或 /22，
      只扫 /24 会漏掉一大半地址 —— 实测就踩过这个坑：本机 192.168.76.69，
      掩码 255.255.240.0 即 /20，真实网段是 192.168.64.0/20，
      而手机可能落在 192.168.70.x 这种「同网段但不同 /24」的位置。
    - 也不无脑扫整个大网段：/16 有 6 万多个地址，扫完人都凉了。
      策略是「真实网段 + 上限保护」：
        * 网段地址数 <= MAX_SCAN  → 全扫
        * 超过                    → 只扫高概率区域（见 build_scan_list）
    - 超时 0.45s 是试出来的：再短会漏掉响应慢的手机，再长整体变慢。
    - 结果写进 phone_ip.txt 而不是只打印，方便 .bat 直接读。
      写多行（可能有多个候选），由调用方逐个 adb connect 试。
"""
import socket
import ipaddress
import concurrent.futures
import sys
import os
import re
import subprocess

# 控制台中文兜底：调用方（启动器.bat）会设 PYTHONIOENCODING=gbk，
# 但直接双击运行本脚本时没有这个变量，此时按 UTF-8 输出。
# 若控制台代码页不匹配，宁可把个别字显示成 '?' 也不要抛异常中断扫描 ——
# 这里只是提示文字，不是数据，所以 errors="replace" 是可以接受的。
try:
    sys.stdout.reconfigure(errors="replace")
except (AttributeError, OSError):
    pass

PORT = 5555
TIMEOUT = 0.45
WORKERS = 128
OUT_NAME = "phone_ip.txt"

# 单次扫描的地址数上限。超过就退化成「高概率区域」。
# /20 有 4094 个地址，128 线程 × 0.45s 超时 ≈ 15 秒 —— 可接受，
# 所以上限设在这里，让常见的 /22、/20 都能一次扫完。
# 真正扫不动的是 /16（6.5 万个），那种情况才降级。
MAX_SCAN = 4096


def local_ip():
    """用 UDP connect 拿本机出口 IP（不发包，只为让内核按路由表选网卡）。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


def mask_to_prefix(mask):
    """把 '255.255.240.0' 转成 20。"""
    return sum(bin(int(x)).count("1") for x in mask.split("."))


def read_ipconfig():
    """
    从 ipconfig 读本机 IPv4 和子网掩码。

    为什么不用 netifaces 之类的库：不想给一个独立小脚本加第三方依赖。
    为什么不用 ipaddress 猜 /24：那正是这次要修的 bug。
    ipconfig 的中文输出在不同 Windows 语言版本下字段名不同，
    所以用「找掩码格式的字符串」而不是匹配字段名，更稳。

    返回 (ip, prefix) 或 (None, None)。
    """
    ip = local_ip()   # 先用 UDP 拿 IP，稳定且不受语言影响
    try:
        r = subprocess.run(
            ["ipconfig"],
            capture_output=True, timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        text = (r.stdout or b"").decode("gbk", "replace")
    except (OSError, subprocess.TimeoutExpired):
        return ip, None

    # 找 ip 后面紧跟的那个掩码（同一网卡块内，掩码一般紧挨着 IP）
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if ip in line:
            # 往后看几行，找第一个形如 x.x.x.x 的掩码
            for nxt in lines[i + 1:i + 4]:
                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})", nxt)
                if m:
                    cand = m.group(1)
                    # 掩码的合法性：二进制必须是连续的 1
                    try:
                        p = mask_to_prefix(cand)
                        ipaddress.IPv4Network(f"0.0.0.0/{p}")
                        if p >= 16:   # 比 /16 还小的大网段，按 /16 处理
                            return ip, p
                    except (ValueError, ipaddress.NetmaskValueError):
                        continue
            break
    return ip, None


def build_scan_list(my_ip, prefix):
    """
    决定要扫哪些地址。

    prefix 已知且网段不大 → 全扫真实网段。
    网段太大 → 只扫高概率区域：
        a) 本机所在的 /24
        b) 网关所在的 /24
        c) 常见 DHCP 起始段（.0 和 .1 结尾的 /24）
    手机通常和电脑连同一个 AP，落在 a 或 b 的概率极高。
    """
    if prefix:
        net = ipaddress.IPv4Network(f"{my_ip}/{prefix}", strict=False)
        n = net.num_addresses - 2
        if n <= MAX_SCAN:
            hosts = [str(h) for h in net.hosts()]
            return net, hosts, f"{net}（{len(hosts)} 个地址）"

    # 降级：只扫高概率 /24
    octets = my_ip.split(".")
    base = ".".join(octets[:3])
    cand_nets = [f"{base}.0/24"]
    # 网关段：把第三段按 /24 边界对齐（假设至少 /24）
    for delta in (-1, 1, -2, 2):
        third = int(octets[2]) + delta
        if 0 <= third <= 255:
            cand_nets.append(f"192.168.{third}.0/24" if octets[0] == "192" and octets[1] == "168"
                             else f"{octets[0]}.{octets[1]}.{third}.0/24")

    hosts = []
    seen = set()
    for c in cand_nets:
        try:
            net = ipaddress.IPv4Network(c, strict=False)
        except ValueError:
            continue
        for h in net.hosts():
            s = str(h)
            if s != my_ip and s not in seen:
                seen.add(s)
                hosts.append(s)
        if len(hosts) >= MAX_SCAN:
            break

    desc = f"高概率区域（真实网段过大，只扫 {len(cand_nets)} 个 /24，共 {len(hosts)} 个地址）"
    return None, hosts[:MAX_SCAN], desc


def probe(host):
    """只做 TCP 握手：连得上就说明 5555 在监听，不需要真的说 adb 协议。"""
    try:
        with socket.create_connection((str(host), PORT), timeout=TIMEOUT):
            return str(host)
    except OSError:
        return None


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(here, OUT_NAME)

    try:
        my_ip = local_ip()
    except OSError as e:
        print(f"[找手机] 拿不到本机 IP，网络可能没连上：{e}")
        return 2

    my_ip2, prefix = read_ipconfig()
    if my_ip2:
        my_ip = my_ip2

    net, hosts, desc = build_scan_list(my_ip, prefix)
    print(f"[找手机] 本机 {my_ip}" + (f"，子网掩码 /{prefix}" if prefix else "（读不到掩码）"))
    print(f"[找手机] 扫描范围：{desc}")

    found = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for r in ex.map(probe, hosts):
            if r:
                found.append(r)

    if not found:
        print("[找手机] 没找到开着 5555 的设备。")
        print("")
        print("  常见原因：")
        print("    1. 手机重启过或拔过线 —— 无线调试已关闭")
        print("       解决：插数据线，双击「初始化_无线adb.bat」")
        print("    2. 手机没连和电脑相同的 WiFi")
        print("    3. 路由器开了 AP 隔离 / 访客网络，设备之间不能互通")
        # 清掉旧缓存，避免下次又拿一个死 IP 去试
        try:
            os.remove(out_path)
        except OSError:
            pass
        return 1

    print(f"[找手机] 找到 {len(found)} 个候选：{', '.join(found)}")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(found) + "\n")
    print(f"[找手机] 已写入 {OUT_NAME}，交给启动器逐个验证。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
