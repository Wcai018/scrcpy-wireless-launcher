# 更新日志 / Changelog

本项目的所有重要变更都会记录在此文件。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [1.2.0] - 2026-09-25

### 平台支持状态

同前：**Windows + Android 已验证，macOS / Linux 仍未测试**。
本版所有实测均在 realme RMX5010 / Android 16 (SDK 36) + scrcpy 3.3.3 上完成。

### 新增

- **电脑上直接打中文**（本版核心）—— 启动器默认加 `--keyboard=uhid`
  - 用法：**电脑输入法保持英文**，在投屏窗口里敲拼音，**手机输入法组词上屏**
  - `--keyboard=uhid` 把电脑键盘模拟成手机认得的物理键盘，走**按键通路**，
    中文由手机输入法组词 —— 不经过只支持 ASCII 的 `INJECT_TEXT` 文本通路
  - 手机端**不需要做任何配置**（详见下方「实测发现」）
  - 实测证据：B 站搜索框 `uiautomator dump` 读回 `text="咏春DJ版"`，
    且该文本进入搜索历史；uhid 键盘注册为 `/dev/input/event9`，
    `dumpsys input` 显示 `Classes: KEYBOARD | ALPHAKEY`、`Enabled: true`

- **README 重写「键盘输入」章节**
  - 说明电脑输入法「中文 / 英文」两种状态分别走哪条通路、为什么中文会丢
  - 给出 `uhid` 方案的原理与实测结论
  - 明确「手机端不需要配置」以及换机型时的自查方法
  - 按项目定位**移除横竖屏章节**（本工具不做旋转功能）

### 修复 / 澄清

- **纠正一个在此前文档中广泛流传的错误结论**
  - 旧文说「中文无法送进手机，必须靠工具自动把电脑输入法切成英文」——
    **这个前提是错的**。问题不在输入法状态，而在 `--keyboard` 模式。
  - 正确解法是 `--keyboard=uhid`（见上），**不需要改用户的输入法**
- `scripts/ime-helper.py` 的 `guard` 子命令基于上述错误前提，
  本版起**启动器不再调用它**；文件保留但顶部已加勘误，不建议使用
  （其 `check` 子命令的诊断输出仍有参考价值）
- `docs/输入法验证指南.md` 顶部加入勘误说明，保留作为排查过程记录

### 实测发现（供其他机型参考）

| 排查项 | 结论 |
|---|---|
| 手机物理键盘布局要不要改成「中文(简体)」 | **不用**。本机该页显示标题`中文（中国）`、取值`默认`，本来就是中文 |
| 要不要压住手机软键盘 | **不用**。`show_ime_with_hard_keyboard` 设 0/1 实测都压不住（但不影响打中文） |
| 电脑输入法切中文能不能打 | 可能可以（手机组词通路仍通），但不如英文态稳定，**推荐固定用英文** |
| 电脑能否把中文「字符」直接送过去 | 不能。uhid 键盘 `getevent -lp` 只有 `KEY`/`MSC`/`LED` 能力，无字符类事件；中文一律由手机输入法组词 |

---

## [1.1.0] - 2026-09-24

### 平台支持状态

同 1.0.0，无变化：**Windows + Android 已验证，macOS / Linux 仍未测试**。

### 新增

- **换网络自动重扫** `scripts/find-phone.py`
  - 手机 IP 由路由器 DHCP 分配，换个网络（公司 ↔ 家里）就会变
  - 启动器现在按「已有连接 → 缓存 → `config.ini` → 扫描局域网」的顺序查找
  - 扫描只覆盖 `/24`（253 个地址，约 1~2 秒）；`/16` 要扫 6 万多个，不现实
  - 需要本机有 Python；**没有 Python 也能用**，只是换网络时要手改 `PHONE_IP`

- **设备身份校验** —— 拒绝非 Android 的 `adbd`
  - 局域网里的电视盒子 / NAS / 路由器 / IoT 也可能在 5555 上跑 `adbd`，
    能被 `adb connect` 上、`adb devices` 也显示 `device`，但 shell 根本不是 Android
  - 现在连接后会校验 `/system/bin/getprop` 是否存在，不是 Android 就跳过并打印原因
  - `launch.bat` 内可选设置 `EXPECTED_MODEL` 进一步限定型号

- **文档：键盘输入与横竖屏**
  - 说明电脑打字直接进手机（默认开启，无需配置）
  - 说明中文输入的可行与不可行路径，附上游源码依据
  - 说明 `MOD+r`（切设备方向）与 `MOD+左/右`（只转窗口画面）的区别

### 修复

- `launch.bat` 有一行误写成 `echo.echo   ====...`，导致该行把 `echo` 当正文打印出来
- `launch.bat` 调用 `scripts\find-phone.py` 时用了相对路径，但此时 cwd 已被
  `pushd` 切到 scrcpy 目录，必然找不到 —— 改为 `%ROOT%` 绝对路径
