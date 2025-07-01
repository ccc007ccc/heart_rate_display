# heart_rate_tool.py

import asyncio
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

# 心率值全局变量
heart_rate = 0

# 通知回调处理函数
def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray):
    global heart_rate
    try:
        heart_rate = int(data.hex().split('06')[1], 16)
        print(f"当前心率：{heart_rate}")
    except Exception as e:
        print(f"解析心率失败: {e}")

# 查找“Heart Rate Measurement”特征 UUID
async def find_heart_rate_measurement_uuid(client: BleakClient):
    for service in client.services:
        for characteristic in service.characteristics:
            if "Heart Rate Measurement" in characteristic.description:
                return characteristic.uuid
    return None

# 扫描蓝牙设备，供用户选择，返回 MAC 地址
async def scan_and_select_device() -> str:
    print("正在扫描附近的蓝牙设备，请稍候...")
    devices = await BleakScanner.discover()
    if not devices:
        print("未找到任何蓝牙设备。")
        return ''

    for idx, device in enumerate(devices):
        print(f"[{idx}] 设备名: {device.name or '未知'}, MAC地址: {device.address}")

    try:
        idx = int(input("请输入要连接的设备编号: "))
        return devices[idx].address
    except (ValueError, IndexError):
        print("无效的编号。")
        return ''

# 主函数：连接设备并获取心率
async def get_heart_rate(mac: str):
    if not mac:
        print("MAC地址无效。")
        return

    timeout = 10
    disconnected_event = asyncio.Event()

    def disconnected_callback(client):
        print("设备已断开连接。")
        disconnected_event.set()

    print(f"正在连接设备 {mac}...")
    async with BleakClient(mac, disconnected_callback=disconnected_callback, timeout=timeout) as client:
        print("设备已连接。")

        hr_uuid = await find_heart_rate_measurement_uuid(client)
        if hr_uuid:
            print("已找到心率特征，开始接收数据...")
            await client.start_notify(hr_uuid, notification_handler)
            print("按 Ctrl+C 停止程序。")
            try:
                await disconnected_event.wait()
            except KeyboardInterrupt:
                print("用户中断，正在断开连接...")
        else:
            print("未找到心率测量特征。")
