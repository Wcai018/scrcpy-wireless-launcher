# 更新日志 / Changelog

本项目的所有重要变更都会记录在此文件。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [1.0.0] - 2026-09-22

### 新增

- **初始化向导** `setup.bat` / `setup.sh`
  - 自动定位 scrcpy（扫描本目录、PATH、常见安装位置）
  - 自动读取手机 WiFi IP，兼容 `wlan0` / `wlan1` 等不同网卡名
  - 开启 adb TCP 监听并建立无线连接
  - 自动写入 `config.ini`，保留用户已修改的 `EXTRA_ARGS`

- **启动器** `launch.bat` / `launch.sh`
  - 复用已有的无线连接，避免重复 connect
  - **ping 探活前置** —— 手机不可达时 2 秒内给出诊断，不再长时间阻塞
  - 失败时提供分场景的排查指引（IP 变化 / 无线调试关闭）
  - 异常退出时保留窗口，方便查看报错

- **桌面快捷方式**
  - `scripts/create-shortcut.ps1` —— Windows，无需额外依赖
  - `scripts/create-shortcut.py` —— 跨平台（Windows `.lnk` / macOS `.command` / Linux `.desktop`）

- **项目图标** `scripts/generate-icon.py` —— 纯代码绘制，含多尺寸 ICO

- **配置文件** `config.ini` —— 支持 `PHONE_IP` / `PORT` / `SCRCPY_DIR` / `EXTRA_ARGS`

- **文档**
  - 中英双语 README
  - `docs/SECURITY.md` —— adb tcpip 的安全风险与缓解措施
  - `docs/CONTRIBUTING.md` —— 贡献指南，含 GBK 编码约定说明

### 已知问题

- 尚未在 macOS / Linux 上实测
- 部分厂商 ROM 的 WiFi 网卡名非 `wlan0`，可能需手动指定
- 一个 `config.ini` 对应一台手机，多设备需复制多份目录

---

## 修复过的坑（开发记录）

这些是本项目在开发过程中实际踩到并修复的问题，记录下来避免重蹈：

### 批处理中文乱码

最初脚本存为 UTF-8，导致 cmd 按 GBK 解析时中文注释被拆碎执行，
报 `'_IP' 不是内部或外部命令`。

**教训**：Windows 批处理必须存为 GBK + CRLF，且 `chcp 65001` 无法修复
（它在文件开始执行后才生效）。保留 `修复脚本编码.py` 用于批量转码。

### adb connect 长时间阻塞

对不可达地址执行 `adb connect` 会阻塞十几秒，用户看到黑窗口以为程序死了。

**教训**：连接前先 `ping -n 1 -w 1500` 探活，失败场景可缩短到 2 秒内响应。

### 快捷方式属性丢失

用 pywin32 的 `shell.CLSID_ShellLink` 接口时，
`SetWorkingDirectory` / `SetIconLocation` 会静默失效，只有 `TargetPath` 写入成功。

**教训**：必须用 `win32com.client.Dispatch("WScript.Shell").CreateShortCut()`
才能完整写入所有属性。
