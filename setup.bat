@echo off
REM ============================================================================
REM  scrcpy-wireless-launcher  ::  初始化向导
REM  https://github.com/Wcai018/scrcpy-wireless-launcher
REM
REM  作用：插上数据线后运行一次，自动完成无线 adb 初始化并写入 config.ini
REM  编码：GBK (CP936)  CRLF 行尾  —— 请勿存成 UTF-8，否则中文会乱码
REM ============================================================================

setlocal enabledelayedexpansion
title scrcpy 无线投屏 - 初始化向导

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

echo.
echo   ==================================================
echo      scrcpy 无线投屏 - 初始化向导
echo   ==================================================
echo.
echo   前提：手机已用数据线连接电脑，并已授权 USB 调试
echo.

REM ==================== 1. 定位 scrcpy ====================
echo   [1/6] 定位 scrcpy ...

set "SCRCPY_DIR="
if exist "%ROOT%\scrcpy.exe" (
    set "SCRCPY_DIR=%ROOT%"
    goto :FOUND_SCRCPY
)

REM 读旧配置
if exist "%ROOT%\config.ini" (
    for /f "usebackq tokens=1,* delims==" %%a in ("%ROOT%\config.ini") do (
        if /i "%%a"=="SCRCPY_DIR" if not "%%b"=="" if exist "%%b\scrcpy.exe" set "SCRCPY_DIR=%%b"
    )
)
if defined SCRCPY_DIR goto :FOUND_SCRCPY

REM 从 PATH 找
for %%i in (scrcpy.exe) do set "SCRC_PATH=%%~$PATH:i"
if defined SCRC_PATH (
    for %%j in ("!SCRC_PATH!") do set "SCRCPY_DIR=%%~dpj"
    if "!SCRCPY_DIR:~-1!"=="\" set "SCRCPY_DIR=!SCRCPY_DIR:~0,-1!"
)
if defined SCRCPY_DIR goto :FOUND_SCRCPY

REM 常见安装位置
for %%d in (
    "C:\scrcpy"
    "C:\Program Files\scrcpy"
    "%LOCALAPPDATA%\scrcpy"
    "%USERPROFILE%\scrcpy"
    "%USERPROFILE%\scoop\apps\scrcpy\current"
) do (
    if exist "%%~d\scrcpy.exe" (
        set "SCRCPY_DIR=%%~d"
        goto :FOUND_SCRCPY
    )
)

echo.
echo   [X] 没有找到 scrcpy.exe
echo.
echo   请下载 scrcpy 后解压，并把它的路径填到下面。
echo   下载地址：https://github.com/Genymobile/scrcpy/releases
echo.
set /p "SCRCPY_DIR=  scrcpy 所在目录: "
set "SCRCPY_DIR=!SCRCPY_DIR:"=!"
if not exist "!SCRCPY_DIR!\scrcpy.exe" (
    echo   [X] 该目录下没有 scrcpy.exe，请检查
    pause
    exit /b 1
)

:FOUND_SCRCPY
echo   [OK] scrcpy 目录: !SCRCPY_DIR!
set "ADB=!SCRCPY_DIR!\adb.exe"
if not exist "!ADB!" (
    echo   [X] 该目录下没有 adb.exe（scrcpy 发行包自带）
    pause
    exit /b 1
)
echo.

REM 复制窗口图标（scrcpy 只认自己目录下的 icon.png）
if exist "%ROOT%\assets\icon.png" (
    if not exist "!SCRCPY_DIR!\icon.png" (
        copy /y "%ROOT%\assets\icon.png" "!SCRCPY_DIR!\icon.png" >nul 2>&1
    )
)

REM ==================== 2. 检查 USB 设备 ====================
echo   [2/6] 检查 USB 设备 ...
"!ADB!" start-server >nul 2>&1
"!ADB!" devices -l
echo.

set "USBDEV="
for /f "skip=1 tokens=1,2" %%a in ('"!ADB!" devices') do (
    if "%%b"=="device" (
        echo %%a | findstr /C:":" >nul
        if errorlevel 1 set "USBDEV=%%a"
    )
)

