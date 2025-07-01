# Heart Rate Monitor

This is a heart rate monitor application with a floating window that displays real-time heart rate, especially useful during gaming or other full-screen activities. *(Tested only on Xiaomi Band 10)*

🌍 **English** | [简体中文](./README_zh-CN.md)

## Features

* **Low Energy Bluetooth (BLE) Device Scanning:** Scan nearby BLE devices and allow the user to select a heart rate broadcasting device.
* **Real-Time Heart Rate Display:** Show current heart rate in a dedicated UI window.
* **Floating Window:** A customizable, always-on-top window to display heart rate.
* **Click-Through Floating Window:** The floating window can be locked to become click-through, allowing interaction with applications underneath.
* **Customizable Colors:** Set different font colors for the locked and unlocked states of the floating window.
* **Configuration Saving:** Save the last used device MAC address and floating window settings (position, visibility, lock state, and colors).

## File Overview

* **main.py**: Main entry point of the application. Handles command-line arguments and starts the GUI.
* **heart\_rate\_display\_ui.py**: Contains the main application class `HeartRateMonitor`, which sets up the user interface using `tkinter`.
* **floating\_window\.py**: Defines the `FloatingWindow` class that manages the floating window used to display heart rate.
* **get\_heart\_rate/heart\_rate\_tool.py**: Handles scanning, connecting to BLE heart rate devices, and receiving data from them.
* **get\_heart\_rate/test.py**: A test script for scanning and selecting BLE devices.
* **config.py**: Handles saving and loading application configuration to and from `config.json`.
* **requirements.txt**: Lists the Python packages required to run this application.
* **.gitignore**: Specifies files and directories to be ignored by Git.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/ccc007ccc/HeartRateMonitor
   cd HeartRateMonitor
   ```
2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the application:**

   ```bash
   python main.py
   ```
2. **Scan Devices:** Click the "Scan Devices" button to search for nearby BLE heart rate monitors.
3. **Select and Connect:** Choose your device from the list and click "Connect."
4. **Floating Window:**

   * Click "Show Floating Window" to display the heart rate overlay.
   * Drag the window to your desired position.
   * Click "Lock Floating Window" to make it click-through. The color will change to indicate the locked state.
   * You can customize the font colors for both locked and unlocked states in the main window.
5. **Save Settings:** Click "Save Settings" to store the current device and window configuration. Settings are also saved automatically when closing the app.