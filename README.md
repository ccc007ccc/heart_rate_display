# Heart Rate Monitor

This is a heart rate monitoring application with a floating window that displays real-time heart rate data. It is especially useful during gaming or other full-screen activities. *(Tested only on Xiaomi Band 10)*

🌍 [English](./README.md) | **Simplified Chinese**

## Features

* **Low Energy Bluetooth (BLE) Device Scanning:** Scans for nearby BLE devices and allows the user to select a heart rate broadcasting device.
* **Real-Time Heart Rate Display:** Displays the current heart rate in a dedicated UI window.
* **Floating Window:** A customizable, always-on-top window for displaying heart rate data.
* **Click-Through Floating Window:** The floating window can be locked to become click-through, allowing interaction with underlying applications.
* **Customizable Colors:** You can set different font colors for the locked and unlocked states of the floating window.
* **Configuration Saving:** Saves the last used device MAC address and floating window settings (position, visibility, lock state, and colors).

## File Overview

* **main.py**: The main entry point of the application. Handles command-line arguments and launches the GUI.
* **heart\_rate\_display\_ui.py**: Contains the main application class `HeartRateMonitor`, which sets up the user interface using tkinter.
* **floating\_window\.py**: Defines the `FloatingWindow` class, which manages the floating window that displays heart rate data.
* **get\_heart\_rate/heart\_rate\_tool.py**: Responsible for scanning, connecting to BLE heart rate devices, and receiving data.
* **get\_heart\_rate/test.py**: A test script for scanning and selecting BLE devices.
* **config.py**: Manages saving and loading application configuration from the `config.json` file.
* **requirements.txt**: Lists the Python packages required to run this application.
* **.gitignore**: Specifies which files and directories should be ignored by Git.

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
   * You can customize font colors for the locked and unlocked states in the main window.
5. **Save Settings:** Click "Save Settings" to store the current device and floating window configuration. Settings are also saved automatically when closing the app.

## FAQ

1. **Why doesn't the floating window appear in some full-screen games?**

   This is because some games use "exclusive full-screen" mode, which takes full control of the screen and prevents other applications (including this app's floating window) from being displayed on top.

   Displaying a floating window in true full-screen mode requires drawing directly into the game's rendering pipeline, which I avoided due to the risk of getting banned during testing 😓.

   **Solution:** Try changing the game's display mode from "Full Screen" or "Exclusive Full Screen" to "Borderless Window" or "Windowed Full Screen." This provides a similar visual experience while allowing the floating window to display properly.

2. **The app can't find my Bluetooth band or heart rate strap?**

   Make sure your device has enabled heart rate broadcasting and is discoverable via Bluetooth. Also ensure your computer’s Bluetooth is turned on and functioning properly.