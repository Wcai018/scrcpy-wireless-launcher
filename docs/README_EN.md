<div align="center">

<img src="../assets/icon.png" width="120" alt="scrcpy-wireless-launcher">

# scrcpy-wireless-launcher

**Double-click once. Screen mirror over WiFi. Never plug in a cable again.**

[![Platform](https://img.shields.io/badge/Windows-verified-2ea44f?style=flat-square)](#platform-support-status)
[![Platform](https://img.shields.io/badge/macOS%20%7C%20Linux-untested-yellow?style=flat-square)](#platform-support-status)
[![scrcpy](https://img.shields.io/badge/scrcpy-%E2%89%A5%202.0-56b3ff?style=flat-square)](https://github.com/Genymobile/scrcpy)
[![License](https://img.shields.io/badge/license-MIT-5eeaa8?style=flat-square)](../LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](#contributing)

[简体中文](../README.md) · [English](README_EN.md)

</div>

---

## ⚠️ Platform support status

**Please read this before deciding whether to use this project.**

| Platform | Status | Notes |
|---|---|---|
| **Windows 10 / 11** | ✅ **Verified** | Fully tested. Environment: Windows 11 + realme RMX5010 (Android 16) + scrcpy 3.3.3 |
| **Android** | ✅ **Verified** | Uses the official `scrcpy-server`; no custom modifications |
| **macOS** | ⚠️ **Untested** | Scripts are written to spec but have **never been executed on real hardware** |
| **Linux** | ⚠️ **Untested** | Same as above |

**Why are some platforms untested?**

The author only has a Windows environment, and the macOS / Linux scripts
cannot be verified without one. Rather than pretending to support them,
this is stated plainly — so you can immediately tell whether a problem
is your setup or simply code nobody has run yet.

**If you use this on macOS / Linux:**

- Feedback is very welcome (both success and failure), see [Contributing](#contributing)
- Please attach full output if you hit issues
- Until verified, treat those scripts as **experimental**

> In short: **safe to use on Windows; on macOS / Linux, be prepared to tinker.**

---

## What is this

[scrcpy](https://github.com/Genymobile/scrcpy) is the best open-source screen mirroring tool
available — but its **wireless mode** requires typing a sequence of commands every time:

```bash
adb tcpip 5555
adb connect 192.168.1.100:5555
scrcpy
```

After a phone reboot you start over. When the IP changes, you hunt for the new one.
**This project turns that into a one-time setup.**

What it does:

- **One-time setup** — plug in the USB cable once, run `setup`, done
- **One-click mirroring** — thereafter, double-click a desktop icon
- **Actionable diagnostics** — tells you *"your phone's IP changed"* or *"wireless debugging is off"*
  instead of dumping a stack trace
- **Portable** — settings live in `config.ini`; copy the folder to migrate

---

## Quick start

### 1. Prerequisites

You need **scrcpy ≥ 2.0** ([releases](https://github.com/Genymobile/scrcpy/releases))
and **USB debugging enabled** on your phone.

<details>
<summary><b>How to enable USB debugging</b></summary>

1. Settings → About phone → tap **Build number** 7 times to unlock Developer options
2. Settings → System → Developer options → enable **USB debugging**
3. Connect via USB; when prompted *"Allow USB debugging?"* → check **Always allow** → **Allow**
4. Your phone and computer must be on the **same LAN** (WiFi)

</details>

### 2. Setup (once)

Connect the phone via USB, then:

| Platform | Action | Status |
|---|---|---|
| **Windows** | Double-click `setup.bat` | ✅ Verified |
| **macOS / Linux** | `./setup.sh` | ⚠️ Untested |

The script locates scrcpy, reads the phone's WiFi IP, enables TCP listening,
establishes the wireless connection, and writes `config.ini`.

Once you see `[OK] Setup complete!`, you can **unplug the cable**.

### 3. Mirror

| Platform | Action | Status |
|---|---|---|
| **Windows** | Double-click `launch.bat`, or run `scripts/create-shortcut.ps1` for a desktop icon | ✅ Verified |
| **macOS / Linux** | `./launch.sh`, or `python3 scripts/create-shortcut.py` | ⚠️ Untested |

That's it. No cable needed from now on.

---

## Keyboard input: type Chinese directly from your computer

Focus the mirroring window and just type — this is a native scrcpy capability, and this
project wires it up with the right default.

### The one-line rule

| Where you want to type | PC keyboard layout | Result |
|---|---|---|
| On the **computer** | **Chinese** | Chinese appears on the computer as usual |
| In the **mirroring window** | **English** | Type pinyin → the phone's IME composes Chinese |

**Just remember: keep the PC layout on English while typing into the mirror.**

### Why English and not Chinese

This is the easiest trap to fall into, so here is the mechanism up front.

scrcpy has two **completely different** paths for keyboard input:

| Path | What it sends | Chinese? |
|---|---|---|
| Key path `INJECT_KEYCODE` | individual **keycodes** | ✅ Yes. The phone's IME gets `n-i-h-a-o` and composes 你好 itself |
| Text path `INJECT_TEXT` | a **pre-composed string** | ❌ No. `KeyCharacterMap.getEvents()` only covers ASCII; Chinese returns `null` |

**Which path is used depends on the PC IME's current state:**

- PC IME in **Chinese** mode → composes first → takes the text path → Chinese is dropped
- PC IME in **English** mode → raw keys pass through → takes the key path →
  **the phone's IME composes, Chinese works**

So "I switched the PC IME to Chinese and nothing happens in the mirror" is not a bug —
it is an inherent limit of the text path.

### How this project solves it: `--keyboard=uhid` (default)

The launcher now passes `--keyboard=uhid`, which makes the computer look like a
**physical keyboard** to the phone (via the Linux UHID kernel module — not Bluetooth,
and no real hardware involved).

Keys then arrive as a physical keyboard would, the phone's IME composes, and Chinese
lands in the field.

**Verified on real hardware** (realme RMX5010 / Android 16 / scrcpy 3.3.3): the uhid
keyboard registers as `/dev/input/event9`, `dumpsys input` shows
`Classes: KEYBOARD | ALPHAKEY`, `Enabled: true`; typing pinyin in the Bilibili search
box with the PC on English produced Chinese that landed in the field and search history.

### No phone-side configuration needed

scrcpy's docs mention configuring the physical keyboard layout on the device.
**Measured result: you don't have to.**

On the test device the Physical keyboard page already showed the layout as
**Chinese (China)** — nothing to change. If another model fails to produce Chinese,
open **Settings → System → Languages and input → Physical keyboard** and check the
keyboard named `scrcpy` (it only appears while mirroring). Press `MOD+k` to open that
page directly.

### Other input methods

| Method | Notes |
|---|---|
| Pinyin + phone IME composition | ✅ Recommended (with the PC on English) |
| `MOD+v` to paste the PC clipboard | ✅ Best for long Chinese text; independent of IME state |
| Pre-composed Chinese from a PC IME | ❌ The text path does not support CJK; it is dropped |

`MOD` defaults to **left Alt** or **left Win**.

---

## Why this exists

Raw scrcpy wireless mode has a few recurring papercuts. All handled here:

| Problem | Raw scrcpy | This project |
|---|---|---|
| 3 commands before every session | ✗ | Double-click |
| Wireless debugging dies on reboot | Re-read the manual | `setup` restores it |
| IP changed → connection fails | `unable to connect` | Rescans the LAN automatically |
| Hangs when unreachable | Long blocking wait | Ping probe, fails in ~2s |
| Another device also listens on 5555 | May connect to the wrong thing | Verifies `getprop`, Android only |
| New machine needs reconfiguration | ✗ | Copy `config.ini` |

> On "wrong device": TV boxes, NAS units, routers and IoT gear can also run `adbd` on
> port 5555. `adb connect` succeeds and `adb devices` shows `device` — but the shell is
> not Android. This project checks for `/system/bin/getprop` and skips anything else.

---

## Configuration

`config.ini`, generated during setup (**edit it freely**):

```ini
# Phone's LAN IP address
PHONE_IP=192.168.1.100

# adb wireless port
PORT=5555

# Directory containing scrcpy
SCRCPY_DIR=D:\Tools\scrcpy

# Extra arguments passed to scrcpy
EXTRA_ARGS=--no-audio
```

### Changed networks?

Nothing to edit. The launcher looks for the phone in this order:

1. An already-live wireless connection → use it
2. The cached address in `phone_ip.txt` (last successful connection)
3. `PHONE_IP` from `config.ini`
4. All of the above fail → scan the local `/24` (about 1–2 seconds)

Step 4 needs Python. **It works without Python too** — you just have to edit
`PHONE_IP` in `config.ini` yourself when the network changes
(on the phone: Settings → WLAN → current network details).

The scan only finds hosts with port 5555 open, and **an open port is not proof of a
phone** — so every candidate is re-verified as Android. See "Why this exists" above.

### Common recipes

Just change the `EXTRA_ARGS` line:

```ini
# Enable audio (Android 11+)
EXTRA_ARGS=

# Higher quality
EXTRA_ARGS=--no-audio --max-size=1920 --video-bit-rate=8M

# Lower latency (gaming)
EXTRA_ARGS=--no-audio --max-size=1024 --max-fps=60 --video-bit-rate=4M

# Keep screen awake
EXTRA_ARGS=--no-audio --stay-awake

# Turn phone screen off while mirroring
EXTRA_ARGS=--no-audio --turn-screen-off
```

Full reference: [scrcpy docs](https://github.com/Genymobile/scrcpy/blob/master/doc/video.md).

---

## Troubleshooting

<details>
<summary><b>"Phone X is not responding"</b></summary>

Your phone and computer are not on the same network, or the IP changed.

1. Verify both are on the **same** WiFi
2. On the phone: Settings → WLAN → tap the current network → note the IP address
3. If it differs from `PHONE_IP`, edit `config.ini` or re-run setup

**Tip:** assign a static IP (DHCP reservation) for your phone in your router's admin panel.

</details>

<details>
<summary><b>"adb connection failed" but the phone pings fine</b></summary>

Usually means the phone rebooted and wireless adb was disabled.
**Plug in USB and re-run `setup`.**

</details>

<details>
<summary><b>Connection drops after a while</b></summary>

Android's WiFi power saving puts the network to sleep. Try:

- Developer options → enable **Stay awake** (screen stays on while charging)
- Keep the phone on USB power while mirroring
- On some devices, disable "WiFi power saving" / "smart network switching"

</details>

<details>
<summary><b>Chinese text appears garbled on Windows</b></summary>

The `.bat` file was saved as UTF-8. Windows batch files require **GBK (CP936)**.

Fix: open in Notepad and re-save with encoding set to **ANSI**.

> Released scripts in this repo are already GBK-encoded.

</details>

<details>
<summary><b>Desktop shortcut creation fails on Windows</b></summary>

Requires `pywin32`:

```bash
pip install pywin32
```

Alternatively, right-click `scripts/create-shortcut.ps1` → *Run with PowerShell*.

</details>

<details>
<summary><b>Multiple phones?</b></summary>

One `config.ini` per phone. Duplicate the whole folder:

```
scrcpy-phone-a/   (PHONE_IP=192.168.1.100)
scrcpy-phone-b/   (PHONE_IP=192.168.1.101)
```

Generate a desktop shortcut in each.

</details>

---

## Project layout

```
scrcpy-wireless-launcher/
├── setup.bat                    # Windows setup wizard       [VERIFIED]
├── launch.bat                   # Windows launcher           [VERIFIED]
├── setup.sh                     # macOS / Linux setup        [UNTESTED]
├── launch.sh                    # macOS / Linux launcher     [UNTESTED]
├── config.ini.example           # Config template (setup generates config.ini)
├── scripts/
│   ├── create-shortcut.ps1      # Desktop shortcut (Windows) [VERIFIED]
│   ├── create-shortcut.py       # Desktop shortcut (cross-platform)
│   │                            #   [only the Windows branch is verified]
│   ├── generate-icon.py         # Regenerate the icon        [VERIFIED]
│   ├── find-phone.py            # Scan the LAN for the phone  [VERIFIED]
│   └── fix-encoding.py          # Convert .bat back to GBK   [VERIFIED]
├── assets/
│   ├── icon.png
│   └── icon.ico
└── docs/
    └── README_EN.md             # This file
```

---

## Requirements

| Item | Requirement | Status |
|---|---|---|
| OS | **Windows 10 / 11** | ✅ Verified |
| OS | macOS 11+ / Linux | ⚠️ Scripts provided, **untested** |
| scrcpy | ≥ 2.0 ([download](https://github.com/Genymobile/scrcpy/releases)) | ✅ Verified on 3.3.3 |
| Phone | Android 5.0+ (audio needs Android 11+) | ✅ Verified on Android 16 |
| Network | Phone and computer on the same LAN | ✅ Verified |
| Optional | Python 3.8+ (icon / shortcut generation) | ✅ Verified |

> **On version ranges**: only scrcpy **3.3.3** has been tested. Versions ≥ 2.0
> should work in theory (`--no-audio` needs 2.0+, `--window-title` needs 2.0+),
> but this has not been verified one by one. Feedback welcome if you use another version.

---

## Security

This project **only invokes the `adb` bundled with the official scrcpy release**.
No modified binaries are included.

`adb tcpip 5555` opens a debugging port on your LAN. Please note:

- Use only on **trusted networks** (home / office)
- Do not leave wireless debugging enabled on public WiFi
- Run `adb usb` to disable TCP mode when done

See [SECURITY.md](SECURITY.md) for details.

---

## Contributing

Issues and PRs are welcome. **Two kinds of feedback are especially needed:**

### 🙋 macOS / Linux test reports (most needed)

`setup.sh` and `launch.sh` are written to spec, but the author has neither
environment and has **never executed them**. If you try them, please report
back — success or failure:

**Success** — tell me your distro/version and I'll mark it verified

**Failure** — please attach:

```bash
bash -x ./setup.sh 2>&1 | tail -50   # execution trace
```

plus your system info (`sw_vers` or `lsb_release -a`).

### 📱 Device compatibility reports

Some vendors don't name their WiFi interface `wlan0` (could be `wlan1`,
`wlan2`, or a vendor-specific name), which breaks the "read phone WiFi IP" step.
If you hit this, please attach:

```bash
adb shell ip -f inet addr
```

### Other

- **scrcpy version compatibility** — only 3.3.3 has been tested
- **Better diagnostics** — if you hit a failure mode the scripts don't cover

---

## Credits

- [scrcpy](https://github.com/Genymobile/scrcpy) by Genymobile —
  this project is merely a usability wrapper around it
- Everyone who reported device-specific issues

## License

[MIT](../LICENSE)

> This project is not affiliated with Genymobile. It is a community tool.
