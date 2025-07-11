# webhook_manager.py

import threading
import json
import os
from urllib import request, error
from typing import Callable, Optional, List, Dict

# 定义 Webhook 的独立配置文件
WEBHOOK_CONFIG_FILE = "config_webhook.json"
# 定义 GitHub 仓库中的预设文件 URL
GITHUB_CONFIG_URL = "https://raw.githubusercontent.com/ccc007ccc/HeartRateMonitor/main/config_webhook.json"

class WebhookManager:
    """
    管理所有Webhook的加载、保存和发送。
    现在直接读写独立的 config_webhook.json 文件。
    """
    def __init__(self, logger_func: Callable[[str], None], response_logger: Optional[Callable[[str], None]] = None):
        self.logger = logger_func
        self.response_logger = response_logger
        self.webhooks: List[Dict] = []
        self.load_webhooks() # 初始化时即加载

    def load_webhooks(self):
        """从 config_webhook.json 加载Webhook列表"""
        if not os.path.exists(WEBHOOK_CONFIG_FILE):
            self.webhooks = []
            self.logger("未找到 Webhook 配置文件，已初始化为空列表。")
            return
        try:
            with open(WEBHOOK_CONFIG_FILE, "r", encoding="utf-8") as f:
                self.webhooks = json.load(f)
            self.logger(f"从 {WEBHOOK_CONFIG_FILE} 加载了 {len(self.webhooks)} 个 Webhook 配置。")
        except (json.JSONDecodeError, IOError) as e:
            self.webhooks = []
            self.logger(f"加载 {WEBHOOK_CONFIG_FILE} 失败: {e}")

    def save_webhooks(self):
        """将当前Webhook列表保存到 config_webhook.json"""
        try:
            with open(WEBHOOK_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.webhooks, f, indent=4, ensure_ascii=False)
            self.logger(f"已将 {len(self.webhooks)} 个 Webhook 配置保存到 {WEBHOOK_CONFIG_FILE}。")
        except IOError as e:
            self.logger(f"保存 {WEBHOOK_CONFIG_FILE} 失败: {e}")

    def get_webhooks(self) -> List[Dict]:
        """获取所有Webhook配置"""
        return self.webhooks

    def save_webhook(self, index: Optional[int], config: Dict):
        """保存或新增一个Webhook配置"""
        if index is None:
            self.webhooks.append(config)
            self.logger(f"新增 Webhook: {config.get('name')}")
        else:
            self.webhooks[index] = config
            self.logger(f"更新 Webhook: {config.get('name')}")
        self.save_webhooks() # 每次更改后自动保存

    def delete_webhook(self, index: int):
        """删除一个Webhook配置"""
        if 0 <= index < len(self.webhooks):
            removed = self.webhooks.pop(index)
            self.logger(f"删除 Webhook: {removed.get('name')}")
            self.save_webhooks() # 每次更改后自动保存

    def sync_from_github(self) -> tuple[bool, str]:
        """从GitHub下载最新的预设文件并覆盖本地文件"""
        self.logger("开始从 GitHub 同步 Webhook 预设...")
        try:
            req = request.Request(GITHUB_CONFIG_URL, headers={'User-Agent': 'HeartRateMonitor-App'})
            with request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    content = response.read().decode('utf-8')
                    # 验证下载的内容是合法的JSON
                    json.loads(content)
                    with open(WEBHOOK_CONFIG_FILE, "w", encoding="utf-8") as f:
                        f.write(content)
                    self.logger("成功从 GitHub 同步并覆盖了本地 Webhook 配置文件。")
                    self.load_webhooks() # 同步后重新加载
                    return True, "同步成功！已从GitHub获取最新的官方预设。"
                else:
                    msg = f"同步失败: GitHub 服务器返回状态码 {response.status}"
                    self.logger(msg)
                    return False, msg
        except Exception as e:
            msg = f"同步过程中发生错误: {e}"
            self.logger(msg)
            return False, msg

    def send_all_enabled_webhooks(self, heart_rate: int):
        """向所有启用的Webhook发送心率数据"""
        for config in self.webhooks:
            if config.get("enabled", False):
                thread = threading.Thread(target=self._send_request, args=(config, heart_rate), daemon=True)
                thread.start()

    def test_webhook(self, config: Dict):
        """测试单个Webhook配置"""
        self.logger(f"正在测试 Webhook: {config.get('name')}")
        test_heart_rate = 88 
        thread = threading.Thread(target=self._send_request, args=(config, test_heart_rate, True), daemon=True)
        thread.start()

    def _send_request(self, config: Dict, heart_rate: int, is_test: bool = False):
        """执行HTTP请求的内部方法"""
        def log_response(message):
            if is_test and self.response_logger:
                self.response_logger(message)
            else:
                self.logger(message)

        try:
            bpm_str = str(heart_rate)
            
            url = config.get("url", "").replace("{bpm}", bpm_str)
            if not url.startswith(('http://', 'https://')):
                log_response(f"[{config.get('name')}] 发送失败: 无效的URL。")
                return

            headers_str = config.get("headers", "{}").replace("{bpm}", bpm_str)
            body_str = config.get("body", "{}").replace("{bpm}", bpm_str)

            headers = json.loads(headers_str)
            if 'User-Agent' not in headers:
                headers['User-Agent'] = 'HeartRateMonitor-Webhook'
            if 'Content-Type' not in headers:
                 headers['Content-Type'] = 'application/json'
                 
            data = body_str.encode('utf-8')

            req = request.Request(url, data=data, headers=headers, method='POST')

            with request.urlopen(req, timeout=10) as response:
                response_body = response.read().decode('utf-8', errors='ignore')
                log_response(
                    f"--- Webhook 测试响应 ---\n"
                    f"名称: {config.get('name')}\n"
                    f"状态码: {response.status} {response.reason}\n"
                    f"响应体:\n{response_body}\n"
                    f"----------------------"
                )
        except json.JSONDecodeError as e:
            log_response(f"[{config.get('name')}] 发送失败: Headers 或 Body 的 JSON 格式错误: {e}")
        except error.HTTPError as e:
            log_response(
                f"--- Webhook 测试响应 (HTTP错误) ---\n"
                f"名称: {config.get('name')}\n"
                f"状态码: {e.code} {e.reason}\n"
                f"响应体:\n{e.read().decode('utf-8', errors='ignore') if e.fp else '无响应体'}\n"
                f"-----------------------------"
            )
        except error.URLError as e:
            log_response(f"[{config.get('name')}] 发送失败 (URL错误): {e.reason}")
        except Exception as e:
            log_response(f"[{config.get('name')}] 发送时发生未知错误: {e}")