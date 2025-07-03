# ❤️ 心率监控器 - HeartRateMonitor

一个专为实时显示心率而设计的轻量级桌面应用，支持悬浮窗显示，适用于游戏等全屏活动。现在还支持通过 API 提供心率数据，配合 Xbox Game Bar 小组件使用，即使在**独占全屏游戏**中也能查看心率！

---

## ✨ 功能亮点

* 📡 **低功耗蓝牙 (BLE) 扫描**：查找并连接支持心率广播的设备（如小米手环10等）。
* 🖥️ **可自定义悬浮窗**：在桌面上实时显示心率，支持字体颜色自定义与拖拽定位。
* 🔒 **可穿透点击**：锁定悬浮窗后支持点击穿透，不干扰操作。
* 🌐 **API服务器支持**：允许其他程序通过本地 API 获取心率数据。
* 🕹️ **VRChat OSC支持**: 支持在vrchat聊天框显示心率
* 🎮 **可选 Xbox Game Bar 小组件**：解决独占全屏游戏无法显示悬浮窗的问题。

---

## 🚀 安装与使用

### ✅ 方法一：下载可执行文件

1. 前往 [Releases 页面](https://github.com/ccc007ccc/HeartRateMonitor/releases) 下载最新版本的可执行文件（`.exe`）。
2. 将文件放进单独的文件夹并双击运行 `HeartRateMonitor.exe`，无需安装 Python 环境。

---

### 🔧 方法二：从源码运行

1. 克隆仓库：

   ```bash
   git clone https://github.com/ccc007ccc/HeartRateMonitor
   cd HeartRateMonitor
   ```
2. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```
3. 运行主程序：

   ```bash
   python main.py
   ```

---

### 📌 使用步骤（主程序）

1. 启动程序后，点击 **“扫描设备”**，选择您的心率设备并连接。
2. 点击 **“显示悬浮窗”** 开启心率悬浮窗，可自由拖动位置。
3. 点击 **“锁定悬浮窗”** 开启穿透点击功能（颜色将变化）。
5. 点击 **“保存设置”** 持久保存设备和窗口配置，程序退出时也会自动保存。

---

## 🎮 可选：Xbox Game Bar 小组件（安装复杂）

> ⚠️ **仅在独占全屏游戏中需要使用此组件！**
> 对于无边框或窗口化模式，主程序自带悬浮窗已经足够！

HeartRateWidget 是一款 Game Bar 小组件，配合主程序的 API 服务工作，可实现心率在游戏中叠加显示。

### 🧩 安装小组件

1. 下载 [最新的HeartRateWidget压缩包](https://github.com/ccc007ccc/HeartRateWidget/releases)
2. 解压 `HeartRateWidget.zip`。
3. 右键点击 `Install.ps1` → 选择 **“使用 PowerShell 运行”**。

<img src="https://github.com/user-attachments/assets/f6e678ab-82f6-4a04-b2be-05fde29b5d52" width="450"/>

4. 按提示启用 **开发者模式** 并完成安装。

<img src="https://github.com/user-attachments/assets/55921401-8023-4e46-a773-7f72fdcdfa5b" width="450"/>


---

### 📺 启动与使用小组件

1. 按 **Win + G** 打开 Xbox Game Bar。
2. 在小组件菜单中找到 **HeartRateWidget** 并点击。
3. 初次显示为 `❤️N/A`，点击右上角图钉将其固定在屏幕上。


---

### 🔓 允许小组件访问 API（仅首次设置）

1. 下载并运行 [EnableLoopback 工具](https://github.com/Kuingsmile/uwp-tool/releases/download/latest/enableLoopback.exe)。
2. 勾选列表中的 `HeartRateWidget` 应用 → 点击 “**Save Changes**”。

<img src="https://github.com/user-attachments/assets/1af9ea49-b616-4789-b672-b584810ca24d" width="450"/>

---

### 🌐 启用主程序的 API 服务器

1. 打开 HeartRateMonitor 主程序。
2. 勾选 “**启用API服务器**”。
3. HeartRateWidget 将自动连接并显示您的实时心率。

<img src="https://github.com/user-attachments/assets/41b2f0ca-7923-42e7-a4c7-7609ecabff86" width="450"/>

## ❓常见问题

**Q1: 为什么悬浮窗在某些游戏里不显示？**
A: 游戏使用了“独占全屏”模式，请改为“窗口化”或使用 Xbox Game Bar 小组件。

**Q2: 无法找到心率设备？**
A: 请确保设备开启了心率广播，且电脑蓝牙功能正常。
