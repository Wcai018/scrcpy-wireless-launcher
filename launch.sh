#!/usr/bin/env bash
# ============================================================================
#  scrcpy-wireless-launcher :: macOS / Linux 启动器
#  https://github.com/Wcai018/scrcpy-wireless-launcher
# ============================================================================

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

CONF="$ROOT/config.ini"

# ---------- 颜色 ----------
if [ -t 1 ]; then
    C_RED=$'\033[31m'; C_GRN=$'\033[32m'; C_YLW=$'\033[33m'; C_CYN=$'\033[36m'; C_RST=$'\033[0m'
else
    C_RED=""; C_GRN=""; C_YLW=""; C_CYN=""; C_RST=""
fi

info()  { printf "  %s\n" "$*"; }
ok()    { printf "  %s[OK]%s %s\n" "$C_GRN" "$C_RST" "$*"; }
warn()  { printf "  %s[!]%s %s\n"  "$C_YLW" "$C_RST" "$*"; }
err()   { printf "  %s[X]%s %s\n"  "$C_RED" "$C_RST" "$*"; }

# ---------- 读配置 ----------
if [ ! -f "$CONF" ]; then
    echo
    err "找不到配置文件 config.ini"
    info "请先运行一次： ./setup.sh"
    echo
    exit 1
fi

PHONE_IP=""; PORT="5555"; SCRCPY_DIR=""; EXTRA_ARGS="--no-audio"

while IFS='=' read -r key val || [ -n "$key" ]; do
    key="$(echo "$key" | tr -d '[:space:]')"
    case "$key" in
        ""|\#*) continue ;;
    esac
    case "$key" in
        PHONE_IP)   PHONE_IP="$val" ;;
        PORT)       PORT="$val" ;;
        SCRCPY_DIR) SCRCPY_DIR="$val" ;;
        EXTRA_ARGS) EXTRA_ARGS="$val" ;;
    esac
done < "$CONF"

if [ -z "$PHONE_IP" ]; then
    err "config.ini 里没有 PHONE_IP，请重新运行 ./setup.sh"
    exit 1
fi

# ---------- 定位 scrcpy ----------
[ -z "$SCRCPY_DIR" ] && SCRCPY_DIR="$ROOT"
if [ ! -x "$SCRCPY_DIR/scrcpy" ]; then
    if command -v scrcpy >/dev/null 2>&1; then
        SCRCPY_DIR="$(dirname "$(command -v scrcpy)")"
    fi
fi
if [ ! -x "$SCRCPY_DIR/scrcpy" ]; then
    err "找不到 scrcpy 可执行文件"
    info "请安装 scrcpy，或在 config.ini 里设置 SCRCPY_DIR"
    exit 1
fi

ADB="$SCRCPY_DIR/adb"
[ -x "$ADB" ] || ADB="$(command -v adb || echo adb)"

echo
echo "  =============================================="
echo "     scrcpy 无线投屏"
echo "  =============================================="
echo

# ---------- 1. 启动 adb ----------
"$ADB" start-server >/dev/null 2>&1

# ---------- 2. 是否已有无线连接 ----------
TXDEV="$( "$ADB" devices | awk -v p=":$PORT" 'NR>1 && index($1,p) {print $1; exit}' )"

# ---------- 3. 探活 + 连接 ----------
if [ -z "$TXDEV" ]; then
    info "[1/3] 检查手机是否在线 $PHONE_IP ..."

    if ! ping -c 1 -W 2 "$PHONE_IP" >/dev/null 2>&1; then
        err "手机 $PHONE_IP 没有响应"
        echo
        info "可能原因："
        info "  1. 手机和电脑不在同一个网络"
        info "  2. 手机 IP 变了（路由器重启 / 换网络）"
        info "  3. 手机 WiFi 断了或进入了睡眠"
        echo
        info "怎么办："
        info "  - 确认手机连着和电脑相同的网络"
        info "  - 在手机上查看 IP，若与 $PHONE_IP 不同，改 config.ini"
        info "  - 或插数据线运行 ./setup.sh 重新初始化"
        echo
        exit 1
    fi

    info "[2/3] 手机在线，正在建立 adb 连接 ..."
    "$ADB" connect "$PHONE_IP:$PORT" >/dev/null 2>&1
    sleep 1
    TXDEV="$( "$ADB" devices | awk -v p=":$PORT" 'NR>1 && index($1,p) {print $1; exit}' )"
fi

# ---------- 4. 结果检查 ----------
if [ -z "$TXDEV" ]; then
    err "adb 连接失败"
    echo
    info "手机能 ping 通但 adb 连不上，通常是："
    info "  1. 手机重启过，无线 adb 已关闭"
    info "     - 插数据线运行 ./setup.sh 重新初始化"
    info "  2. USB 调试授权掉了"
    info "     - 重新插线授权后再跑一次 ./setup.sh"
    echo
    exit 1
fi

ok "已连接: $TXDEV"
info "[3/3] 正在启动投屏 ..."
echo

# ---------- 5. 启动 scrcpy ----------
# shellcheck disable=SC2086
"$SCRCPY_DIR/scrcpy" -s "$TXDEV" --window-title="手机投屏" $EXTRA_ARGS
