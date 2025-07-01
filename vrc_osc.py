# vrc_osc.py

from pythonosc import udp_client

class VrcOscClient:
    """一个用于向VRChat发送OSC消息的客户端。"""

    def __init__(self, logger_func):
        """
        初始化 VrcOscClient。

        Args:
            logger_func (function): 用于记录日志消息的函数。
        """
        self.client = None
        self.ip = "127.0.0.1"
        self.port = 9000
        self.logger = logger_func

    def connect(self, ip: str, port: int):
        """
        使用目标IP和端口初始化OSC客户端。

        Args:
            ip (str): VRChat客户端的IP地址。
            port (int): VRChat客户端的OSC端口。
        
        Returns:
            tuple[bool, str]: 返回一个元组，包含成功状态和消息。
        """
        self.ip = ip
        self.port = port
        try:
            self.client = udp_client.SimpleUDPClient(self.ip, self.port)
            return True, f"OSC客户端已就绪，将发送至 {self.ip}:{self.port}"
        except Exception as e:
            self.client = None
            return False, f"创建OSC客户端失败: {e}"

    def disconnect(self):
        """断开OSC客户端。"""
        self.client = None

    def is_connected(self) -> bool:
        """检查客户端是否已初始化。"""
        return self.client is not None

    def send_heart_rate(self, heart_rate: int):
        """
        将心率发送到VRChat的聊天框。

        Args:
            heart_rate (int): 要发送的当前心率值。
        """
        # --- UPDATED: 修改此处的判断条件 ---
        # 将 `if not self.is_connected():` 替换为更直接的检查。
        # 这能更好地帮助Pylance理解在此之后self.client不为None。
        if self.client is None:
            self.logger("OSC发送失败：客户端未连接或未初始化。")
            return

        # VRChat聊天框的OSC地址
        address = "/chatbox/input"
        
        # 要显示的消息内容，以及一个布尔值True以使其立即发送
        message = f"❤️ {heart_rate}"
        
        try:
            # 经过上面的判断，Pylance现在可以确定这里的self.client不是None
            self.client.send_message(address, [message, True])
        except Exception as e:
            self.logger(f"发送OSC消息失败: {e}")