- `phone_ip.txt` 未加入 `.gitignore`，可能把个人内网 IP 提交上去

### 已知问题

- 扫描依赖 Python（可选，缺失时降级为手动改 `PHONE_IP`）
- 「校验通过」这条正向路径尚未在真机上验证（测试时手边没有可用设备），
  负向路径（拒绝非 Android）已实测

---

## [1.0.0] - 2026-09-22

### 平台支持状态

| 平台 | 状态 |
|---|---|
| Windows 10 / 11 | ✅ 已验证（Windows 11 + realme RMX5010 / Android 16 + scrcpy 3.3.3） |
| Android | ✅ 已验证（使用官方 scrcpy-server） |
| macOS | ⚠️ 未测试（脚本已提供，未经真机执行） |
| Linux | ⚠️ 未测试（同上） |

> 未测试平台不会在文档中标注为「支持」。README 与徽章均如实反映此状态。

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
    ⚠️ 仅 Windows 分支经实测，macOS / Linux 分支未验证

- **项目图标** `scripts/generate-icon.py` —— 纯代码绘制，含多尺寸 ICO

- **配置文件** `config.ini` —— 支持 `PHONE_IP` / `PORT` / `SCRCPY_DIR` / `EXTRA_ARGS`

- **文档**
  - 中英双语 README
  - `docs/SECURITY.md` —— adb tcpip 的安全风险与缓解措施
  - `docs/CONTRIBUTING.md` —— 贡献指南，含 GBK 编码约定说明

### 已知问题

- **macOS / Linux 未经实测** —— 脚本存在但从未执行，可能存在未知问题（最主要的不确定性）
- 尚未在 Windows 之外的平台发布验证
- 部分厂商 ROM 的 WiFi 网卡名非 `wlan0`，可能需手动指定
- 一个 `config.ini` 对应一台手机，多设备需复制多份目录
- scrcpy 版本仅在 3.3.3 实测，其他版本未逐一验证

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

### adb shell 的输出行尾是两个 CR

在 .bat 里把 `adb shell xxx` 的输出读进变量再比较，会莫名其妙失败。
实测十六进制是 `41 42 43 31 32 33 0D 0D 0A` —— **`\r\r\n`，两个 CR**。
而 `for /f` 不会剥掉尾部的 CR，于是变量变成 `"/system/bin/getprop\r"`，
拿它做精确字符串比较必然不相等。

最坏的情况是「判据写反」：本想拒绝假设备，结果把真设备也一起拒了。

**教训**：判断某行输出用 `findstr /R /C:"^锚定内容"`，让 findstr 自己处理行尾；
需要取字符串则用 `set /p VAR=< 文件`（`set /p` 会连行尾一起吃掉）。
两条路都实测过。

### 端口开着不等于就是手机

扫描局域网时发现一台设备开着 5555，`adb connect` 成功、`adb devices` 显示 `device`，
但：
- 型号自称 `Nexus_4 / mako`（2012 年的机型）
- `getprop`、`settings` 命令都不存在
- MAC 前缀 `00:E0:4C` 是 Realtek（网卡/SoC 厂商，不是手机厂商）

判断它是一台跑着 `adbd` 的非 Android Linux 设备（路由器 / NAS / 盒子一类）。

更麻烦的是，**两个直觉上的判据都不可信**：

| 判据 | 实测结果 |
|---|---|
| 命令退出码 | 命令不存在时**依然返回 0** |
| 报错走 stderr | 实际走 **stdout**，会污染解析 |

**教训**：只认 `/system/bin/getprop` 是否存在（用 findstr 锚定行首判断）。
另外，连接前多验一步的成本，远低于把投屏打到一台电视上的成本。

### pushd 之后相对路径失效

`launch.bat` 里用 `pushd` 切到 scrcpy 目录，是为了避免路径含空格时
`for /f` 的引号嵌套出错。但切完之后，`scripts\find-phone.py` 就被解析成
`<scrcpy目录>\scripts\find-phone.py`，报 `No such file or directory`。

**教训**：`pushd` 之后访问本项目自己的文件，一律用 `%ROOT%` 绝对路径。

### Python 输出编码与 cmd 控制台不一致

Python 被管道 / 重定向时默认按 **UTF-8** 输出，而 cmd 控制台是 **GBK**。
结果：`.bat` 的中文显示正常，Python 脚本的中文全是乱码。

**教训**：在 .bat 里调用 Python 前设 `PYTHONIOENCODING=gbk`，与本 .bat 的编码对齐。
Python 侧再加 `sys.stdout.reconfigure(errors="replace")` 兜底 ——
这里只是提示文字不是数据，个别字降级成 `?` 可以接受，抛异常中断扫描不行。
