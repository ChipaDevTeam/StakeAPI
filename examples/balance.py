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
    user_agent = os.getenv("STAKE_USER_AGENT")
    async with StakeAPI(access_token=access_token, session_cookie=session_cookie, cf_clearance=cf_clearance, user_agent=user_agent) as client:
        
        # 1. Get your balance
        balance = await client.get_user_balance()
        print("Raw response:", balance)
        print("\n💰 Your Balance:")
        if balance["available"]:
            for currency, amount in balance["available"].items():
                if amount > 0:
                    print(f"  {currency.upper()}: {amount}")
            if not any(amount > 0 for amount in balance["available"].values()):
                print("  (all balances are 0)")
        else:
            print("  (no balance data returned)")

asyncio.run(main())
