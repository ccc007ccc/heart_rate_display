# api_server.py

import http.server
import socketserver
import threading
import json
from typing import TYPE_CHECKING, Optional

# 使用类型检查来避免循环导入，同时获得代码提示
if TYPE_CHECKING:
    from heart_rate_display_ui import HeartRateMonitor

class HeartRateApiHandler(http.server.BaseHTTPRequestHandler):
    """处理HTTP请求的处理器"""
    
    # [修正1] 使用 Optional 允许类型为 None
    heart_rate_monitor_instance: Optional['HeartRateMonitor'] = None

    def do_GET(self):
        if self.path == '/heartrate':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*') # 允许跨域请求
            self.end_headers()
            
            # 从主程序实例获取当前心率 (这里的代码因为有判断，所以本身是安全的)
            current_heart_rate = self.heart_rate_monitor_instance.heart_rate if self.heart_rate_monitor_instance else 0
            is_connected = self.heart_rate_monitor_instance.connected if self.heart_rate_monitor_instance else False
            
            response = {
                'heart_rate': current_heart_rate,
                'connected': is_connected
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    def log_message(self, format, *args):
        pass  # 禁用默认日志输出

class ApiServer:
    """运行在独立线程中的API服务器"""
    def __init__(self, monitor_instance: 'HeartRateMonitor', port=8080):
        self.port = port
        self.monitor_instance = monitor_instance
        self.httpd: Optional[socketserver.ThreadingTCPServer] = None
        self.server_thread: Optional[threading.Thread] = None

    def start(self):
        """启动服务器"""
        if self.server_thread and self.server_thread.is_alive():
            self.monitor_instance.log_message("API服务器已在运行中。")
            return

        # 将主程序实例传递给请求处理器
        handler = HeartRateApiHandler
        handler.heart_rate_monitor_instance = self.monitor_instance
        
        try:
            # 使用 ThreadingTCPServer 以便能正确关闭
            self.httpd = socketserver.ThreadingTCPServer(("", self.port), handler)
            self.server_thread = threading.Thread(target=self.httpd.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            self.monitor_instance.log_message(f"API服务器已在 http://127.0.0.1:{self.port} 启动")
        except Exception as e:
            self.monitor_instance.log_message(f"启动API服务器失败: {e}")
            self.httpd = None
            self.server_thread = None

    def stop(self):
        """停止服务器"""
        if self.httpd:
            self.monitor_instance.log_message("正在停止API服务器...")
            self.httpd.shutdown()
            self.httpd.server_close()
            
            # [修正2] 在调用 join 之前检查线程对象是否存在
            if self.server_thread:
                self.server_thread.join(timeout=2)

            self.httpd = None
            self.server_thread = None
            self.monitor_instance.log_message("API服务器已停止。")