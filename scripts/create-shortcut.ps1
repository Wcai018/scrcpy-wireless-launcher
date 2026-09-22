# ============================================================================
#  scrcpy-wireless-launcher :: 创建桌面快捷方式
# ----------------------------------------------------------------------------
#  用法：
#     右键本文件 -> 使用 PowerShell 运行
#     或在 PowerShell 中执行：
#         powershell -ExecutionPolicy Bypass -File create-shortcut.ps1
# ============================================================================

$ErrorActionPreference = "Stop"

# 仓库根目录（本脚本位于 scripts/ 下）
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "launch.bat"))) {
    # 兼容脚本被单独拷贝出来的情况
    if (Test-Path (Join-Path $PSScriptRoot "launch.bat")) {
        $Root = $PSScriptRoot
    } else {
        Write-Host "  [X] 找不到 launch.bat，请确认脚本位于仓库的 scripts\ 目录下" -ForegroundColor Red
        exit 1
    }
}

$LaunchBat = Join-Path $Root "launch.bat"
$IconPath  = Join-Path $Root "assets\icon.ico"
$Desktop   = [Environment]::GetFolderPath("Desktop")
$LnkPath   = Join-Path $Desktop "手机无线投屏.lnk"

Write-Host ""
Write-Host "  创建桌面快捷方式 ..." -ForegroundColor Cyan
Write-Host "    目标 : $LaunchBat"
Write-Host "    图标 : $IconPath"
Write-Host "    输出 : $LnkPath"
Write-Host ""

if (-not (Test-Path $LaunchBat)) {
    Write-Host "  [X] 找不到 $LaunchBat" -ForegroundColor Red
    exit 1
}

try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($LnkPath)
    $Shortcut.TargetPath       = $LaunchBat
    $Shortcut.WorkingDirectory = $Root
    if (Test-Path $IconPath) {
        $Shortcut.IconLocation = "$IconPath,0"
    }
    $Shortcut.Description = "scrcpy 无线投屏 - 双击启动"
    $Shortcut.WindowStyle = 1
    $Shortcut.Save()

    Write-Host "  [OK] 快捷方式已创建：$LnkPath" -ForegroundColor Green
    if (-not (Test-Path $IconPath)) {
        Write-Host "  [i] 未找到自定义图标，使用默认图标" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [X] 创建失败：$_" -ForegroundColor Red
    exit 1
}

Write-Host ""
