@echo off
REM ============================================================================
REM  scrcpy-wireless-launcher  ::  启动器
REM  https://github.com/Wcai018/scrcpy-wireless-launcher
REM
REM  作用：双击即可通过 WiFi 启动 scrcpy 投屏
REM  编码：GBK (CP936)  CRLF 行尾  —— 请勿存成 UTF-8，否则中文会乱码
REM
REM  ---- 两个常用功能（scrcpy 原生能力，无需额外安装）----
REM   1) 电脑打字直接进手机：默认就开着，敲键盘即可
REM   2) 横竖屏切换：投屏窗口里按 MOD+r
REM      MOD = 左Alt 或 左Win
REM ============================================================================

setlocal enabledelayedexpansion
title scrcpy 无线投屏

REM ---------- 环境准备 ----------
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

REM set /p 需要文件才能吃掉行尾的 CR（原因见 :accept_if_android）
set "TMPFILE=%TEMP%\_scrcpy_model.tmp"
REM Python 被管道/重定向时默认按 UTF-8 输出，而 cmd 控制台是 GBK，
REM 不指定的话 find-phone.py 的中文提示在窗口里会显示成乱码。
set "PYTHONIOENCODING=gbk"
set "PY_EXE="
set "TXDEV="
set "TXMODEL="
set "CACHE=%ROOT%\phone_ip.txt"

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

REM ---------- 定位 scrcpy ----------
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
    echo       请在 config.ini 里改 SCRCPY_DIR，或把 scrcpy 加入 PATH
    pause
    exit /b 1
)

echo.
echo   ==============================================
echo      scrcpy 无线投屏
echo   ==============================================
echo.

REM 切到 scrcpy 目录，用相对名调用 adb，
REM 避免路径含空格时 for /f 里的引号嵌套出错
pushd "!SCRCPY_DIR!"
adb.exe start-server >nul 2>&1

REM ---------- 1. 已有活着的连接？ ----------
call :pick_device
if not "!TXDEV!"=="" (
    echo   [OK] 复用已连接设备: !TXDEV!  ^(!TXMODEL!^)
    goto :launch
)

echo   [1/3] 没有现成连接，开始查找手机 ...

REM ---------- 2. 试上次成功过的地址（缓存） ----------
if exist "!CACHE!" (
    echo   [2/3] 尝试上次的地址 ...
    for /f "usebackq tokens=1" %%i in ("!CACHE!") do (
        if "!TXDEV!"=="" call :try_connect %%i
    )
)

REM ---------- 3. 试 config.ini 里的地址 ----------
if "!TXDEV!"=="" if defined PHONE_IP (
    echo   [2/3] 尝试 config.ini 里的 !PHONE_IP! ...
    call :try_connect !PHONE_IP!
)

REM ---------- 4. 兜底：扫局域网 ----------
if "!TXDEV!"=="" (
    echo   [2/3] 已知地址都不通，扫描当前局域网 ...
    call :find_python
    if "!PY_EXE!"=="" (
        echo.
        echo   [X] 系统里没找到 Python，无法自动扫描。
        echo       三个办法选一个：
        echo         a^) 插数据线，双击 setup.bat 重新初始化
        echo         b^) 改 config.ini 的 PHONE_IP
        echo             查手机 IP: 设置 - WLAN - 当前网络详情
        echo         c^) 装个 Python，之后换网络就不用手改了
        echo.
        popd
        pause
        exit /b 1
    )
    REM 必须用 %ROOT% 的绝对路径：此时 cwd 已经被 pushd 到 scrcpy 目录，
    REM 写相对路径会去找 <scrcpy目录>\scripts\find-phone.py，必然找不到。
    "!PY_EXE!" "%ROOT%\scripts\find-phone.py" !PORT! "!CACHE!"
    if exist "!CACHE!" (
        for /f "usebackq tokens=1" %%i in ("!CACHE!") do (
            if "!TXDEV!"=="" call :try_connect %%i
        )
    )
)

