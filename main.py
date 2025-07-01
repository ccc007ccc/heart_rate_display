# main.py

"""
心率监控器主启动脚本
支持GUI界面和命令行模式
"""

import sys
import argparse
import asyncio
def main():
    parser = argparse.ArgumentParser(description='心率监控器')
    parser.add_argument('--cli', action='store_true', help='使用命令行模式')
    parser.add_argument('--scan', action='store_true', help='仅扫描设备')
    parser.add_argument('--mac', type=str, help='直接连接指定MAC地址的设备')
    
    args = parser.parse_args()
    
    if args.scan:
        # 仅扫描设备
        from get_heart_rate.heart_rate_tool import scan_and_select_device
        asyncio.run(scan_and_select_device())
        
    elif args.cli or args.mac:
        # 命令行模式
        from get_heart_rate.heart_rate_tool import get_heart_rate, scan_and_select_device
        from config import load_mac, save_mac
        
        async def cli_main():
            if args.mac:
                mac = args.mac
                save_mac(mac)
            else:
                mac = load_mac()
                if not mac:
                    print("未找到已保存的设备，开始扫描...")
                    mac = await scan_and_select_device()
                    if mac:
                        save_mac(mac)
                        
            if mac:
                await get_heart_rate(mac)
            else:
                print("未选择设备，程序退出。")
        
        asyncio.run(cli_main())
        
    else:
        # GUI模式（默认）
        try:
            from heart_rate_display_ui import HeartRateMonitor
            app = HeartRateMonitor()
            app.run()
        except ImportError as e:
            print(f"GUI模式启动失败: {e}")
            print("请确保安装了tkinter库，或使用 --cli 参数运行命令行模式")
            sys.exit(1)

if __name__ == "__main__":
    main()