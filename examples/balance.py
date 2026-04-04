import asyncio
from stakeapi import StakeAPI
import dotenv
import os

dotenv.load_dotenv()

async def main():
    # Replace with your actual access token
    access_token = os.getenv("STAKE_ACCESS_TOKEN")
    session_cookie = os.getenv("STAKE_SESSION_COOKIE")
    cf_clearance = os.getenv("STAKE_CF_CLEARANCE")
    async with StakeAPI(access_token=access_token, session_cookie=session_cookie, cf_clearance=cf_clearance) as client:
        
        # 1. Get your balance
        balance = await client.get_user_balance()
        print("💰 Your Balance:")
        for currency, amount in balance["available"].items():
            if amount > 0:
                print(f"  {currency.upper()}: {amount}")

asyncio.run(main())