REM ---------- 5. 结果检查 ----------
if "!TXDEV!"=="" (
    echo.
    echo   [X] 没有找到可用的手机。
    echo.
    echo   最常见的原因：手机重启过，无线调试已关闭。
    echo   解决：插数据线，双击 setup.bat 重新初始化。
    echo.
    echo   其他可能：
    echo     - 手机没连和电脑相同的 WiFi
    echo     - 路由器开了 AP 隔离，设备之间不能互通
    echo.
    popd
    pause
    exit /b 1
)

REM 把这次成功的地址记进缓存，下次秒连
for /f "tokens=1 delims=:" %%a in ("!TXDEV!") do > "!CACHE!" echo %%a

:launch
echo   [OK] 已连接: !TXDEV!  ^(!TXMODEL!^)
echo   [3/3] 正在启动投屏 ...
echo.
echo   ----------------------------------------------
echo    电脑打字直接进手机，敲键盘就行
echo    中文输入: 按 MOD+v 粘贴电脑剪贴板
echo              （用电脑输入法直接打中文会被丢，原因见 README）
echo    横竖屏:   MOD+r 切设备方向
echo              MOD+左/右 转画面   MOD+f 全屏
echo    返回/主页: MOD+b / 右键     MOD+h
echo    MOD = 左Alt 或 左Win
echo   ----------------------------------------------
echo.

scrcpy.exe -s !TXDEV! --window-title="手机投屏" !EXTRA_ARGS!

set "RC=!errorlevel!"
popd
if not "!RC!"=="0" (
    echo.
    echo   scrcpy 异常退出，错误信息见上
    pause
)
endlocal
exit /b 0


REM ==================== 子过程 ====================

:pick_device
REM 挑出状态为 device、且确认是真 Android 的无线设备。
REM 必须校验第二列：offline / unauthorized 也会出现在列表里。
set "TXDEV="
set "TXMODEL="
for /f "tokens=1,2" %%a in ('adb.exe devices ^| findstr /C:":%PORT%"') do (
    if "%%b"=="device" call :accept_if_android "%%a"
)
exit /b 0

:accept_if_android
REM %1 = IP:PORT
REM
REM 判据 1：是不是真 Android。
REM 这里用 findstr 锚定行首来判断，而不是把输出读进变量再精确比较 ——
REM 原因是实测踩到的坑：adb shell 的输出行尾是 \r\r\n（两个 CR），
REM 而 for /f 不会剥掉尾部 CR，读进变量会变成 "/system/bin/getprop\r"，
REM 拿它做精确比较必然失败，结果是「真手机也被拒掉」这种最坏情况。
REM findstr 自己处理行尾，不受影响。
REM
REM 另外别改用 getprop 的退出码判断：实测那个伪装端点在命令不存在时
REM 退出码依然是 0，报错还走 stdout，两个信号都不可信。
adb.exe -s %1 shell ls -d /system/bin/getprop 2>nul | findstr /R /C:"^/system/bin/getprop" >nul
if errorlevel 1 (
    echo       [跳过] %~1 不是 Android 设备
    exit /b 0
)

REM 判据 2：取型号。
REM 用 set /p 读文件而不是 for /f 读变量，因为 set /p 会连行尾一起吃掉，
REM 正好避开上面那个 \r 问题。
adb.exe -s %1 shell getprop ro.product.model > "%TMPFILE%" 2>nul
set "MODEL="
set /p MODEL=< "%TMPFILE%"
del "%TMPFILE%" >nul 2>&1
if not defined MODEL set "MODEL=(未知型号)"

set "TXDEV=%1"
set "TXMODEL=!MODEL!"
exit /b 0

:try_connect
REM %1 = 纯 IP。连上并通过 Android 校验才算数。
adb.exe connect %1:%PORT% >nul 2>&1
ping -n 2 127.0.0.1 >nul
call :pick_device
exit /b 0

:find_python
REM py 启动器最可靠（python.org 官方安装包都带），退而求其次用 python
set "PY_EXE="
where py >nul 2>&1
if not errorlevel 1 set "PY_EXE=py"
if defined PY_EXE exit /b 0
where python >nul 2>&1
if not errorlevel 1 set "PY_EXE=python"
exit /b 0
