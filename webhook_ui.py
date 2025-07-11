# webhook_ui.py

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
from typing import Optional

class WebhookWindow(tk.Toplevel):
    """
    Webhook管理的独立窗口
    """
    def __init__(self, master, webhook_manager):
        super().__init__(master)
        self.webhook_manager = webhook_manager
        self.selected_index: Optional[int] = None

        self.title("Webhook 设置")
        self.geometry("800x600")
        self.minsize(600, 450)
        
        self.transient(master)
        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- UI ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # 左侧列表区域
        list_frame = ttk.LabelFrame(main_frame, text="Webhook 预设", padding="10")
        list_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.columnconfigure(1, weight=1)
        
        self.listbox = tk.Listbox(list_frame, exportselection=False)
        self.listbox.grid(row=0, column=0, columnspan=2, sticky="nswe")
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        
        btn_grid = ttk.Frame(list_frame)
        btn_grid.grid(row=1, column=0, columnspan=2, pady=(10,0), sticky="ew")
        btn_grid.columnconfigure((0,1), weight=1)

        ttk.Button(btn_grid, text="新增", command=self.new_webhook).grid(row=0, column=0, sticky="ew", padx=(0,2))
        self.delete_button = ttk.Button(btn_grid, text="删除", command=self.delete_webhook, state=tk.DISABLED)
        self.delete_button.grid(row=0, column=1, sticky="ew", padx=(2,0))
        
        # [修改] 新增同步按钮
        ttk.Button(list_frame, text="同步官方预设", command=self.sync_webhooks).grid(row=2, column=0, columnspan=2, pady=(5,0), sticky="ew")

        # 右侧编辑区域
        edit_frame = ttk.Frame(main_frame)
        edit_frame.grid(row=0, column=1, sticky="nsew")
        edit_frame.rowconfigure(1, weight=1) # Body
        edit_frame.rowconfigure(3, weight=1) # Headers
        edit_frame.rowconfigure(5, weight=1) # Response
        edit_frame.columnconfigure(0, weight=1)
        
        details_frame = ttk.LabelFrame(edit_frame, text="预设详情", padding="10")
        details_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        details_frame.columnconfigure(1, weight=1)
        
        self.enabled_var = tk.BooleanVar()
        self.name_var = tk.StringVar()
        self.url_var = tk.StringVar()

        ttk.Checkbutton(details_frame, text="启用此 Webhook", variable=self.enabled_var).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        ttk.Label(details_frame, text="名称:").grid(row=1, column=0, sticky="w")
        ttk.Entry(details_frame, textvariable=self.name_var).grid(row=1, column=1, sticky="ew", padx=(5,0))
        ttk.Label(details_frame, text="URL:").grid(row=2, column=0, sticky="w", pady=(5,0))
        ttk.Entry(details_frame, textvariable=self.url_var).grid(row=2, column=1, sticky="ew", padx=(5,0), pady=(5,0))
        
        ttk.Label(details_frame, text="Body (JSON):").grid(row=3, column=0, sticky="nw", pady=(10,0))
        self.body_text = tk.Text(details_frame, height=6, font=("Consolas", 9))
        self.body_text.grid(row=3, column=1, sticky="nsew", padx=(5,0), pady=(10,0))
        details_frame.rowconfigure(3, weight=1)
        
        ttk.Label(details_frame, text="Headers (JSON):").grid(row=4, column=0, sticky="nw", pady=(10,0))
        self.headers_text = tk.Text(details_frame, height=4, font=("Consolas", 9))
        self.headers_text.grid(row=4, column=1, sticky="nsew", padx=(5,0), pady=(10,0))

        response_frame = ttk.LabelFrame(edit_frame, text="测试响应日志", padding="10")
        response_frame.grid(row=4, column=0, sticky="nsew", pady=(10,0))
        response_frame.columnconfigure(0, weight=1)
        response_frame.rowconfigure(0, weight=1)
        self.response_log = scrolledtext.ScrolledText(response_frame, height=5, font=("Consolas", 9), state="disabled")
        self.response_log.pack(fill="both", expand=True)

        button_frame = ttk.Frame(edit_frame)
        button_frame.grid(row=5, column=0, sticky="sew", pady=(10,0))
        button_frame.columnconfigure(0, weight=1)
        
        action_button_frame = ttk.Frame(button_frame)
        action_button_frame.pack(side="right")
        
        ttk.Button(action_button_frame, text="测试发送", command=self.test_webhook).pack(side="left", padx=5)
        ttk.Button(action_button_frame, text="保存更改", command=self.save_webhook).pack(side="left")
        
        self.webhook_manager.response_logger = self.log_to_response_window
        
        self.load_webhooks_into_listbox()
        self.clear_form()

    # [新增] 同步功能
    def sync_webhooks(self):
        if messagebox.askyesno("确认同步", "这将从GitHub下载官方预设，并覆盖你本地的 `config_webhook.json` 文件。\n\n你所有自定义的Webhook都将丢失。确定要继续吗？"):
            success, message = self.webhook_manager.sync_from_github()
            messagebox.showinfo("同步结果", message)
            if success:
                self.load_webhooks_into_listbox()
                self.clear_form()

    def log_to_response_window(self, message):
        def _task():
            self.response_log.config(state="normal")
            self.response_log.insert(tk.END, message + "\n\n")
            self.response_log.see(tk.END)
            self.response_log.config(state="disabled")
        self.after(0, _task)
        
    def load_webhooks_into_listbox(self):
        self.listbox.delete(0, tk.END)
        for i, hook in enumerate(self.webhook_manager.get_webhooks()):
            status = "✓" if hook.get("enabled") else "✗"
            self.listbox.insert(tk.END, f"[{status}] {hook.get('name', '未命名')}")

    def on_listbox_select(self, event=None):
        selections = self.listbox.curselection()
        if not selections:
            return
        self.selected_index = selections[0]
        self.delete_button.config(state=tk.NORMAL)
        
        config = self.webhook_manager.get_webhooks()[self.selected_index]
        
        self.enabled_var.set(config.get("enabled", False))
        self.name_var.set(config.get("name", ""))
        self.url_var.set(config.get("url", ""))
        
        self.body_text.delete(1.0, tk.END)
        self.body_text.insert(1.0, config.get("body", "{\n    \"bpm\": \"{bpm}\"\n}"))
        
        self.headers_text.delete(1.0, tk.END)
        self.headers_text.insert(1.0, config.get("headers", "{\n    \"Content-Type\": \"application/json\"\n}"))
        
    def clear_form(self):
        self.selected_index = None
        self.listbox.selection_clear(0, tk.END)
        self.delete_button.config(state=tk.DISABLED)
        
        self.enabled_var.set(False)
        self.name_var.set("")
        self.url_var.set("")
        self.body_text.delete(1.0, tk.END)
        self.body_text.insert(1.0, "{\n    \"bpm\": \"{bpm}\"\n}")
        self.headers_text.delete(1.0, tk.END)
        self.headers_text.insert(1.0, "{\n    \"Content-Type\": \"application/json\"\n}")

    def new_webhook(self):
        self.clear_form()

    def delete_webhook(self):
        if self.selected_index is None:
            return
        name = self.name_var.get() or "此预设"
        if messagebox.askyesno("确认删除", f"确定要删除 '{name}' 吗？此操作无法撤销。"):
            self.webhook_manager.delete_webhook(self.selected_index)
            self.load_webhooks_into_listbox()
            self.clear_form()

    def get_config_from_form(self):
        body = self.body_text.get(1.0, tk.END).strip()
        headers = self.headers_text.get(1.0, tk.END).strip()
        
        try:
            # 检查是否为空，如果为空则视为空JSON对象
            if not body: body = "{}"
            if not headers: headers = "{}"
            json.loads(body)
            json.loads(headers)
        except json.JSONDecodeError as e:
            messagebox.showerror("格式错误", f"Body或Headers不是有效的JSON格式: {e}")
            return None
            
        return {
            "enabled": self.enabled_var.get(),
            "name": self.name_var.get() or "未命名",
            "url": self.url_var.get(),
            "body": body,
            "headers": headers
        }

    def save_webhook(self):
        config = self.get_config_from_form()
        if config:
            # save_webhook 现在会自己调用 save_webhooks
            self.webhook_manager.save_webhook(self.selected_index, config)
            self.load_webhooks_into_listbox()
            # 重新选中刚保存的项
            if self.selected_index is not None:
                self.listbox.selection_set(self.selected_index)
            messagebox.showinfo("成功", f"Webhook '{config['name']}' 已保存。")
    
    def test_webhook(self):
        config = self.get_config_from_form()
        if config:
            self.webhook_manager.test_webhook(config)

    def on_closing(self):
        # [修改] 不再调用主窗口的保存，因为 manager 自己会保存
        # self.webhook_manager.save_webhooks() 
        self.destroy()