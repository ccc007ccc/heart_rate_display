# floating_window.py

import tkinter as tk
import sys
import re
from typing import Optional
from PIL import Image, ImageTk

class FloatingWindow:
    """
    悬浮窗类
    - 支持使用 {bpm} 和 {img} 占位符自定义显示格式。
    - 支持加载并显示图片。
    """
    def __init__(self, heart_rate_monitor):
        self.heart_rate_monitor = heart_rate_monitor
        self.window: Optional[tk.Toplevel] = None
        self.locked = False
        
        self.dragging = False
        self.start_x = 0
        self.start_y = 0

        self.last_geometry = "200x80+100+100"
        self.display_format = "❤️{bpm}"
        self.image_path: Optional[str] = None
        self.image_original: Optional[Image.Image] = None
        self.image_tk: Optional[ImageTk.PhotoImage] = None

        self.unlocked_color = "#00FF00"
        self.locked_color = "#FF6600"

        self.content_frame: Optional[tk.Frame] = None
        self.display_widgets: list[dict] = []
        self.bpm_label: Optional[tk.Label] = None

    def create_window(self):
        """创建悬浮窗"""
        if self.window:
            return
            
        self.window = tk.Toplevel(self.heart_rate_monitor.root)
        self.window.title("心率")
        self.window.geometry(self.last_geometry)
        
        self.content_frame = tk.Frame(self.window, bg="black")
        self.content_frame.pack(expand=True, fill="both")
        
        self.rebuild_display()
        
        self.bind_events()
        
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        self.apply_lock_state()

    def rebuild_display(self):
        """
        根据 display_format 重新构建悬浮窗内容。
        """
        if not self.content_frame:
            return

        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.display_widgets = []
        self.bpm_label = None

        parts = re.split(r'({bpm}|{img})', self.display_format)

        for part in parts:
            if not part:
                continue
            
            if part == "{bpm}":
                label = tk.Label(self.content_frame, text="--")
                label.pack(side=tk.LEFT, padx=0, pady=0)
                self.bpm_label = label
                self.display_widgets.append({'type': 'bpm', 'widget': label})

            elif part == "{img}":
                label = tk.Label(self.content_frame)
                label.pack(side=tk.LEFT, padx=0, pady=0)
                self.display_widgets.append({'type': 'img', 'widget': label})

            else:
                label = tk.Label(self.content_frame, text=part)
                label.pack(side=tk.LEFT, padx=0, pady=0)
                self.display_widgets.append({'type': 'text', 'widget': label})
        
        self._update_font_size()
        self.apply_lock_state()
        self.update_heart_rate(self.heart_rate_monitor.heart_rate)


    def bind_events(self):
        """绑定拖拽和大小调整事件"""
        if not self.window:
            return
        self.window.bind("<Configure>", self._update_font_size)
        
    def _update_font_size(self, event=None):
        """
        [核心修改]
        动态调整字体大小，并为不同类型的文本设置不同字体：
        - {bpm} 使用 "Arial" 粗体，确保数字清晰。
        - 其他文本（包括Emoji）使用系统默认字体 "TkDefaultFont"，以正确显示彩色Emoji。
        """
        if not self.window:
            return
            
        height = self.window.winfo_height()
        new_size = max(10, int(height / 2.5))
        
        # 为心率数字定义一个特殊字体
        bpm_font = ("Arial", new_size, "bold")
        # 为其他文本（包括Emoji）使用默认字体，只改变大小
        text_font = ("TkDefaultFont", new_size)

        if self.image_original and "{img}" in self.display_format:
            try:
                img_h = int(height * 0.5)
                if img_h > 0:
                    ratio = img_h / self.image_original.height
                    img_w = int(self.image_original.width * ratio)
                    if img_w > 0:
                        resized_img = self.image_original.resize((img_w, img_h), Image.Resampling.LANCZOS)
                        self.image_tk = ImageTk.PhotoImage(resized_img)
            except Exception as e:
                self.image_tk = None
                self.heart_rate_monitor.log_message(f"图片缩放失败: {e}")
        else:
            self.image_tk = None

        # 遍历所有组件，应用新的字体大小和图片
        for item in self.display_widgets:
            widget_type = item['type']
            widget = item['widget']
            if widget_type == 'img':
                widget.config(image=self.image_tk)
            elif widget_type == 'bpm':
                # 只对心率数字应用特殊字体
                widget.config(font=bpm_font)
            elif widget_type == 'text':
                # 对普通文本和Emoji应用默认字体
                widget.config(font=text_font)

    def set_image(self, path: Optional[str]):
        """设置并加载图片"""
        self.image_path = path
        if path:
            try:
                self.image_original = Image.open(path)
            except Exception as e:
                self.image_original = None
                self.heart_rate_monitor.log_message(f"加载图片失败: {e}")
        else:
            self.image_original = None
        
        if self.is_open():
            self.rebuild_display()

    def update_format(self, new_format: str):
        """更新显示格式"""
        self.display_format = new_format
        if self.is_open():
            self.rebuild_display()

    def update_heart_rate(self, heart_rate):
        """只更新心率数字Label的文本"""
        if self.is_open() and self.bpm_label:
            text = str(heart_rate) if heart_rate > 0 else "--"
            self.bpm_label.config(text=text)
            
    def close_window(self):
        """关闭悬浮窗"""
        if self.window:
            self.last_geometry = self.window.geometry()
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
        """根据锁定状态设置窗口及所有内部件的属性"""
        if not self.window or not self.content_frame:
            return

        if self.locked:
            color = self.locked_color
            self.window.overrideredirect(True)
            self.window.attributes("-topmost", True)
            self.window.attributes("-transparentcolor", "black")
            self.heart_rate_monitor.log_message(f"悬浮窗已锁定 - {color} 显示")
        else:
            color = self.unlocked_color
            self.window.overrideredirect(False)
            self.window.attributes("-topmost", False)
            self.window.attributes("-transparentcolor", "")
            self.heart_rate_monitor.log_message(f"悬浮窗已解锁 - {color} 显示")
        
        self.content_frame.config(bg="black")
        for item in self.display_widgets:
            widget = item['widget']
            widget.config(bg="black")
            if item['type'] in ['text', 'bpm']:
                if item['type'] == 'bpm':
                    widget.config(fg=color)
                else:
                    widget.config(fg=self.unlocked_color)

    def toggle_lock(self):
        """切换锁定状态"""
        self.locked = not self.locked
        self.apply_lock_state()