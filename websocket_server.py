# websocket_server.py

import asyncio
import json
import threading
from typing import Set, Optional, Callable, TYPE_CHECKING
import websockets
from websockets.server import ServerProtocol

if TYPE_CHECKING:
    from heart_rate_display_ui import HeartRateMonitor


class WebSocketServer:
    """
    运行在独立线程中的WebSocket服务器，用于实时推送心率数据。
    """

    def __init__(self, monitor_instance: 'HeartRateMonitor', port: int, logger_func: Callable[[str], None]):
        self.monitor_instance = monitor_instance
        self.port = port
        self.logger = logger_func
        self.server_thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.server = None
        self.connected_clients: Set[ServerProtocol] = set()

    # [修正] 从函数签名中移除未使用的 'path' 参数，以解决 TypeError
    async def _handler(self, websocket: ServerProtocol):
        """处理新的客户端连接和消息"""
        self.connected_clients.add(websocket)
        self.logger(f"[WebSocket] 客户端连接: {websocket.remote_address}") # type: ignore
        try:
            # 发送当前状态
            await self.send_data(websocket)
            # 持续监听，直到客户端断开
            async for message in websocket: # type: ignore
                pass
        except websockets.exceptions.ConnectionClosed:
            self.logger(f"[WebSocket] 客户端断开连接: {websocket.remote_address}") # type: ignore
        finally:
            # 确保即使在发生异常时也能移除客户端
            if websocket in self.connected_clients:
                self.connected_clients.remove(websocket)

    async def _run_server(self):
        """启动WebSocket服务器的异步任务"""
        try:
            async with websockets.serve(self._handler, "0.0.0.0", self.port) as server: # type: ignore
                self.server = server
                self.logger(f"WebSocket 服务器已在 ws://0.0.0.0:{self.port} 启动")
                await server.wait_closed()
        except OSError as e:
            self.logger(f"[WebSocket] 服务器启动失败: {e}. 端口可能已被占用。")
        except Exception as e:
            self.logger(f"[WebSocket] 服务器发生未知错误: {e}")

    def _start_server_thread(self):
        """在新的事件循环和线程中运行服务器"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._run_server())

    def start(self):
        """在独立线程中启动WebSocket服务器"""
        if self.server_thread and self.server_thread.is_alive():
            self.logger("[WebSocket] 服务器已在运行中。")
            return
        self.server_thread = threading.Thread(target=self._start_server_thread, daemon=True)
        self.server_thread.start()

    def stop(self):
        """停止WebSocket服务器"""
        if self.server and self.loop:
            self.logger("[WebSocket] 正在停止服务器...")
            # 优雅地关闭所有客户端连接
            for client in self.connected_clients:
                self.loop.call_soon_threadsafe(asyncio.create_task, client.close()) # type: ignore

            # 停止服务器
            self.loop.call_soon_threadsafe(self.server.close)

            # 等待服务器完全关闭
            if self.server_thread:
                 self.server_thread.join(timeout=2)

        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

        self.logger("[WebSocket] 服务器已停止。")
        self.server = None
        self.server_thread = None
        self.loop = None

    async def send_data(self, websocket: ServerProtocol):
        """向单个客户端发送当前的心率数据"""
        data = {
            "heart_rate": self.monitor_instance.heart_rate,
            "connected": self.monitor_instance.connected,
            "status": "connected" if self.monitor_instance.connected else "disconnected"
        }
        try:
            await websocket.send(json.dumps(data)) # type: ignore
        except websockets.exceptions.ConnectionClosed:
            pass # 连接已关闭，无需处理

    def broadcast(self):
        """向所有连接的客户端广播心率数据"""
        if not self.connected_clients or not self.loop:
            return

        # 使用 call_soon_threadsafe 从主线程安排协程在服务器的事件循环中执行
        for client in list(self.connected_clients):
            self.loop.call_soon_threadsafe(
                asyncio.create_task, self.send_data(client)
            )