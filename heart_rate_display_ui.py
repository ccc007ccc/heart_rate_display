# heart_rate_display_ui.py

import asyncio
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import queue
from datetime import datetime

from get_heart_rate.heart_rate_tool import get_heart_rate, scan_and_select_device
from config import save_mac, load_mac
from floating_window import FloatingWindow

class HeartRateMonitor:
    def __init__(self):
        self.heart_rate = 0
        self.connected = False
        self.current_mac = ""
        self.ble_task = None
        self.ble_loop = None
        self.ble_thread = None
        self.should_stop = False
        
        # 悬浮窗
        self.floating_window = FloatingWindow(self)
        
        # 用于线程间通信的队列
        self.log_queue = queue.Queue()
        self.heart_rate_queue = queue.Queue()
        
        # 创建主窗口
        self.setup_ui()
        
        # 启动日志更新
        self.update_logs()
        self.update_heart_rate_display()
        
        # 加载已保存的MAC地址
        self.load_saved_device()

    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("心率监控器 - 游戏悬浮显示")
        self.root.geometry("650x550")
        self.root.resizable(True, True)
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # 心率显示区域
        heart_rate_frame = ttk.LabelFrame(main_frame, text="心率监控", padding="10")
        heart_rate_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        heart_rate_frame.columnconfigure(0, weight=1)
        
        self.heart_rate_label = tk.Label(
            heart_rate_frame, 
            text="心率: --", 
            font=("Arial", 32, "bold"), 
            fg="red"
        )
        self.heart_rate_label.grid(row=0, column=0)
        
        self.status_label = tk.Label(
            heart_rate_frame, 
            text="状态: 未连接", 
            font=("Arial", 12), 
            fg="gray"
        )
        self.status_label.grid(row=1, column=0, pady=(5, 0))
        
        # 设备信息区域
        device_frame = ttk.LabelFrame(main_frame, text="设备信息", padding="10")
        device_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        device_frame.columnconfigure(1, weight=1)
        
        ttk.Label(device_frame, text="当前设备:").grid(row=0, column=0, sticky=tk.W)
        self.device_label = ttk.Label(device_frame, text="未选择设备")
        self.device_label.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        
        # 连接控制按钮区域
        button_frame = ttk.LabelFrame(main_frame, text="连接控制", padding="10")
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        
        self.scan_button = ttk.Button(
            button_frame, 
            text="扫描设备", 
            command=self.scan_devices
        )
        self.scan_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        self.connect_button = ttk.Button(
            button_frame, 
            text="连接", 
            command=self.connect_device,
            state=tk.DISABLED
        )
        self.connect_button.grid(row=0, column=1, padx=5, sticky="ew")
        
        self.disconnect_button = ttk.Button(
            button_frame, 
            text="断开", 
            command=self.disconnect_device,
            state=tk.DISABLED
        )
        self.disconnect_button.grid(row=0, column=2, padx=(5, 0), sticky="ew")
        
        # 悬浮窗控制区域
        floating_frame = ttk.LabelFrame(main_frame, text="悬浮窗控制", padding="10")
        floating_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        floating_frame.columnconfigure(0, weight=1)
        floating_frame.columnconfigure(1, weight=1)
        
        self.show_floating_button = ttk.Button(
            floating_frame,
            text="显示悬浮窗",
            command=self.toggle_floating_window
        )
        self.show_floating_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        self.lock_button = ttk.Button(
            floating_frame,
            text="锁定悬浮窗",
            command=self.toggle_floating_lock,
            state=tk.DISABLED
        )
        self.lock_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        
        # 使用说明
        info_text = """使用说明:
1. 扫描并连接心率设备
2. 点击"显示悬浮窗"在屏幕上显示心率
3. 悬浮窗解锁时(绿色)可拖拽移动，右键菜单操作
4. 点击"锁定悬浮窗"或右键菜单锁定后(橙色)穿透点击，游戏内可用
5. 悬浮窗始终保持在最前端显示"""
        
        info_label = tk.Label(floating_frame, text=info_text, justify=tk.LEFT, font=("Arial", 9))
        info_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=12, 
            width=70,
            font=("Consolas", 9)
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # 清除日志按钮
        ttk.Button(
            log_frame, 
            text="清除日志", 
            command=self.clear_logs
        ).grid(row=1, column=0, pady=(5, 0), sticky=tk.E)

    def log_message(self, message):
        """添加日志消息到队列"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}")

    def update_logs(self):
        """更新日志显示"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        
        # 每100ms检查一次
        self.root.after(100, self.update_logs)

    def update_heart_rate_display(self):
        """更新心率显示"""
        try:
            while True:
                heart_rate = self.heart_rate_queue.get_nowait()
                self.heart_rate = heart_rate
                # 更新主窗口显示
                self.heart_rate_label.config(text=f"心率: {heart_rate}")
                if heart_rate > 0:
                    self.heart_rate_label.config(fg="green")
                else:
                    self.heart_rate_label.config(fg="red")
                
                # 更新悬浮窗显示
                if self.floating_window.is_open():
                    self.floating_window.update_heart_rate(heart_rate)
        except queue.Empty:
            pass
        
        # 每500ms检查一次
        self.root.after(500, self.update_heart_rate_display)

    def clear_logs(self):
        """清除日志"""
        self.log_text.delete(1.0, tk.END)

    def load_saved_device(self):
        """加载已保存的设备"""
        mac = load_mac()
        if mac:
            self.current_mac = mac
            self.device_label.config(text=f"MAC: {mac}")
            self.connect_button.config(state=tk.NORMAL)
            self.log_message(f"从配置文件加载设备: {mac}")

    def toggle_floating_window(self):
        """切换悬浮窗显示"""
        if self.floating_window.is_open():
            self.floating_window.close_window()
        else:
            self.floating_window.create_window()
            self.show_floating_button.config(text="关闭悬浮窗")
            self.lock_button.config(state=tk.NORMAL)
            self.log_message("悬浮窗已显示")
            
    def toggle_floating_lock(self):
        """切换悬浮窗锁定状态"""
        if self.floating_window.is_open():
            self.floating_window.toggle_lock()
            if self.floating_window.locked:
                self.lock_button.config(text="解锁悬浮窗")
            else:
                self.lock_button.config(text="锁定悬浮窗")
                
    def floating_window_closed(self):
        """悬浮窗关闭回调"""
        self.show_floating_button.config(text="显示悬浮窗")
        self.lock_button.config(state=tk.DISABLED, text="锁定悬浮窗")
        self.log_message("悬浮窗已关闭")

    def scan_devices(self):
        """扫描蓝牙设备"""
        self.scan_button.config(state=tk.DISABLED, text="扫描中...")
        self.log_message("开始扫描蓝牙设备...")
        
        # 在后台线程中执行扫描
        scan_thread = threading.Thread(target=self._scan_devices_thread, daemon=True)
        scan_thread.start()

    def _scan_devices_thread(self):
        """扫描设备的后台线程"""
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 执行扫描
            devices = loop.run_until_complete(self._scan_bluetooth_devices())
            
            # 更新UI（在主线程中）
            self.root.after(0, self._show_device_selection, devices)
            
        except Exception as e:
            self.log_message(f"扫描失败: {str(e)}")
            self.root.after(0, lambda: self.scan_button.config(state=tk.NORMAL, text="扫描设备"))

    async def _scan_bluetooth_devices(self):
        """扫描蓝牙设备的异步函数"""
        from bleak import BleakScanner
        
        self.log_message("正在扫描蓝牙设备...")
        devices = await BleakScanner.discover(timeout=10.0)
        self.log_message(f"发现 {len(devices)} 个设备")
        
        return devices

    def _show_device_selection(self, devices):
        """显示设备选择对话框"""
        self.scan_button.config(state=tk.NORMAL, text="扫描设备")
        
        if not devices:
            messagebox.showwarning("扫描结果", "未发现任何蓝牙设备")
            return
        
        # 创建设备选择窗口
        selection_window = tk.Toplevel(self.root)
        selection_window.title("选择设备")
        selection_window.geometry("500x400")
        selection_window.transient(self.root)
        selection_window.grab_set()
        
        # 设备列表
        frame = ttk.Frame(selection_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="选择要连接的设备:", font=("Arial", 12)).pack(pady=(0, 10))
        
        # 创建列表框
        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=("Consolas", 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # 添加设备到列表
        for device in devices:
            name = device.name or "未知设备"
            listbox.insert(tk.END, f"{name} ({device.address})")
        
        # 按钮框架
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                selected_device = devices[selection[0]]
                self.current_mac = selected_device.address
                self.device_label.config(text=f"MAC: {selected_device.address}")
                self.connect_button.config(state=tk.NORMAL)
                save_mac(selected_device.address)
                self.log_message(f"选择设备: {selected_device.name or '未知'} ({selected_device.address})")
                selection_window.destroy()
            else:
                messagebox.showwarning("选择设备", "请选择一个设备")
        
        def on_cancel():
            selection_window.destroy()
        
        ttk.Button(button_frame, text="取消", command=on_cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="确定", command=on_select).pack(side=tk.RIGHT)

    def connect_device(self):
        """连接设备"""
        if not self.current_mac:
            messagebox.showwarning("连接失败", "请先选择设备")
            return
        
        if self.connected:
            messagebox.showinfo("连接状态", "设备已连接")
            return
        
        self.should_stop = False
        self.connect_button.config(state=tk.DISABLED)
        self.disconnect_button.config(state=tk.NORMAL)
        
        self.log_message(f"正在连接设备: {self.current_mac}")
        
        # 启动蓝牙连接线程
        self.ble_thread = threading.Thread(target=self._connect_ble_thread, daemon=True)
        self.ble_thread.start()

    def _connect_ble_thread(self):
        """蓝牙连接的后台线程"""
        try:
            # 创建新的事件循环
            self.ble_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.ble_loop)
            
            # 运行蓝牙连接
            self.ble_loop.run_until_complete(self._run_heart_rate_monitor())
            
        except Exception as e:
            self.log_message(f"连接失败: {str(e)}")
            self.root.after(0, self._on_disconnect)

    async def _run_heart_rate_monitor(self):
        """运行心率监控"""
        # 自定义心率更新回调
        def heart_rate_callback(characteristic, data):
            if self.should_stop:
                return
            try:
                # 尝试多种解析方法
                value = 0
                if len(data) >= 2:
                    # 标准心率数据格式
                    if data[0] & 0x01:  # 16位心率值
                        value = int.from_bytes(data[1:3], byteorder='little')
                    else:  # 8位心率值
                        value = data[1]
                else:
                    # 备用解析方法
                    hex_data = data.hex()
                    if '06' in hex_data:
                        value = int(hex_data.split('06')[1], 16)
                
                if value > 0:
                    self.heart_rate_queue.put(value)
                    self.log_message(f"心率: {value} BPM")
            except Exception as e:
                self.log_message(f"解析心率数据失败: {str(e)}")
        
        # 更新连接状态
        self.root.after(0, self._on_connect)
        
        try:
            # 运行心率监控，传入自定义回调
            await self._run_custom_heart_rate_monitor(self.current_mac, heart_rate_callback)
            
        finally:
            if not self.should_stop:
                self.root.after(0, self._on_disconnect)

    async def _run_custom_heart_rate_monitor(self, mac, callback):
        """自定义心率监控实现"""
        from bleak import BleakClient
        
        disconnected_event = asyncio.Event()
        
        def disconnected_callback(client):
            self.log_message("设备连接断开")
            disconnected_event.set()
            
        async with BleakClient(mac, disconnected_callback=disconnected_callback, timeout=15.0) as client:
            self.log_message("设备连接成功")
            
            # 查找心率特征
            hr_uuid = await self._find_heart_rate_characteristics(client)
            
            if hr_uuid:
                self.log_message(f"找到心率特征: {hr_uuid}")
                await client.start_notify(hr_uuid, callback)
                self.log_message("开始接收心率数据")
                
                # 等待断开或停止信号
                while not self.should_stop and not disconnected_event.is_set():
                    await asyncio.sleep(0.1)
                    
                try:
                    await client.stop_notify(hr_uuid)
                except:
                    pass
            else:
                self.log_message("未找到心率特征")
                raise Exception("未找到心率特征")

    async def _find_heart_rate_characteristics(self, client):
        """查找心率特征"""
        # 标准心率服务和特征UUID
        heart_rate_service_uuid = "0000180d-0000-1000-8000-00805f9b34fb"
        heart_rate_measurement_uuid = "00002a37-0000-1000-8000-00805f9b34fb"
        
        # 首先尝试标准UUID
        for service in client.services:
            if service.uuid.lower() == heart_rate_service_uuid:
                for characteristic in service.characteristics:
                    if characteristic.uuid.lower() == heart_rate_measurement_uuid:
                        return characteristic.uuid
        
        # 查找描述中包含心率的特征
        for service in client.services:
            for characteristic in service.characteristics:
                description = characteristic.description.lower()
                if any(keyword in description for keyword in ['heart rate', 'heart_rate', 'hr']):
                    return characteristic.uuid
        
        # 查找具有notify属性的特征
        for service in client.services:
            for characteristic in service.characteristics:
                if "notify" in characteristic.properties:
                    return characteristic.uuid
        
        return None

    def _on_connect(self):
        """连接成功回调"""
        self.connected = True
        self.status_label.config(text="状态: 已连接", fg="green")
        self.log_message("设备连接成功，开始监控心率")

    def _on_disconnect(self):
        """断开连接回调"""
        self.connected = False
        self.status_label.config(text="状态: 未连接", fg="gray")
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.heart_rate_label.config(text="心率: --", fg="red")
        self.heart_rate_queue.put(0)  # 清除悬浮窗显示
        self.log_message("设备已断开连接")

    def disconnect_device(self):
        """断开设备连接"""
        self.should_stop = True
        
        if self.ble_loop and not self.ble_loop.is_closed():
            try:
                # 在事件循环中设置停止标志
                if self.ble_loop.is_running():
                    self.ble_loop.call_soon_threadsafe(lambda: None)
            except:
                pass
        
        self._on_disconnect()
        self.log_message("手动断开连接")

    def on_closing(self):
        """主窗口关闭事件"""
        self.log_message("正在关闭程序...")
        
        # 断开蓝牙连接
        self.should_stop = True
        if self.connected:
            self.disconnect_device()
        
        # 关闭悬浮窗
        if self.floating_window.is_open():
            self.floating_window.close_window()
        
        # 关闭主窗口
        self.root.destroy()

    def run(self):
        """运行程序"""
        self.log_message("心率监控器启动")
        self.log_message("游戏悬浮显示工具 - 支持透明悬浮窗和点击穿透")
        
        # 设置关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    """主入口函数"""
    app = HeartRateMonitor()
    app.run()

if __name__ == "__main__":
    main()