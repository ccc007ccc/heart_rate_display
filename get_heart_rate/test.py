# test.py

import asyncio
from heart_rate_tool import scan_and_select_device, get_heart_rate

async def main():
    mac = await scan_and_select_device()
    if mac:
        print(mac)

if __name__ == "__main__":
    asyncio.run(main())