if "!USBDEV!"=="" (
    echo   [X] 没有找到已授权的 USB 设备
    echo.
    echo   请确认：
    echo     1. 数据线已插好（换根线 / 换个 USB 口试试）
    echo     2. 手机屏幕弹出「允许 USB 调试？」后点了允许
    echo     3. 手机的 设置 - 开发者选项 - USB调试 已打开
    echo     4. 下拉通知栏，USB 模式选「文件传输 / MTP」
    echo.
    pause
    exit /b 1
)
echo   [OK] 找到设备: !USBDEV!
echo.

REM ==================== 3. 读取手机 IP ====================
echo   [3/6] 读取手机 WiFi IP ...
set "PHONE_IP="
for /f "tokens=2 delims=/" %%i in ('"!ADB!" -s !USBDEV! shell ip -f inet addr show wlan0 ^| findstr "inet "') do set "PHONE_IP=%%i"

if "!PHONE_IP!"=="" (
    echo   [X] 读取不到 WiFi IP —— 手机可能没有连接 WiFi
    echo       请让手机连上和电脑相同的 WiFi 后重试
    pause
    exit /b 1
)
echo   [OK] 手机 IP: !PHONE_IP!
echo.

REM ==================== 4. 开启 TCP 监听 ====================
echo   [4/6] 开启手机 adb 的 TCP 监听（端口 5555）...
"!ADB!" -s !USBDEV! tcpip 5555
echo       等待手机重启 adb 服务 ...
ping -n 5 127.0.0.1 >nul
echo.

REM ==================== 5. 建立无线连接 ====================
echo   [5/6] 建立无线连接 ...
"!ADB!" connect !PHONE_IP!:5555
ping -n 3 127.0.0.1 >nul
echo.

"!ADB!" devices | findstr /C:"!PHONE_IP!:5555" >nul
if errorlevel 1 (
    echo   [X] 无线连接未建立成功
    echo       请重试，或检查手机与电脑是否在同一网络
    pause
    exit /b 1
)
echo   [OK] 无线连接已建立
echo.

REM ==================== 6. 写入配置 ====================
echo   [6/6] 写入配置文件 ...

REM 保留原有的 EXTRA_ARGS（如果用户改过）
set "EXTRA_ARGS=--no-audio"
if exist "%ROOT%\config.ini" (
    for /f "usebackq tokens=1,* delims==" %%a in ("%ROOT%\config.ini") do (
        if /i "%%a"=="EXTRA_ARGS" if not "%%b"=="" set "EXTRA_ARGS=%%b"
    )
)

>  "%ROOT%\config.ini" echo # scrcpy-wireless-launcher 配置文件
>> "%ROOT%\config.ini" echo # 由 setup.bat 自动生成，也可手动修改
>> "%ROOT%\config.ini" echo.
>> "%ROOT%\config.ini" echo # 手机在局域网中的 IP 地址
>> "%ROOT%\config.ini" echo PHONE_IP=!PHONE_IP!
>> "%ROOT%\config.ini" echo.
>> "%ROOT%\config.ini" echo # adb 无线端口，默认 5555
>> "%ROOT%\config.ini" echo PORT=5555
>> "%ROOT%\config.ini" echo.
>> "%ROOT%\config.ini" echo # scrcpy 所在目录
>> "%ROOT%\config.ini" echo SCRCPY_DIR=!SCRCPY_DIR!
>> "%ROOT%\config.ini" echo.
>> "%ROOT%\config.ini" echo # 传给 scrcpy 的额外参数
>> "%ROOT%\config.ini" echo # 想要手机声音？删掉 --no-audio
>> "%ROOT%\config.ini" echo # 想要更高画质？加 --max-size=1920 --video-bit-rate=8M
>> "%ROOT%\config.ini" echo EXTRA_ARGS=!EXTRA_ARGS!

echo   [OK] 配置已保存到 config.ini
echo.

REM ==================== 完成 ====================
echo   ==================================================
echo      [OK] 初始化完成！
echo   ==================================================
echo.
echo     手机 IP   : !PHONE_IP!
echo     scrcpy    : !SCRCPY_DIR!
echo.
echo     现在可以拔掉数据线了。
echo.
echo     桌面上已生成「手机无线投屏」快捷方式（如果开启了创建）。
echo     以后双击它即可投屏，无需再插线。
echo.

REM 顺手创建桌面快捷方式
if exist "%ROOT%\scripts\create-shortcut.vbs" (
    echo   正在创建桌面快捷方式 ...
    cscript //nologo "%ROOT%\scripts\create-shortcut.vbs" >nul 2>&1
)

echo.
pause
endlocal
