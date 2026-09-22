# 贡献指南 / Contributing

感谢你有兴趣参与这个项目。

## 最有价值的贡献

### 1. 机型适配反馈

不同厂商的 WiFi 网卡名不一定是 `wlan0`（有些是 `wlan1`、`wlan2`，
甚至厂商自定义名称）。如果你初始化时卡在「读取手机 WiFi IP」这一步，
请开 Issue 并附上：

```bash
adb shell ip -f inet addr
```

输出即可，我会把对应网卡名加进检测列表。

### 2. macOS / Linux 实测反馈 —— 最需要

`setup.sh` 和 `launch.sh` 是照规范写的，但作者没有这两个环境，
**从未真正执行过**。这是目前项目最大的空白。

如果你用了，无论成功还是失败都请反馈：

**成功了** —— 请告诉我在什么发行版/版本上跑通的，我会把状态改成「已验证」

**失败了** —— 请附上带调试输出的执行过程：

```bash
bash -x ./setup.sh 2>&1 | tail -50
```

以及系统信息：

```bash
sw_vers                    # macOS
lsb_release -a             # Linux
uname -a
```

### 3. 更完善的错误诊断

如果你遇到了脚本未覆盖的失败情况，请附上：

- 你执行的操作
- 完整输出
- `adb devices -l` 的结果
- 手机型号与 Android 版本

## 开发约定

### 编码要求（重要）

`.bat` 脚本**必须保存为 GBK (CP936) 编码 + CRLF 行尾**。

Windows 批处理在 `chcp` 生效前就按系统代码页解析文件内容，
如果存成 UTF-8，中文注释会被拆碎当成命令执行，报一堆
`'xxx' 不是内部或外部命令`。

`chcp 65001` **不能**解决这个问题（它在文件开始执行后才生效）。

### 修改脚本后请自测

```bash
# Windows
setup.bat      # 应先能跑通初始化
launch.bat     # 应能正常投屏

# 关键：测试失败分支
# 把 config.ini 的 PHONE_IP 改成一个不存在的地址，
# 确认脚本能在 2 秒内给出明确提示，而不是卡死
```

### 提交信息

使用约定式提交（Conventional Commits）：

```
feat: 支持 wlan1 / wlan2 网卡名检测
fix: 修复 IP 不可达时 launch 卡住的问题
docs: 补充 Android 11 无线调试的说明
```

## 流程

1. Fork 本仓库
2. 新建分支：`git checkout -b feat/your-feature`
3. 提交改动
4. 发起 Pull Request，说明动机和测试情况

## 许可

贡献的代码默认以 [MIT](../LICENSE) 许可发布。
