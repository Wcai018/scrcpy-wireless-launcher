#!/usr/bin/env bash
# ============================================================================
#  scrcpy-wireless-launcher :: macOS / Linux 初始化向导
#  https://github.com/Wcai018/scrcpy-wireless-launcher
#
#  ⚠️ 本脚本尚未在真机上测试过。
#     作者只有 Windows 环境，此脚本按规范编写但未经执行验证。
#     若遇到问题请反馈： bash -x ./setup.sh 2>&1 | tail -50
#     https://github.com/Wcai018/scrcpy-wireless-launcher/issues
# ============================================================================

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

CONF="$ROOT/config.ini"

if [ -t 1 ]; then
    C_RED=$'\033[31m'; C_GRN=$'\033[32m'; C_YLW=$'\033[33m'; C_RST=$'\033[0m'
else
    C_RED=""; C_GRN=""; C_YLW=""; C_RST=""
fi

info() { printf "  %s\n" "$*"; }
ok()   { printf "  %s[OK]%s %s\n" "$C_GRN" "$C_RST" "$*"; }
warn() { printf "  %s[!]%s %s\n"  "$C_YLW" "$C_RST" "$*"; }
err()  { printf "  %s[X]%s %s\n"  "$C_RED" "$C_RST" "$*"; }

echo
echo "  =================================================="
echo "     scrcpy 无线投屏 - 初始化向导"
echo "  =================================================="
echo
info "前提：手机已用数据线连接电脑，并已授权 USB 调试"
echo

# ==================== 1. 定位 scrcpy ====================
info "[1/6] 定位 scrcpy ..."

SCRCPY_DIR=""
if [ -x "$ROOT/scrcpy" ]; then
    SCRCPY_DIR="$ROOT"
elif command -v scrcpy >/dev/null 2>&1; then
    SCRCPY_DIR="$(dirname "$(command -v scrcpy)")"
elif [ -f "$CONF" ]; then
    cfg_dir="$(grep -E '^SCRCPY_DIR=' "$CONF" | head -1 | cut -d= -f2- || true)"
    [ -n "$cfg_dir" ] && [ -x "$cfg_dir/scrcpy" ] && SCRCPY_DIR="$cfg_dir"
fi

if [ -z "$SCRCPY_DIR" ]; then
    echo
    err "没有找到 scrcpy 可执行文件"
    echo
    info "安装方式（任选其一）："
    info "  macOS   : brew install scrcpy"
    info "  Ubuntu  : sudo apt install scrcpy"
    info "  Arch    : sudo pacman -S scrcpy"
    info "  或从源码/发行包解压到本目录"
    info "  下载地址：https://github.com/Genymobile/scrcpy/releases"
    echo
    printf "  scrcpy 所在目录（留空退出）: "
    read -r input_dir
    if [ -z "$input_dir" ]; then
        exit 1
    fi
    SCRCPY_DIR="${input_dir%/}"
    if [ ! -x "$SCRCPY_DIR/scrcpy" ]; then
        err "该目录下没有可执行的 scrcpy"
        exit 1
    fi
fi

ok "scrcpy 目录: $SCRCPY_DIR"

ADB="$SCRCPY_DIR/adb"
[ -x "$ADB" ] || ADB="$(command -v adb || true)"
if [ -z "$ADB" ] || ! command -v "$ADB" >/dev/null 2>&1 && [ ! -x "$ADB" ]; then
    err "找不到 adb"
    info "macOS  : brew install android-platform-tools"
    info "Ubuntu : sudo apt install android-tools-adb"
    exit 1
fi
echo

# ==================== 2. 检查 USB 设备 ====================
info "[2/6] 检查 USB 设备 ..."
"$ADB" start-server >/dev/null 2>&1
"$ADB" devices -l
echo

USBDEV="$( "$ADB" devices | awk 'NR>1 && $2=="device" && $1 !~ /:/ {print $1; exit}' )"

if [ -z "$USBDEV" ]; then
    err "没有找到已授权的 USB 设备"
    echo
    info "请确认："
    info "  1. 数据线已插好（换根线 / 换个口试试）"
    info "  2. 手机屏幕弹出「允许 USB 调试？」后点了允许"
    info "  3. 手机的 设置 - 开发者选项 - USB调试 已打开"
    info "  4. 下拉通知栏，USB 模式选「文件传输 / MTP」"
    echo
    exit 1
fi
ok "找到设备: $USBDEV"
echo

# ==================== 3. 读取手机 IP ====================
info "[3/6] 读取手机 WiFi IP ..."
PHONE_IP=""

# 依次尝试 wlan0 / wlan1（不同机型网卡名不同）
for IFACE in wlan0 wlan1; do
    PHONE_IP="$( "$ADB" -s "$USBDEV" shell ip -f inet addr show "$IFACE" 2>/dev/null \
                 | awk '/inet /{print $2}' | cut -d/ -f1 | head -1 )"
    [ -n "$PHONE_IP" ] && break
done

# 兜底：从路由表里取
if [ -z "$PHONE_IP" ]; then
    PHONE_IP="$( "$ADB" -s "$USBDEV" shell ip route 2>/dev/null \
                 | awk '$1=="default" && $NF !~ /rmnet/ {print $NF; exit}' )"
fi

if [ -z "$PHONE_IP" ]; then
    err "读取不到 WiFi IP —— 手机可能没有连接 WiFi"
    info "请让手机连上和电脑相同的网络后重试"
    exit 1
fi
ok "手机 IP: $PHONE_IP"
echo

# ==================== 4. 开启 TCP 监听 ====================
info "[4/6] 开启手机 adb 的 TCP 监听（端口 5555）..."
"$ADB" -s "$USBDEV" tcpip 5555
info "      等待手机重启 adb 服务 ..."
sleep 4
echo

# ==================== 5. 建立无线连接 ====================
info "[5/6] 建立无线连接 ..."
"$ADB" connect "$PHONE_IP:5555"
sleep 2
echo

if ! "$ADB" devices | grep -q "$PHONE_IP:5555"; then
    err "无线连接未建立成功"
    info "请重试，或检查手机与电脑是否在同一网络"
    exit 1
fi
ok "无线连接已建立"
echo

# ==================== 6. 写入配置 ====================
info "[6/6] 写入配置文件 ..."

EXTRA_ARGS="--no-audio"
if [ -f "$CONF" ]; then
    prev="$(grep -E '^EXTRA_ARGS=' "$CONF" | head -1 | cut -d= -f2- || true)"
    [ -n "$prev" ] && EXTRA_ARGS="$prev"
fi

cat > "$CONF" <<EOF
# scrcpy-wireless-launcher 配置文件
# 由 setup.sh 自动生成，也可手动修改

# 手机在局域网中的 IP 地址
PHONE_IP=$PHONE_IP

# adb 无线端口，默认 5555
PORT=5555

# scrcpy 所在目录
SCRCPY_DIR=$SCRCPY_DIR

# 传给 scrcpy 的额外参数
# 想要手机声音？删掉 --no-audio
# 想要更高画质？加 --max-size=1920 --video-bit-rate=8M
EXTRA_ARGS=$EXTRA_ARGS
EOF

ok "配置已保存到 config.ini"
echo

# ==================== 完成 ====================
echo "  =================================================="
echo "     [OK] 初始化完成！"
echo "  =================================================="
echo
info "手机 IP : $PHONE_IP"
info "scrcpy  : $SCRCPY_DIR"
echo
info "现在可以拔掉数据线了"
info "以后运行 ./launch.sh 即可投屏，无需再插线"
echo
info "想生成桌面快捷方式？执行： python3 scripts/create-shortcut.py"
echo
