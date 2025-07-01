# floating_window.py

import tkinter as tk
import sys
from typing import Optional

class FloatingWindow:
    """悬浮窗类"""
    def __init__(self, heart_rate_monitor):
        self.heart_rate_monitor = heart_rate_monitor
        self.window: Optional[tk.Toplevel] = None
        self.locked = False
        self.dragging = False
        self.start_x = 0
        self.start_y = 0
        self.last_geometry = "200x80+100+100" # Initial size and position

    def create_window(self):
        """创建悬浮窗"""
        if self.window:
            return
            
        self.window = tk.Toplevel(self.heart_rate_monitor.root)
        self.window.title("心率")
        self.window.geometry(self.last_geometry)
        
        # Heart rate display label
        self.heart_rate_label = tk.Label(
            self.window,
            text="❤️--",
            font=("Arial", 18, "bold"),
            bg="black",
        )
        self.heart_rate_label.pack(expand=True, fill="both")
        
        # Bind events
        self.bind_events()
        
        # Window closing event
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Apply the current lock state without toggling
        self.apply_lock_state()


    def bind_events(self):
        """绑定拖拽和大小调整事件"""
        if not self.window:
            return
        # Bind resizing event to adjust font size
        self.window.bind("<Configure>", self._update_font_size)
        
    def _update_font_size(self, event=None):
        """Dynamically adjust font size based on window height."""
        if not self.window:
            return
        # Calculate new font size, ensuring a minimum size
        height = self.window.winfo_height()
        new_size = max(10, int(height / 2.5))
        
        # Update font
        self.heart_rate_label.config(font=("Arial", new_size, "bold"))

    def set_click_through(self, enable):
        """设置点击穿透 (仅Windows)"""
        if not self.window or sys.platform != "win32":
            return

        try:
            import ctypes
            
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x80000
            WS_EX_TRANSPARENT = 0x20
            
            hwnd = self.window.winfo_id()
            current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            if enable:
                new_style = current_style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            else:
                new_style = current_style & ~WS_EX_TRANSPARENT
            
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            # This call is necessary to apply the changes
            ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 255, 0x2)

        except Exception as e:
            self.heart_rate_monitor.log_message(f"设置点击穿透失败: {e}")
            
    def update_heart_rate(self, heart_rate):
        """更新心率显示"""
        if self.window and self.heart_rate_label:
            if heart_rate > 0:
                text = f"❤️{heart_rate}"
            else:
                text = "❤️--"
            self.heart_rate_label.config(text=text)
            
    def close_window(self):
        """关闭悬浮窗"""
        if self.window:
            self.last_geometry = self.window.geometry() # Save position on close
            self.window.destroy()
            self.window = None
            self.heart_rate_monitor.floating_window_closed()
            
    def is_open(self):
        """检查悬浮窗是否打开"""
        return self.window is not None
    
    def is_locked(self):
        """检查悬浮窗是否被锁定"""
        return self.locked

    def apply_lock_state(self):
        """根据当前锁定状态设置窗口属性"""
        if not self.window:
            return

        if self.locked:
            self.window.overrideredirect(True)
            self.window.attributes("-topmost", True)
            self.window.configure(bg="black")
            self.window.attributes("-transparentcolor", "black")
            self.heart_rate_label.config(fg="#FF6600")  # 橙色表示锁定
            self.heart_rate_monitor.log_message("悬浮窗已锁定 - 橙色显示")
            self.locked = True
        else:
            self.window.overrideredirect(False)
            self.window.attributes("-topmost", False)
            self.window.configure(bg="black")
            self.window.attributes("-transparentcolor", "")
            self.heart_rate_label.config(fg="#00FF00")  # 绿色表示解锁
            self.heart_rate_monitor.log_message("悬浮窗已解锁 - 绿色显示")
            self.locked = False

    def toggle_lock(self):
        """切换锁定状态"""
        self.locked = not self.locked
        self.apply_lock_state()
