@echo off
REM ============================================================================
REM  scrcpy-wireless-launcher  ::  启动器
REM  https://github.com/Wcai018/scrcpy-wireless-launcher
REM
REM  作用：双击即可通过 WiFi 启动 scrcpy 投屏
REM  编码：GBK (CP936)  CRLF 行尾  —— 请勿存成 UTF-8，否则中文会乱码
REM ============================================================================

setlocal enabledelayedexpansion
title scrcpy 无线投屏

REM ---------- 定位本脚本所在目录 ----------
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

REM ---------- 读取配置 ----------
set "CONF=%ROOT%\config.ini"
if not exist "%CONF%" (
    echo.
    echo   [X] 找不到配置文件 config.ini
    echo       请先运行一次  setup.bat  完成初始化
    echo.
    pause
    exit /b 1
)

set "PHONE_IP="
set "PORT=5555"
set "SCRCPY_DIR="
set "EXTRA_ARGS=--no-audio"
for /f "usebackq tokens=1,* delims==" %%a in ("%CONF%") do (
    if /i "%%a"=="PHONE_IP"   set "PHONE_IP=%%b"
    if /i "%%a"=="PORT"       set "PORT=%%b"
    if /i "%%a"=="SCRCPY_DIR" set "SCRCPY_DIR=%%b"
    if /i "%%a"=="EXTRA_ARGS" set "EXTRA_ARGS=%%b"
)

if "!PHONE_IP!"=="" (
    echo   [X] config.ini 里没有 PHONE_IP，请重新运行 setup.bat
    pause
    exit /b 1
)

REM ---------- 定位 scrcpy / adb ----------
if "!SCRCPY_DIR!"=="" set "SCRCPY_DIR=%ROOT%"
if not exist "!SCRCPY_DIR!\scrcpy.exe" (
    REM 尝试从 PATH 里找
    for %%i in (scrcpy.exe) do set "SCRC_PATH=%%~$PATH:i"
    if defined SCRC_PATH (
        for %%j in ("!SCRC_PATH!") do set "SCRCPY_DIR=%%~dpj"
        if "!SCRCPY_DIR:~-1!"=="\" set "SCRCPY_DIR=!SCRCPY_DIR:~0,-1!"
    )
)
if not exist "!SCRCPY_DIR!\scrcpy.exe" (
    echo   [X] 找不到 scrcpy.exe
    echo       请在 setup.bat 里指定正确路径，或在 config.ini 里改 SCRCPY_DIR
    pause
    exit /b 1
)

set "ADB=!SCRCPY_DIR!\adb.exe"
if not exist "!ADB!" set "ADB=adb.exe"

echo.echo   ==============================================
echo      scrcpy 无线投屏
echo   ==============================================
echo.

REM ---------- 1. 启动 adb ----------
REM 切到 scrcpy 目录，用相对名调用，避免路径含空格时 for /f 引号嵌套出错
pushd "!SCRCPY_DIR!"
set "ADBCMD=adb.exe"

"%ADBCMD%" start-server >nul 2>&1

REM ---------- 2. 是否已有无线连接 ----------
set "TXDEV="
for /f "tokens=1" %%i in ('adb.exe devices ^| findstr /C:":!PORT!"') do set "TXDEV=%%i"

REM ---------- 3. 没有则探活 + 连接 ----------
if "!TXDEV!"=="" (
    echo   [1/3] 检查手机是否在线 !PHONE_IP! ...

    ping -n 1 -w 1500 !PHONE_IP! >nul 2>&1
    if errorlevel 1 (
        echo   [X] 手机 !PHONE_IP! 没有响应
        echo.
        echo   可能原因：
        echo     1. 手机和电脑不在同一个 WiFi
        echo     2. 手机 IP 变了（路由器重启 / 换网络）
        echo     3. 手机 WiFi 断了或进入了睡眠
        echo.
        echo   怎么办：
        echo     - 确认手机连着和电脑相同的 WiFi
        echo     - 查看手机 IP：设置 - WLAN - 当前网络详情
        echo       若与 !PHONE_IP! 不同，改 config.ini 里的 PHONE_IP
        echo     - 或插数据线双击 setup.bat 重新初始化
        echo.
        popd
        pause
        exit /b 1
    )

    echo   [2/3] 手机在线，正在建立 adb 连接 ...
    "%ADBCMD%" connect !PHONE_IP!:!PORT! >nul 2>&1
    ping -n 3 127.0.0.1 >nul
    for /f "tokens=1" %%i in ('%ADBCMD% devices ^| findstr /C:":!PORT!"') do set "TXDEV=%%i"
)

REM ---------- 4. 结果检查 ----------
if "!TXDEV!"=="" (
    echo   [X] adb 连接失败
    echo.
    echo   手机能 ping 通但 adb 连不上，通常是：
    echo     1. 手机重启过，无线 adb 已关闭
    echo        - 插数据线双击 setup.bat 重新初始化
    echo     2. USB 调试授权掉了
    echo        - 重新插线授权后，再跑一次 setup.bat
    echo.
    popd
    pause
    exit /b 1
)

echo   [OK] 已连接: !TXDEV!
echo   [3/3] 正在启动投屏 ...
echo.

REM ---------- 5. 启动 scrcpy ----------
scrcpy.exe -s !TXDEV! --window-title="手机投屏" !EXTRA_ARGS!

set "RC=!errorlevel!"

REM ---------- 6. 异常时保留窗口 ----------
popd
if not "!RC!"=="0" (
    echo.
    echo   scrcpy 异常退出，错误信息见上
    pause
)
endlocal
