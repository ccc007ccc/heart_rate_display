# floating_window.py

import tkinter as tk
import ctypes

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
            
        self.window = tk.Toplevel()
        self.window.title("心率悬浮窗")
        self.window.geometry("150x60+100+100")
        self.window.attributes("-topmost", True)
        self.window.overrideredirect(True)  # 无边框
        self.window.attributes("-transparentcolor", "black")
        self.window.configure(bg="black")
        
        # 心率显示标签
        self.heart_rate_label = tk.Label(
            self.window,
            text="心率: --",
            font=("Arial", 18, "bold"),
            fg="#00FF00",  # 绿色
            bg="black"
        )
        self.heart_rate_label.pack(expand=True, fill="both")
        
        # 右键菜单
        self.create_context_menu()
        
        # 绑定拖拽事件
        self.bind_drag_events()
        
        # 设置窗口穿透（默认不穿透，解锁状态）
        self.set_click_through(False)
        
        # 窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
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
                    # 防止窗口已被销毁但事件仍在触发的情况
                    self.dragging = False
                
        def stop_drag(event):
            self.dragging = False
            
        self.heart_rate_label.bind("<Button-1>", start_drag)
        self.heart_rate_label.bind("<B1-Motion>", on_drag)
        self.heart_rate_label.bind("<ButtonRelease-1>", stop_drag)
        
    def set_click_through(self, enable):
        """设置点击穿透"""
        if not self.window:
            return
            
        try:
            hwnd = self.window.winfo_id()
            
            # Windows API常量
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x80000
            WS_EX_TRANSPARENT = 0x20
            WS_EX_TOPMOST = 0x8
            
            # 获取当前窗口样式
            current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            if enable:
                # 启用穿透
                new_style = current_style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST
            else:
                # 禁用穿透
                new_style = current_style | WS_EX_LAYERED | WS_EX_TOPMOST
                new_style = new_style & ~WS_EX_TRANSPARENT
                
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
        except Exception as e:
            print(f"设置点击穿透失败: {e}")
            
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