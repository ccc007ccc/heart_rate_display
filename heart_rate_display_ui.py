import asyncio
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, colorchooser, filedialog
import sys
import queue
from datetime import datetime
import json
from urllib import request, error

from get_heart_rate.heart_rate_tool import get_heart_rate, scan_and_select_device
from config import save_config, load_config
from floating_window import FloatingWindow
from vrc_osc import VrcOscClient
from api_server import ApiServer

class HeartRateMonitor:
    def __init__(self):
        self.heart_rate = 0
        self.connected = False
        self.current_mac = ""
        self.ble_task = None
        self.ble_loop = None
        self.ble_thread = None
        self.should_stop = False
        
        self.api_server = None
        
        self.floating_window = FloatingWindow(self)
        
        self.log_queue = queue.Queue()
        self.vrc_osc_client = VrcOscClient(self.log_message)
        self.vrc_connected = False
        
        self.heart_rate_queue = queue.Queue()
        
        self.setup_ui()
        
        self.update_logs()
        self.update_heart_rate_display()
        
        self.load_settings()

    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("心率监控器 - 游戏悬浮显示")
        self.root.geometry("860x540") 
        self.root.minsize(800, 500)
        self.root.resizable(True, True)
        
        # 初始化所有Tkinter变量
        self.api_server_enabled = tk.BooleanVar(value=False)
        self.api_port_var = tk.StringVar(value="8000")
        self.vrc_ip_var = tk.StringVar(value="127.0.0.1")
        self.vrc_port_var = tk.StringVar(value="9000")
        self.format_var = tk.StringVar(value="❤️{bpm}")
        self.image_path_var = tk.StringVar(value="未选择图片")
        
        # [修改] 推送模式UI变量，默认端口改为8001
        self.push_enabled_var = tk.BooleanVar(value=False)
        self.push_url_var = tk.StringVar(value="http://127.0.0.1:8001/heartrate")

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        main_frame.columnconfigure(0, weight=1, uniform="group1")
        main_frame.columnconfigure(1, weight=1, uniform="group1")
        main_frame.columnconfigure(2, weight=1, uniform="group1")
        main_frame.rowconfigure(1, weight=1) 

        left_column_frame = ttk.Frame(main_frame)
        middle_column_frame = ttk.Frame(main_frame)
        right_column_frame = ttk.Frame(main_frame)

        left_column_frame.grid(row=0, column=0, sticky="new", padx=(0, 5))
        middle_column_frame.grid(row=0, column=1, sticky="new", padx=5)
        right_column_frame.grid(row=0, column=2, sticky="new", padx=(5, 0))

        PAD_Y = (0, 10)

        # == 第1列: 核心连接 & 状态 ==
        heart_rate_frame = ttk.LabelFrame(left_column_frame, text="心率监控", padding="10")
        heart_rate_frame.pack(fill="x", pady=PAD_Y)
        self.heart_rate_label = tk.Label(heart_rate_frame, text="心率: --", font=("Arial", 32, "bold"), fg="red")
        self.heart_rate_label.pack(pady=(0, 5))
        self.status_label = tk.Label(heart_rate_frame, text="状态: 未连接", font=("Arial", 12), fg="gray")
        self.status_label.pack()
        
        device_frame = ttk.LabelFrame(left_column_frame, text="设备信息", padding="10")
        device_frame.pack(fill="x", pady=PAD_Y)
        device_frame.columnconfigure(1, weight=1)
        ttk.Label(device_frame, text="当前设备:").grid(row=0, column=0, sticky=tk.W)
        self.device_label = ttk.Label(device_frame, text="未选择设备")
        self.device_label.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        
        button_frame = ttk.LabelFrame(left_column_frame, text="连接控制", padding="10")
        button_frame.pack(fill="x", pady=PAD_Y)
        button_frame.columnconfigure((0, 1, 2), weight=1)
        self.scan_button = ttk.Button(button_frame, text="扫描设备", command=self.scan_devices)
        self.scan_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.connect_button = ttk.Button(button_frame, text="连接", command=self.connect_device, state=tk.DISABLED)
        self.connect_button.grid(row=0, column=1, padx=5, sticky="ew")
        self.disconnect_button = ttk.Button(button_frame, text="断开", command=self.disconnect_device, state=tk.DISABLED)
        self.disconnect_button.grid(row=0, column=2, padx=(5, 0), sticky="ew")
        
        # == 第2列: 集成功能 ==
        vrc_frame = ttk.LabelFrame(middle_column_frame, text="VRChat OSC 同步", padding="10")
        vrc_frame.pack(fill="x", pady=PAD_Y)
        vrc_frame.columnconfigure(1, weight=1)
        ttk.Label(vrc_frame, text="IP 地址:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(vrc_frame, textvariable=self.vrc_ip_var).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Label(vrc_frame, text="端口:").grid(row=1, column=0, sticky=tk.W, pady=(5,0))
        ttk.Entry(vrc_frame, textvariable=self.vrc_port_var).grid(row=1, column=1, sticky="ew", padx=5, pady=(5,0))
        self.vrc_connect_button = ttk.Button(vrc_frame, text="连接 OSC", command=self.toggle_vrc_connection)
        self.vrc_connect_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10,0))
        self.vrc_status_label = ttk.Label(vrc_frame, text="状态: 未连接", font=("Arial", 10), foreground="gray")
        self.vrc_status_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(5,0))
        
        api_frame = ttk.LabelFrame(middle_column_frame, text="心率API服务器 (被动获取)", padding="10")
        api_frame.pack(fill="x", pady=PAD_Y)
        api_frame.columnconfigure(1, weight=1)
        self.api_server_enabled.trace_add("write", self.toggle_api_server)
        ttk.Checkbutton(api_frame, text="启用API服务器", variable=self.api_server_enabled).grid(row=0, column=0, sticky=tk.W, columnspan=2)
        ttk.Label(api_frame, text="端口:").grid(row=1, column=0, sticky=tk.W, pady=(5,0))
        ttk.Entry(api_frame, textvariable=self.api_port_var, width=10).grid(row=1, column=1, sticky="ew", padx=5, pady=(5,0))
        self.api_status_label = ttk.Label(api_frame, text="状态: 已禁用", font=("Arial", 10), foreground="gray")
        self.api_status_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(5,0))

        # Webhook 推送模块
        push_frame = ttk.LabelFrame(middle_column_frame, text="Webhook 数据推送 (主动发送)", padding="10")
        push_frame.pack(fill="x", pady=PAD_Y)
        push_frame.columnconfigure(1, weight=1)
        self.push_enabled_var.trace_add("write", self.toggle_push_service)
        ttk.Checkbutton(push_frame, text="启用推送", variable=self.push_enabled_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        ttk.Label(push_frame, text="URL:").grid(row=1, column=0, sticky=tk.W, pady=(5,0))
        ttk.Entry(push_frame, textvariable=self.push_url_var).grid(row=1, column=1, sticky="ew", padx=5, pady=(5,0))
        self.push_status_label = ttk.Label(push_frame, text="状态: 已禁用", font=("Arial", 10), foreground="gray")
        self.push_status_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(5,0))
        
        # == 第3列: 悬浮窗 & 设置 ==
        floating_frame = ttk.LabelFrame(right_column_frame, text="悬浮窗控制", padding="10")
        floating_frame.pack(fill="x", pady=PAD_Y)
        floating_frame.columnconfigure((0, 1, 2), weight=1)
        self.show_floating_button = ttk.Button(floating_frame, text="显示悬浮窗", command=self.toggle_floating_window)
        self.show_floating_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.lock_button = ttk.Button(floating_frame, text="锁定悬浮窗", command=self.toggle_floating_lock, state=tk.DISABLED)
        self.lock_button.grid(row=0, column=1, padx=5, sticky="ew")
        self.save_button = ttk.Button(floating_frame, text="保存设置", command=self.save_settings)
        self.save_button.grid(row=0, column=2, padx=(5, 0), sticky="ew")
        
        color_frame = ttk.LabelFrame(right_column_frame, text="悬浮窗颜色设置", padding="10")
        color_frame.pack(fill="x", pady=PAD_Y)
        color_frame.columnconfigure(2, weight=1)
        ttk.Label(color_frame, text="解锁时 (可拖动):").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.unlocked_color_preview = tk.Label(color_frame, text="      ", bg=self.floating_window.unlocked_color)
        self.unlocked_color_preview.grid(row=0, column=1, sticky=tk.W)
        ttk.Button(color_frame, text="选择...", command=self.choose_unlocked_color).grid(row=0, column=2, padx=5, sticky=tk.E)
        ttk.Label(color_frame, text="锁定时 (穿透点击):").grid(row=1, column=0, sticky=tk.W, pady=(5, 0), padx=(0, 10))
        self.locked_color_preview = tk.Label(color_frame, text="      ", bg=self.floating_window.locked_color)
        self.locked_color_preview.grid(row=1, column=1, pady=(5, 0), sticky=tk.W)
        ttk.Button(color_frame, text="选择...", command=self.choose_locked_color).grid(row=1, column=2, padx=5, pady=(5, 0), sticky=tk.E)

        format_frame = ttk.LabelFrame(right_column_frame, text="悬浮窗格式设置", padding="10")
        format_frame.pack(fill="x", pady=PAD_Y)
        format_frame.columnconfigure(1, weight=1)
        ttk.Label(format_frame, text="格式:").grid(row=0, column=0, sticky=tk.W, padx=(0,5))
        ttk.Entry(format_frame, textvariable=self.format_var).grid(row=0, column=1, sticky="ew")
        ttk.Label(format_frame, text="提示:").grid(row=1, column=0, sticky=tk.W, pady=(5,0), padx=(0,5))
        ttk.Label(format_frame, text="{bpm}: 心率, {img}: 图片", foreground="gray").grid(row=1, column=1, sticky="w", pady=(5,0))
        ttk.Label(format_frame, text="图片:").grid(row=2, column=0, sticky=tk.W, pady=(5,0), padx=(0,5))
        ttk.Label(format_frame, textvariable=self.image_path_var, wraplength=160, justify=tk.LEFT, foreground="blue").grid(row=2, column=1, sticky="ew", pady=(5,0))
        btn_subframe = ttk.Frame(format_frame)
        btn_subframe.grid(row=3, column=0, columnspan=2, pady=(10,0), sticky="ew")
        btn_subframe.columnconfigure((0,1,2), weight=1)
        ttk.Button(btn_subframe, text="选择图片...", command=self.choose_image).grid(row=0, column=0, sticky='ew', padx=(0,5))
        ttk.Button(btn_subframe, text="清除图片", command=self.clear_image).grid(row=0, column=1, sticky='ew', padx=5)
        ttk.Button(btn_subframe, text="应用格式", command=self.apply_format).grid(row=0, column=2, sticky='ew', padx=(5,0))

        # == 底部日志区域 ==
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="10")
        log_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=70, font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        ttk.Button(log_frame, text="清除日志", command=self.clear_logs).grid(row=1, column=0, pady=(5, 0), sticky=tk.E)

    def toggle_push_service(self, *args):
        if self.push_enabled_var.get():
            url = self.push_url_var.get()
            if not url or not url.startswith(('http://', 'https://')):
                self.log_message("启用推送失败：URL格式无效。")
                self.push_status_label.config(text="状态: URL无效", foreground="red")
                self.push_enabled_var.set(False)
                return
            self.push_status_label.config(text="状态: 已启用", foreground="blue")
            self.log_message(f"Webhook 推送已启用，将推送至 {url}")
        else:
            self.push_status_label.config(text="状态: 已禁用", foreground="gray")
            self.log_message("Webhook 推送已禁用。")

    def send_push_notification(self):
        url = self.push_url_var.get()
        if not url:
            return

        payload = {
            "heart_rate": self.heart_rate,
            "connected": self.connected
        }
        
        thread = threading.Thread(target=self._execute_push_request, args=(url, payload), daemon=True)
        thread.start()

    def _execute_push_request(self, url, payload):
        try:
            data = json.dumps(payload).encode('utf-8')
            req = request.Request(url, data=data, headers={'Content-Type': 'application/json', 'User-Agent': 'HeartRateMonitor'})
            
            with request.urlopen(req, timeout=5) as response:
                if 200 <= response.status < 300:
                    def update_status_success():
                        self.push_status_label.config(text=f"状态: 推送成功 (HTTP {response.status})", foreground="green")
                    self.root.after(0, update_status_success)
                else:
                    def update_status_server_error():
                        self.push_status_label.config(text=f"状态: 推送失败 (HTTP {response.status})", foreground="red")
                        self.log_message(f"推送失败，服务器返回: {response.status} {response.reason}")
                    self.root.after(0, update_status_server_error)

        except error.HTTPError as e:
            def update_status_http_error():
                self.push_status_label.config(text=f"状态: 推送失败 (HTTP {e.code})", foreground="red")
                self.log_message(f"HTTP推送错误: {e}")
            self.root.after(0, update_status_http_error)
        except error.URLError as e:
            def update_status_url_error():
                self.push_status_label.config(text="状态: 推送失败 (网络错误)", foreground="red")
                self.log_message(f"URL推送错误: {e.reason}")
            self.root.after(0, update_status_url_error)
        except Exception as e:
            def update_status_generic_error():
                self.push_status_label.config(text="状态: 推送失败 (未知错误)", foreground="red")
                self.log_message(f"推送时发生未知错误: {e}")
            self.root.after(0, update_status_generic_error)

    def choose_image(self):
        filepath = filedialog.askopenfilename(
            title="选择一张图片",
            filetypes=[("图片文件", "*.png *.gif *.jpg *.jpeg"), ("所有文件", "*.*")]
        )
        if filepath:
            self.floating_window.set_image(filepath)
            import os
            self.image_path_var.set(os.path.basename(filepath))
            self.log_message(f"已选择图片: {filepath}")

    def clear_image(self):
        self.floating_window.set_image(None)
        self.image_path_var.set("未选择图片")
        self.log_message("已清除图片。")

    def apply_format(self):
        new_format = self.format_var.get()
        self.floating_window.update_format(new_format)
        self.log_message(f"已应用新格式: {new_format}")

    def choose_unlocked_color(self):
        color_code = colorchooser.askcolor(title="选择解锁时的字体颜色", initialcolor=self.floating_window.unlocked_color)
        if color_code and color_code[1]:
            color = color_code[1]
            self.floating_window.unlocked_color = color
            self.unlocked_color_preview.config(bg=color)
            if self.floating_window.is_open():
                self.floating_window.apply_lock_state()
            self.log_message(f"设置解锁颜色为: {color}")

    def choose_locked_color(self):
        color_code = colorchooser.askcolor(title="选择锁定时的字体颜色", initialcolor=self.floating_window.locked_color)
        if color_code and color_code[1]:
            color = color_code[1]
            self.floating_window.locked_color = color
            self.locked_color_preview.config(bg=color)
            if self.floating_window.is_open():
                self.floating_window.apply_lock_state()
            self.log_message(f"设置锁定颜色为: {color}")

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}")

    def update_logs(self):
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        self.root.after(100, self.update_logs)

    def update_heart_rate_display(self):
        try:
            while True:
                heart_rate = self.heart_rate_queue.get_nowait()
                self.heart_rate = heart_rate
                self.heart_rate_label.config(text=f"心率: {heart_rate}")

                if self.push_enabled_var.get():
                    self.send_push_notification()
                
                if heart_rate > 0:
                    self.heart_rate_label.config(fg="green")
                    if self.vrc_connected:
                        self.vrc_osc_client.send_heart_rate(heart_rate)
                else:
                    self.heart_rate_label.config(fg="red")
                if self.floating_window.is_open():
                    self.floating_window.update_heart_rate(heart_rate)
        except queue.Empty:
            pass
        self.root.after(500, self.update_heart_rate_display)

    def clear_logs(self):
        self.log_text.delete(1.0, tk.END)

    def toggle_api_server(self, *args):
        if self.api_server_enabled.get():
            try:
                port = int(self.api_port_var.get())
                self.api_server = ApiServer(self, port)
                self.api_server.start()
                if self.api_server and self.api_server.httpd:
                    self.api_status_label.config(text=f"状态: 运行于 http://127.0.0.1:{port}", foreground="green")
                else:
                    self.api_status_label.config(text="状态: 启动失败", foreground="red")
                    self.api_server_enabled.set(False)
            except ValueError:
                self.log_message("API服务器启动失败：端口号必须是有效的数字。")
                self.api_status_label.config(text="状态: 端口号无效", foreground="red")
                self.api_server_enabled.set(False)
        else:
            if self.api_server:
                self.api_server.stop()
                self.api_server = None
            self.api_status_label.config(text="状态: 已禁用", foreground="gray")

    def save_settings(self):
        geometry = self.floating_window.last_geometry
        if self.floating_window.is_open() and self.floating_window.window is not None:
            geometry = self.floating_window.window.geometry()
            
        config = {
            "mac": self.current_mac,
            "window": {
                "visible": self.floating_window.is_open(),
                "locked": self.floating_window.is_locked(),
                "geometry": geometry,
                "unlocked_color": self.floating_window.unlocked_color,
                "locked_color": self.floating_window.locked_color,
                "format": self.format_var.get(),
                "image_path": self.floating_window.image_path,
            },
            "vrc_osc": {
                "ip": self.vrc_ip_var.get(),
                "port": self.vrc_port_var.get()
            },
            "api_server": {
                "enabled": self.api_server_enabled.get(),
                "port": self.api_port_var.get()
            },
            "push_webhook": {
                "enabled": self.push_enabled_var.get(),
                "url": self.push_url_var.get()
            }
        }
        save_config(config)
        self.log_message("设置已保存到 config.json")

    def load_settings(self):
        config = load_config()
        if not config:
            self.log_message("未找到配置文件，使用默认设置。")
            return

        mac = config.get("mac")
        if mac:
            self.current_mac = mac
            self.device_label.config(text=f"MAC: {mac}")
            self.connect_button.config(state=tk.NORMAL)
            self.log_message(f"从配置文件加载设备: {mac}")

        window_settings = config.get("window")
        if window_settings:
            self.log_message("正在加载悬浮窗设置...")
            unlocked_color = window_settings.get("unlocked_color", "#00FF00")
            locked_color = window_settings.get("locked_color", "#FF6600")
            self.floating_window.unlocked_color = unlocked_color
            self.floating_window.locked_color = locked_color
            self.unlocked_color_preview.config(bg=unlocked_color)
            self.locked_color_preview.config(bg=locked_color)
            format_str = window_settings.get("format", "❤️{bpm}")
            image_path = window_settings.get("image_path")
            self.format_var.set(format_str)
            self.floating_window.update_format(format_str)
            if image_path:
                import os
                if os.path.exists(image_path):
                    self.floating_window.set_image(image_path)
                    self.image_path_var.set(os.path.basename(image_path))
                    self.log_message(f"已加载图片: {image_path}")
                else:
                    self.log_message(f"配置文件中的图片路径不存在: {image_path}")
                    self.image_path_var.set("图片丢失")
            if window_settings.get("visible", False):
                self.floating_window.last_geometry = window_settings.get("geometry", "200x80+100+100")
                self.toggle_floating_window() 
                if window_settings.get("locked", False):
                    self.root.after(100, self.toggle_floating_lock)
        
        vrc_settings = config.get("vrc_osc")
        if vrc_settings:
            self.vrc_ip_var.set(vrc_settings.get("ip", "127.0.0.1"))
            self.vrc_port_var.set(vrc_settings.get("port", "9000"))
            self.log_message("已加载 VRChat OSC 设置")

        api_settings = config.get("api_server")
        if api_settings:
            self.api_port_var.set(api_settings.get("port", "8080"))
            if api_settings.get("enabled", False):
                self.root.after(100, lambda: self.api_server_enabled.set(True))
            self.log_message("已加载 API 服务器设置")

        # [修改] 加载推送设置
        push_settings = config.get("push_webhook")
        if push_settings:
            self.push_url_var.set(push_settings.get("url", "http://127.0.0.1:8001/heartrate"))
            if push_settings.get("enabled", False):
                self.root.after(100, lambda: self.push_enabled_var.set(True))
            self.log_message("已加载 Webhook 推送设置")

    def toggle_vrc_connection(self):
        if self.vrc_connected:
            self.vrc_osc_client.disconnect()
            self.vrc_connected = False
            self.vrc_connect_button.config(text="连接 OSC")
            self.vrc_status_label.config(text="状态: 未连接", foreground="gray")
            self.log_message("VRChat OSC 已断开")
        else:
            ip = self.vrc_ip_var.get()
            port_str = self.vrc_port_var.get()
            if not ip or not port_str:
                messagebox.showerror("OSC 错误", "IP地址和端口不能为空")
                return
            try:
                port = int(port_str)
                success, message = self.vrc_osc_client.connect(ip, port)
                if success:
                    self.vrc_connected = True
                    self.vrc_connect_button.config(text="断开 OSC")
                    self.vrc_status_label.config(text=f"状态: 已连接到 {ip}:{port}", foreground="green")
                    self.log_message(message)
                else:
                    messagebox.showerror("OSC 连接失败", message)
                    self.log_message(f"OSC 连接失败: {message}")
            except ValueError:
                messagebox.showerror("OSC 错误", "端口号必须是有效的数字")
                self.log_message("OSC 连接失败: 端口号无效")
            except Exception as e:
                messagebox.showerror("OSC 连接失败", str(e))
                self.log_message(f"OSC 连接失败: {e}")

    def toggle_floating_window(self):
        if self.floating_window.is_open():
            self.floating_window.close_window()
        else:
            self.floating_window.create_window()
            self.show_floating_button.config(text="关闭悬浮窗")
            self.lock_button.config(state=tk.NORMAL)
            self.log_message("悬浮窗已显示")
            
    def toggle_floating_lock(self):
        if self.floating_window.is_open():
            self.floating_window.toggle_lock()
            if self.floating_window.is_locked():
                self.lock_button.config(text="解锁悬浮窗")
            else:
                self.lock_button.config(text="锁定悬浮窗")
                
    def floating_window_closed(self):
        self.show_floating_button.config(text="显示悬浮窗")
        self.lock_button.config(text="锁定悬浮窗", state=tk.DISABLED)
        self.log_message("悬浮窗已关闭")

    def on_closing(self):
        self.log_message("正在关闭程序...")
        self.save_settings()
        self.should_stop = True
        if self.connected:
            self.disconnect_device()
        if self.vrc_connected:
            self.vrc_osc_client.disconnect()
        if self.api_server and self.api_server.httpd:
            self.api_server.stop()
        if self.floating_window.is_open():
            self.floating_window.close_window()
        self.root.destroy()
        
    def scan_devices(self):
        self.scan_button.config(state=tk.DISABLED, text="扫描中...")
        self.log_message("开始扫描蓝牙设备...")
        threading.Thread(target=self._scan_devices_thread, daemon=True).start()

    def _scan_devices_thread(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            devices = loop.run_until_complete(self._scan_bluetooth_devices())
            self.root.after(0, self._show_device_selection, devices)
        except Exception as e:
            self.log_message(f"扫描失败: {str(e)}")
            self.root.after(0, lambda: self.scan_button.config(state=tk.NORMAL, text="扫描设备"))

    async def _scan_bluetooth_devices(self):
        from bleak import BleakScanner
        self.log_message("正在扫描蓝牙设备...")
        devices = await BleakScanner.discover(timeout=10.0)
        self.log_message(f"发现 {len(devices)} 个设备")
        return devices

    def _show_device_selection(self, devices):
        self.scan_button.config(state=tk.NORMAL, text="扫描设备")
        if not devices:
            messagebox.showwarning("扫描结果", "未发现任何蓝牙设备")
            return
        
        selection_window = tk.Toplevel(self.root)
        selection_window.title("选择设备")
        selection_window.geometry("500x400")
        selection_window.transient(self.root)
        selection_window.grab_set()
        
        frame = ttk.Frame(selection_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=("Consolas", 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        for device in devices:
            listbox.insert(tk.END, f"{device.name or '未知设备'} ({device.address})")
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                selected_device = devices[selection[0]]
                self.current_mac = selected_device.address
                self.device_label.config(text=f"MAC: {selected_device.address}")
                self.connect_button.config(state=tk.NORMAL)
                self.log_message(f"选择设备: {selected_device.name or '未知'} ({selected_device.address})")
                selection_window.destroy()
            else:
                messagebox.showwarning("选择设备", "请选择一个设备")
        
        ttk.Button(button_frame, text="确定", command=on_select).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="取消", command=selection_window.destroy).pack(side=tk.RIGHT, padx=(5, 0))

    def connect_device(self):
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
        self.ble_thread = threading.Thread(target=self._connect_ble_thread, daemon=True)
        self.ble_thread.start()

    def _connect_ble_thread(self):
        try:
            self.ble_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.ble_loop)
            self.ble_loop.run_until_complete(self._run_heart_rate_monitor())
        except Exception as e:
            self.log_message(f"连接失败: {str(e)}")
            self.root.after(0, self._on_disconnect)

    async def _run_heart_rate_monitor(self):
        def heart_rate_callback(characteristic, data):
            if self.should_stop: return
            try:
                value = 0
                if len(data) >= 2:
                    if data[0] & 0x01: value = int.from_bytes(data[1:3], byteorder='little')
                    else: value = data[1]
                else:
                    hex_data = data.hex()
                    if '06' in hex_data: value = int(hex_data.split('06')[1], 16)
                if value > 0:
                    self.heart_rate_queue.put(value)
            except Exception as e:
                self.log_message(f"解析心率数据失败: {str(e)}")
        
        self.root.after(0, self._on_connect)
        try:
            await self._run_custom_heart_rate_monitor(self.current_mac, heart_rate_callback)
        finally:
            if not self.should_stop:
                self.root.after(0, self._on_disconnect)

    async def _run_custom_heart_rate_monitor(self, mac, callback):
        from bleak import BleakClient
        disconnected_event = asyncio.Event()
        def disconnected_callback(client):
            self.log_message("设备连接断开")
            disconnected_event.set()
        async with BleakClient(mac, disconnected_callback=disconnected_callback, timeout=15.0) as client:
            self.log_message("设备连接成功")
            hr_uuid = await self._find_heart_rate_characteristics(client)
            if hr_uuid:
                self.log_message(f"找到心率特征: {hr_uuid}")
                await client.start_notify(hr_uuid, callback)
                self.log_message("开始接收心率数据")
                while not self.should_stop and not disconnected_event.is_set():
                    await asyncio.sleep(0.1)
                try: await client.stop_notify(hr_uuid)
                except: pass
            else:
                self.log_message("未找到心率特征")
                raise Exception("未找到心率特征")

    async def _find_heart_rate_characteristics(self, client):
        uuid_map = { "service": "0000180d-0000-1000-8000-00805f9b34fb", "measurement": "00002a37-0000-1000-8000-00805f9b34fb" }
        for service in client.services:
            if service.uuid.lower() == uuid_map["service"]:
                for char in service.characteristics:
                    if char.uuid.lower() == uuid_map["measurement"]: return char.uuid
        for service in client.services:
            for char in service.characteristics:
                if any(k in char.description.lower() for k in ['heart rate', 'hr']): return char.uuid
        return None

    def _on_connect(self):
        self.connected = True
        self.status_label.config(text="状态: 已连接", fg="green")
        self.log_message("设备连接成功，开始监控心率")

    def _on_disconnect(self):
        self.connected = False
        self.status_label.config(text="状态: 未连接", fg="gray")
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.heart_rate_label.config(text="心率: --", fg="red")
        self.heart_rate_queue.put(0) 
        self.log_message("设备已断开连接")

    def disconnect_device(self):
        self.should_stop = True
        if self.ble_loop and not self.ble_loop.is_closed() and self.ble_loop.is_running():
            self.ble_loop.call_soon_threadsafe(self.ble_loop.stop)
        self._on_disconnect()
        self.log_message("手动断开连接")

    def run(self):
        self.log_message("心率监控器启动")
        self.log_message("游戏悬浮显示工具 - 支持透明悬浮窗和点击穿透")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    app = HeartRateMonitor()
    app.run()

if __name__ == "__main__":
    main()