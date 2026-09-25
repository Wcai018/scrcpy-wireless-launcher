<div align="center">

<img src="assets/icon.png" width="120" alt="scrcpy-wireless-launcher">

# scrcpy-wireless-launcher

**双击一次，用 WiFi 投屏 —— 再也不用插数据线。**

[![Platform](https://img.shields.io/badge/Windows-%E5%B7%B2%E9%AA%8C%E8%AF%81-2ea44f?style=flat-square)](#平台支持状态)
[![Platform](https://img.shields.io/badge/macOS%20%7C%20Linux-%E6%9C%AA%E6%B5%8B%E8%AF%95-yellow?style=flat-square)](#平台支持状态)
[![scrcpy](https://img.shields.io/badge/scrcpy-%E2%89%A5%202.0-56b3ff?style=flat-square)](https://github.com/Genymobile/scrcpy)
[![License](https://img.shields.io/badge/license-MIT-5eeaa8?style=flat-square)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](#贡献)

[简体中文](README.md) · [English](docs/README_EN.md)

</div>

---

## ⚠️ 平台支持状态

**请先读这一节再决定是否使用。**

| 平台 | 状态 | 说明 |
|---|---|---|
| **Windows 10 / 11** | ✅ **已验证** | 完整测试通过。实测环境：Windows 11 + realme RMX5010 (Android 16) + scrcpy 3.3.3 / 4.1 |
| **Android** | ✅ **已验证** | 手机端使用 scrcpy 官方 `scrcpy-server`，无自定义改动 |
| **macOS** | ⚠️ **未测试** | 脚本已按规范编写，但**从未在真机执行过**。可能存在未知问题 |
| **Linux** | ⚠️ **未测试** | 同上 |

**为什么会有未测试的平台？**

作者只有 Windows 环境，而 macOS / Linux 的脚本无法凭空验证。
与其假装支持，不如如实标注 —— 这样你遇到问题时能立刻判断是自己环境的问题，
还是脚本本身就没人跑过。

**如果你在 macOS / Linux 上使用**：

- 欢迎反馈结果（成功或失败都有价值），见[贡献](#贡献)
- 遇到问题请附上完整输出，我会据此修正
- 在通过实测前，这些脚本请视为**实验性功能**

> 一句话：**Windows 上可以放心用，macOS / Linux 上请做好可能需要自己动手的准备。**

---

## 这是什么

[scrcpy](https://github.com/Genymobile/scrcpy) 是目前最好的开源投屏工具，但它的**无线连接**每次都要手敲一串命令：

```bash
adb tcpip 5555
adb connect 192.168.1.100:5555
scrcpy
```

手机重启后还得再来一遍，IP 变了还得重新查。**这个项目把它变成一次配置、永久使用。**

它做的事情很简单但很实际：

- **一键初始化** —— 插一次数据线，跑 `setup.bat`，自动完成全部配置
- **一键投屏** —— 之后在桌面双击图标就能投屏，全程无线
- **自动诊断** —— 连不上时明确告诉你「手机 IP 变了」还是「无线调试关了」，而不是丢一堆报错
- **换机器可用** —— 配置存在 `config.ini`，拷走整个目录即可迁移

---

## 快速开始

### 1. 准备

需要 **scrcpy ≥ 2.0**（[下载地址](https://github.com/Genymobile/scrcpy/releases)）以及**手机已开启 USB 调试**。

<details>
<summary><b>怎么开启 USB 调试？</b></summary>

1. 设置 → 关于手机 → 连续点击「版本号」7 次，启用开发者模式
2. 设置 → 系统 → 开发者选项 → 打开 **USB 调试**
3. 用数据线连接电脑，手机弹出「允许 USB 调试？」→ 勾选**始终允许** → 点**允许**
4. 手机和电脑必须连接**同一个局域网**（WiFi）

</details>

### 2. 初始化（只需一次）

用数据线连上手机，然后：

| 平台 | 操作 | 状态 |
|---|---|---|
| **Windows** | 双击 `setup.bat` | ✅ 已验证 |
| **macOS / Linux** | `./setup.sh` | ⚠️ 未测试 |

脚本会自动：定位 scrcpy → 读取手机 WiFi IP → 开启 TCP 监听 → 建立无线连接 → 写入 `config.ini`。

看到 `[OK] 初始化完成！` 就可以**拔掉数据线**了。

### 3. 投屏

| 平台 | 操作 | 状态 |
|---|---|---|
| **Windows** | 双击 `launch.bat`，或运行 `scripts/create-shortcut.ps1` 生成桌面图标 | ✅ 已验证 |
| **macOS / Linux** | `./launch.sh`，或 `python3 scripts/create-shortcut.py` 生成桌面图标 | ⚠️ 未测试 |

完成。以后每次投屏都无需插线。

---

## 效果

初始化成功时的输出：

```
  ==================================================
     scrcpy 无线投屏 - 初始化向导
  ==================================================

  [1/6] 定位 scrcpy ...
  [OK] scrcpy 目录: D:\Tools\scrcpy

  [2/6] 检查 USB 设备 ...
  [OK] 找到设备: 30d731d7

  [3/6] 读取手机 WiFi IP ...
  [OK] 手机 IP: 192.168.1.100

  [4/6] 开启手机 adb 的 TCP 监听（端口 5555）...
  [5/6] 建立无线连接 ...
  [OK] 无线连接已建立

  [6/6] 写入配置文件 ...
  [OK] 配置已保存到 config.ini

  ==================================================
     [OK] 初始化完成！
  ==================================================
```

连不上时的提示（**明确告诉你原因和下一步**）：

```
  [1/3] 检查手机是否在线 192.168.1.100 ...
  [X] 手机 192.168.1.100 没有响应

  可能原因：
    1. 手机和电脑不在同一个 WiFi
    2. 手机 IP 变了（路由器重启 / 换网络）
    3. 手机 WiFi 断了或进入了睡眠

  怎么办：
    - 确认手机连着和电脑相同的 WiFi
    - 查看手机 IP：设置 - WLAN - 当前网络详情
      若与 192.168.1.100 不同，改 config.ini 里的 PHONE_IP
    - 或插数据线双击 setup.bat 重新初始化
```

---

## 键盘输入：电脑上直接打中文

投屏窗口获得焦点后，直接敲键盘就会输入到手机 —— 这是 scrcpy 的原生能力，
本项目把它接出来并配置好默认值。

### 一句话用法

| 你要在哪打字 | 电脑输入法 | 结果 |
|---|---|---|
| 在**电脑**上打字 | **中文** | 电脑正常出中文 |
| 在**投屏窗口**里打字 | **英文** | 敲拼音 → 手机输入法组词 → 中文上屏 |

**记住一句就够：要在投屏里打字，电脑输入法保持英文。**

### 为什么是「电脑保持英文」而不是「电脑切中文」

这是本项目最容易走弯路的一点，先把原理说清楚，省得你也绕一圈。

scrcpy 把电脑键盘送到手机，有两条**完全不同的通路**：

| 通路 | 送什么 | 中文能不能过 |
|---|---|---|
| 按键通路 `INJECT_KEYCODE` | 单个按键的**键码** | ✅ 能过。手机输入法收到 `n-i-h-a-o`，自己组词成「你好」 |
| 文本通路 `INJECT_TEXT` | 一段**已经组好的文字** | ❌ 过不去。`KeyCharacterMap.getEvents()` 只覆盖 ASCII，中文返回 `null` |

而**走哪条通路，取决于电脑输入法当前的状态**：

- 电脑输入法在**中文**态 → 输入法先把字组好 → 走文本通路 → 中文被丢弃
- 电脑输入法在**英文**态 → 原始按键原样透传 → 走按键通路 → **手机输入法组词，中文正常**

所以「电脑输入法切中文后在投屏里打字没反应」不是 bug，而是文本通路的固有限制。

### 本项目怎么解决的：`--keyboard=uhid`（默认已开启）

启动器默认带 `--keyboard=uhid`，它的作用是**把电脑键盘模拟成手机认得的一把物理键盘**
（通过 Linux UHID 内核模块，不是蓝牙、也不是真的接了硬件）。

这样电脑的按键会以**物理键盘**的身份进到手机，手机输入法照着组词，中文就上屏了。

**实测确认**（realme RMX5010 / Android 16 / scrcpy 3.3.3）：uhid 键盘会注册为
`/dev/input/event9`，`dumpsys input` 里显示 `Classes: KEYBOARD | ALPHAKEY`、
`Enabled: true`；在 B 站搜索框用「电脑英文 + 敲拼音」成功打出中文并进入搜索历史。

### 手机端不需要做任何配置

scrcpy 官方文档提到 uhid 需要先在手机上配置物理键盘布局。**实测结论：不用你动手。**

本机（realme RMX5010 / Android 16）物理键盘设置页显示键盘布局**本来就是「中文（中国）」**，
无需修改。如果换机型后打不出中文，可以到
**设置 → 系统 → 语言和输入法 → 物理键盘** 看一眼那把叫 `scrcpy` 的键盘
（投屏运行时才会出现），确认布局不是「默认」以外的异常值。

投屏里按 `MOD+k` 可直接打开这个设置页。

### 关于「电脑切中文能打进去吗」

实测中电脑输入法处于中文态时，中文**也可能**上屏（手机组词通路仍可用），
但**不如英文态稳定**。推荐固定用「电脑英文 + 敲拼音」，这是最可靠的姿势。

### 其他输入方式

| 方式 | 说明 |
|---|---|
| 敲拼音，让手机输入法组词 | ✅ 主推方式（配合电脑英文态） |
| 按 `MOD+v` 粘贴电脑剪贴板 | ✅ 长中文文本推荐，不受输入法状态影响 |
| 用电脑输入法打好整段中文再敲 | ❌ 文本通路不支持 CJK，会被丢弃 |

`MOD` 默认是**左 Alt** 或**左 Win** 键。

---

## 为什么需要它

裸用 scrcpy 的无线模式有几个反复踩的坑，这个项目把它们都处理了：

| 问题 | 裸用 scrcpy | 本项目 |
|---|---|---|
| 每次投屏要敲 3 条命令 | ✗ | 双击图标 |
| 手机重启后无线调试失效 | 需重新查手册 | `setup` 一键恢复 |
| IP 变化后连接失败 | 报 `unable to connect` | 自动重扫局域网，不用手改配置 |
| 连不上时卡住无响应 | 长时间阻塞 | 先 ping 探活，2 秒内给出诊断 |
| 局域网里别的设备也开着 5555 | 可能连错设备 | 校验 `getprop`，只认 Android |
| 换电脑要重新配置 | ✗ | 拷 `config.ini` 即可 |

> 关于「连错设备」：局域网里的电视盒子、NAS、路由器、IoT 设备也可能在 5555 上跑
> `adbd`，能被 `adb connect` 上、`adb devices` 也显示 `device`。本项目在连接后
> 会校验设备上是否存在 `/system/bin/getprop`，不是 Android 就跳过并打印原因。

---

## 配置说明

初始化后生成的 `config.ini`（**可直接手改**）：

```ini
# 手机在局域网中的 IP 地址
PHONE_IP=192.168.1.100

# adb 无线端口，默认 5555
PORT=5555

# scrcpy 所在目录
SCRCPY_DIR=D:\Tools\scrcpy

# 传给 scrcpy 的额外参数
EXTRA_ARGS=--no-audio
```

### 换网络了怎么办

不用改配置。启动器按这个顺序找手机：

1. 已经有活着的无线连接 → 直接用
2. `phone_ip.txt` 里的缓存地址（上次成功连过的）
3. `config.ini` 里的 `PHONE_IP`
4. 都失败 → 扫一遍当前局域网（`/24` 网段，约 1~2 秒）

第 4 步需要本机有 Python。**没有 Python 也能用**，只是换网络时要手动改
`config.ini` 的 `PHONE_IP`（手机上看：设置 → WLAN → 当前网络详情）。

扫描靠的是「谁开着 5555 端口」，但**端口开着不等于就是手机** ——
所以扫到的每个候选都会再验一次是不是 Android，见下文「为什么需要它」。

### 常用参数

改 `EXTRA_ARGS` 这一行即可：

```ini
# 想要手机声音（Android 11+）
EXTRA_ARGS=

# 更高画质
EXTRA_ARGS=--no-audio --max-size=1920 --video-bit-rate=8M

# 降低延迟（游戏场景）
EXTRA_ARGS=--no-audio --max-size=1024 --max-fps=60 --video-bit-rate=4M

# 保持屏幕常亮
EXTRA_ARGS=--no-audio --stay-awake

# 关闭手机屏幕（省电，仅投屏）
EXTRA_ARGS=--no-audio --turn-screen-off
```

完整参数见 [scrcpy 官方文档](https://github.com/Genymobile/scrcpy/blob/master/doc/video.md)。

---

## 常见问题

<details>
<summary><b>提示「手机 XX 没有响应」</b></summary>

手机和电脑没在同一网络，或 IP 变了。

1. 确认手机连的是和电脑**同一个** WiFi
2. 手机上查看当前 IP：设置 → WLAN → 点击当前网络 → 查看 IP 地址
3. 若与配置不符，改 `config.ini` 里的 `PHONE_IP`，或重跑 `setup`

**建议**：在路由器后台给手机设置静态 IP 绑定（MAC 绑定），一劳永逸。

</details>

<details>
<summary><b>提示「adb 连接失败」但手机能 ping 通</b></summary>

通常是手机重启过，无线 adb 被关闭了。**插数据线重跑一次 `setup`** 即可。

</details>

<details>
<summary><b>提示「不是 Android 设备」，但我确定手机开着无线调试</b></summary>

说明扫到的那台不是手机。局域网里别的设备（电视盒子 / NAS / 路由器 / IoT）
也可能在 5555 上跑 `adbd`，能被 `adb connect` 上，但 shell 不是 Android。

本项目会逐个候选去验，自动跳到下一个。如果**所有**候选都被跳过，
那多半是手机本身没开无线调试 —— 插线重跑 `setup`。

想进一步缩小范围，可以在 `launch.bat` 里设置 `EXPECTED_MODEL`（见脚本内注释），
只接受指定型号。

</details>

<details>
<summary><b>中文打不进去 / 只出英文</b></summary>

先确认**电脑输入法是不是英文态** —— 在投屏里打字时它必须是英文，敲拼音，
手机输入法才会组词。若在中文态，按键会被电脑输入法吃掉去组词，中文反而进不去。

详见上文「键盘输入：电脑上直接打中文」。两条路径：

- 电脑输法**英文** + 敲**拼音**，让**手机的**输入法组词上屏（主推）
- 用电脑输入法打好，按 `MOD+v` 粘贴过去（长文本更方便）

如果英文态敲拼音也不出字，检查手机是否启用了输入法：

```bash
adb shell ime list -s
```

一个都没有就先去手机设置里启用一个。

</details>

<details>
<summary><b>连接一段时间后自动断开</b></summary>

Android 的 WiFi 省电策略会休眠网络。解决办法：

- 开发者选项 → 打开「**保持唤醒状态**」（充电时不锁屏）
- 或用数据线供电的同时无线投屏
- 部分机型需要关闭「WiFi 智能省电」

</details>

<details>
<summary><b>中文显示乱码 / 脚本报「不是内部或外部命令」</b></summary>

`.bat` 脚本文件被存成了 UTF-8 编码。Windows 批处理需要 **GBK (CP936)** 编码。

修复：用记事本打开脚本，另存为时**编码选择 ANSI**。

> 注：本项目发布的脚本已确保为 GBK 编码。

</details>

<details>
<summary><b>Windows 上无法创建桌面快捷方式</b></summary>

需要 `pywin32`：

```bash
pip install pywin32
```

或直接右键 `scripts/create-shortcut.ps1` → 使用 PowerShell 运行。

</details>

<details>
<summary><b>支持多台手机吗？</b></summary>

当前版本一个 `config.ini` 对应一台手机。多设备可以复制整个目录：

```
scrcpy-phone-a/   (config.ini -> PHONE_IP=192.168.1.100)
scrcpy-phone-b/   (config.ini -> PHONE_IP=192.168.1.101)
```

每个目录各自生成桌面快捷方式即可。

</details>

---

## 项目结构

```
scrcpy-wireless-launcher/
├── setup.bat                    # Windows 初始化向导          [已验证]
├── launch.bat                   # Windows 启动器              [已验证]
├── setup.sh                     # macOS / Linux 初始化向导    [未测试]
├── launch.sh                    # macOS / Linux 启动器        [未测试]
├── config.ini.example           # 配置模板（setup 会生成实际的 config.ini）
├── scripts/
│   ├── create-shortcut.ps1      # 生成桌面快捷方式（Windows） [已验证]
│   ├── create-shortcut.py       # 生成桌面快捷方式（跨平台）  [仅 Windows 分支验证]
│   ├── generate-icon.py         # 重新生成图标                [已验证]
│   ├── find-phone.py            # 扫描局域网找手机（换网络兜底）[已验证]
│   └── fix-encoding.py          # 把 .bat 转回 GBK 编码       [已验证]
├── assets/
│   ├── icon.png
│   └── icon.ico
├── docs/
│   ├── README_EN.md             # English documentation
│   ├── SECURITY.md              # 安全说明
│   ├── CONTRIBUTING.md          # 贡献指南
│   └── CHANGELOG.md             # 更新日志
└── .github/workflows/lint.yml   # CI：编码与语法检查
```

---

## 关于窗口图标

scrcpy 只会加载**它自己所在目录**下的 `icon.png` 作为窗口图标。
`setup` 脚本会在初始化时自动把 `assets/icon.png` 复制过去（若该位置尚无此文件）。

> 不同版本的 scrcpy 对图标参数支持不同：`--window-icon` 是 4.x 才引入的，
> 3.x 及更早版本只能靠目录内的 `icon.png` 自动加载。本项目采用兼容全部版本的方案。

---

## 环境要求

| 项目 | 要求 | 状态 |
|---|---|---|
| 操作系统 | **Windows 10 / 11** | ✅ 已验证 |
| 操作系统 | macOS 11+ / Linux | ⚠️ 脚本已提供，**未测试** |
| scrcpy | ≥ 2.0（[下载](https://github.com/Genymobile/scrcpy/releases)） | ✅ 已在 3.3.3 / 4.1 验证 |
| 手机 | Android 5.0+（Android 11+ 支持音频转发） | ✅ 已在 Android 16 验证 |
| 网络 | 手机与电脑处于同一局域网 | ✅ 已验证 |
| 可选 | Python 3.8+（仅生成图标 / 创建快捷方式时需要） | ✅ 已验证 |

> **关于版本范围**：scrcpy 侧已在 **3.3.3** 与 **4.1** 实测过。理论上 ≥ 2.0 都适用
> （`--no-audio` 需要 2.0+，`--window-title` 需要 2.0+），但未逐一验证。
> 若你用的是其他版本，欢迎反馈结果。

---

## 安全说明

本项目**只调用 scrcpy 官方发行包自带的 `adb`**，不含任何修改版二进制。

`adb tcpip 5555` 会在局域网中开放调试端口。请注意：

- 仅在**可信网络**（家庭 / 办公）中使用
- 不要在公共 WiFi 下保持无线调试开启
- 用完后可执行 `adb usb` 关闭 TCP 模式

详细说明见 [docs/SECURITY.md](docs/SECURITY.md)。

---

## 贡献

欢迎提 Issue 和 PR。**特别需要**以下两类反馈：

### 🙋 macOS / Linux 实测报告（最需要）

`setup.sh` 和 `launch.sh` 是照规范写的，但作者没有这两个环境，
**从未真正执行过**。如果你用了，无论成功还是失败都请反馈：

**成功了** —— 请告诉我在什么发行版/版本上跑通的，我会把状态改成「已验证」

**失败了** —— 请附上：

```bash
bash -x ./setup.sh 2>&1 | tail -50   # 带调试输出的执行过程
```

以及你的系统信息（`sw_vers` 或 `lsb_release -a`）。

### 📱 机型适配反馈

某些品牌的 WiFi 网卡名不是 `wlan0`（可能是 `wlan1`、`wlan2` 或厂商自定义名），
会导致「读取手机 WiFi IP」失败。遇到请附上：

```bash
adb shell ip -f inet addr
```

### 其他

- **scrcpy 版本兼容性** —— 目前已在 3.3.3 与 4.1 上实测，其他版本欢迎反馈
- **更完善的错误诊断** —— 如果你踩到了脚本没覆盖的坑

---

## 致谢

- [scrcpy](https://github.com/Genymobile/scrcpy) by Genymobile —— 本项目只是它的一个易用性封装
- 所有提供实测反馈的贡献者

## 许可

[MIT](LICENSE)

> 本项目与 Genymobile 官方无关，仅为社区工具。
