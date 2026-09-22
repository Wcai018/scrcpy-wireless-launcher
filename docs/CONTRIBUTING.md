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

### 2. macOS / Linux 实测反馈

目前主要在 Windows 上验证。macOS 和 Linux 的脚本是照规范写的，
但缺少真实环境测试。如果你使用了并能跑通（或跑不通），
都欢迎反馈。

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
