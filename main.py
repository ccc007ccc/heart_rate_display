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
    parser.add_argument('--scan', action='store_true', help='仅扫描设备')
    
    args = parser.parse_args()
    
    if args.scan:
        # 仅扫描设备
        from get_heart_rate.heart_rate_tool import scan_and_select_device
        asyncio.run(scan_and_select_device())
        
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