# floating_window.py

import tkinter as tk
import sys

class FloatingWindow:
    """悬浮窗类"""
    def __init__(self, heart_rate_monitor):
        self.heart_rate_monitor = heart_rate_monitor
        self.window = None
        self.locked = False
        self.dragging = False
        self.start_x = 0
        self.start_y = 0
        
    def create_window(self):
        """创建悬浮窗"""
        if self.window:
            return
            
        # 修复 #1: 明确将悬浮窗与主窗口关联
        self.window = tk.Toplevel(self.heart_rate_monitor.root)
        self.window.title("心率悬浮窗")
        self.window.geometry("150x60+100+100")
        
        # 使用无边框和置顶属性
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        
        # 设置窗口背景为透明
        self.window.configure(bg="black")
        self.window.attributes("-transparentcolor", "black")
        
        # 心率显示标签
        self.heart_rate_label = tk.Label(
            self.window,
            text="心率: --",
            font=("Arial", 18, "bold"),
            fg="#00FF00",  # 绿色
            bg="black"
        )
        self.heart_rate_label.pack(expand=True, fill="both")
        
        # 创建右键菜单
        self.create_context_menu()
        
        # 绑定拖拽事件
        self.bind_drag_events()
        
        # 窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # 初始化窗口为解锁状态（可点击）
        # 在窗口创建后调用，确保句柄(hwnd)已生成
        self.window.after(100, lambda: self.set_click_through(False))

    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="锁定/解锁", command=self.toggle_lock)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="关闭悬浮窗", command=self.close_window)
        
        def show_context_menu(event):
            if not self.locked:
                try:
                    self.context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    self.context_menu.grab_release()
        
        self.heart_rate_label.bind("<Button-3>", show_context_menu)
        
    def bind_drag_events(self):
        """绑定拖拽事件"""
        def start_drag(event):
            if not self.locked:
                self.dragging = True
                self.start_x = event.x
                self.start_y = event.y
                
        def on_drag(event):
            if self.dragging and not self.locked and self.window is not None:
                try:
                    x = self.window.winfo_x() + event.x - self.start_x
                    y = self.window.winfo_y() + event.y - self.start_y
                    self.window.geometry(f"+{x}+{y}")
                except tk.TclError:
                    self.dragging = False
                
        def stop_drag(event):
            self.dragging = False
            
        self.heart_rate_label.bind("<Button-1>", start_drag)
        self.heart_rate_label.bind("<B1-Motion>", on_drag)
        self.heart_rate_label.bind("<ButtonRelease-1>", stop_drag)
        
    def set_click_through(self, enable):
        """设置点击穿透 (仅Windows)"""
        # 修复 #2: 彻底重构此函数以避免与Tkinter冲突
        if not self.window:
            return
            
        if sys.platform != "win32":
            if enable:
                self.heart_rate_monitor.log_message("警告: 点击穿透功能仅在Windows上受支持。")
            return

        try:
            import ctypes
            
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x80000
            WS_EX_TRANSPARENT = 0x20
            
            hwnd = self.window.winfo_id()
            current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            if enable:
                # 启用穿透 (添加 WS_EX_TRANSPARENT 样式)
                new_style = current_style | WS_EX_TRANSPARENT
            else:
                # 禁用穿透 (移除 WS_EX_TRANSPARENT 样式)
                new_style = current_style & ~WS_EX_TRANSPARENT
            
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            # 确保窗口更新其样式
            ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 255, 0x2)

        except Exception as e:
            self.heart_rate_monitor.log_message(f"设置点击穿透失败: {e}")
            
    def toggle_lock(self):
        """切换锁定状态"""
        self.locked = not self.locked
        self.set_click_through(self.locked)
        
        if self.locked:
            self.heart_rate_label.config(fg="#FF6600")  # 橙色表示锁定
            self.heart_rate_monitor.log_message("悬浮窗已锁定 - 橙色显示")
        else:
            self.heart_rate_label.config(fg="#00FF00")  # 绿色表示解锁
            self.heart_rate_monitor.log_message("悬浮窗已解锁 - 绿色显示")
            
    def update_heart_rate(self, heart_rate):
        """更新心率显示"""
        if self.window and self.heart_rate_label:
            if heart_rate > 0:
                text = f"心率: {heart_rate}"
            else:
                text = "心率: --"
            self.heart_rate_label.config(text=text)
            
    def close_window(self):
        """关闭悬浮窗"""
        if self.window:
            self.window.destroy()
            self.window = None
            self.heart_rate_monitor.floating_window_closed()
            
    def is_open(self):
        """检查悬浮窗是否打开"""
        return self.window is not None