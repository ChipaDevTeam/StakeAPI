"""
Example showing how to extract credentials from curl and use StakeAPI.

This script demonstrates how to extract authentication tokens from a curl command
and use them with the StakeAPI client.
"""

import asyncio
import os
from stakeapi import StakeAPI
from stakeapi.auth import AuthManager
from stakeapi.exceptions import StakeAPIError, AuthenticationError


def extract_credentials_from_curl():
    """
    Extract credentials from the provided curl command.
    """
    curl_command = '''
    curl "https://stake.com/_api/graphql" \
      -H "accept: application/graphql+json, application/json" \
      -H "accept-language: en-US,en;q=0.9,es;q=0.8,fr;q=0.7" \
      -H "content-type: application/json" \
      -b "__cf_bm=0UrVjE2yhtAPLtAjo8sXafWIDosk8CJZtlvTgYGaJ90-1754250710-1.0.1.1-NzAp2m3qW3OVPQMgfhReSSTEWdaZgRJCnaHD91EVW5kKSZ9YpF2K2U2sVi2ID3SgUueODGsfl9sJSbXGjd2USVu5mabjebFTIZ36CYk77qw; _cfuvid=wN5iP_udNioDqe72oYRj3JPSPMk6_BYrTwQMmV96akU-1754250710539-0.0.1.1-604800000; cf_clearance=2qWB3rpISmDKhYCJoEJGu5qwUh8b8AA5qvVMtnSnD2w-1754250712-1.2.1.1-EUpelA_bJtU_toWYxfxNDrYIYfUzvHY.GSfuPv.QiTu82LRX5afzHtRDdLVrcMBIXTUrgQGqr7Wwvsc0q0LVRUkTgQnreSyzlljFLXwYIuJIX1rcyabuPijKSSN09nGqNmtENAcMOq5rN7MOL6au41CcEtJmnVrb89agfqYcn.SSjh6ThgyTBd4RyFP9y3NBFwZMvhLxn6RotmDCeCciBINWmvkTMH1r50XfCflwRHE; locale=en; currency_currency=btc; currency_hideZeroBalances=false; currency_currencyView=crypto; cookie_consent=false; fiat_number_format=en; leftSidebarView_v2=expanded; sidebarView=hidden; oddsFormat=decimal; quick_bet_popup=false; sportMarketGroupMap={}; cookie_last_vip_tab=progress; _ga=GA1.1.1234042555.1754250716; intercom-id-cx1ywgf2=a0d337a5-770b-4dea-a245-5df666428ab9; intercom-device-id-cx1ywgf2=82d3308c-ec2f-4a92-87c5-2ba4f98ae0f4; g_state={\"i_l\":0}; session=2775b505cccaee723e5c705ba552fea7c272f6d20f68d7224eb3ba23446ca295e80a9f1ba23a2dccd9699d93a6f819a4; session_info={\"id\":\"0be02cf3-5eb3-4b04-bbe8-cad69a79cbbb\",\"sessionName\":\"Opera (Windows PC)\",\"ip\":\"190.100.241.134\",\"country\":\"CL\",\"city\":\"Las Condes\",\"active\":true,\"updatedAt\":\"Sun, 03 Aug 2025 19:53:31 GMT\"}; intercom-session-cx1ywgf2=NWEybWV0TXdBdlpuK1VOZFdEWGpTVFlYNVhDTHVwbkJKKzhJaTdHd251WkNyV2wzMnBDZTFwZUlvVHdySDVQNEhUek9KdGlLQVJMdUxMdUFXM215eE1XNGt6eTM5THE5VC94NVV4NVpxaFU9LS1Odk1USUZwQloza1cyR2toWTFGOWVnPT0=--60ddf7c212745988ef200f8fe209bbf56569e865; mp_e29e8d653fb046aa5a7d7b151ecf6f99_mixpanel=%7B%22distinct_id%22%3A%2276e19766-b534-4f94-bad5-e840efca1158%22%2C%22%24device_id%22%3A%2287db344b-2905-4084-b268-0606b0590769%22%2C%22%24initial_referrer%22%3A%22%24direct%22%2C%22%24initial_referring_domain%22%3A%22%24direct%22%2C%22__mps%22%3A%7B%7D%2C%22__mpso%22%3A%7B%7D%2C%22__mpus%22%3A%7B%7D%2C%22__mpa%22%3A%7B%7D%2C%22__mpu%22%3A%7B%7D%2C%22__mpr%22%3A%5B%5D%2C%22__mpap%22%3A%5B%5D%2C%22%24user_id%22%3A%2276e19766-b534-4f94-bad5-e840efca1158%22%7D; fullscreen_preference=false; _dd_s=rum=0&expire=1754251717678; _ga_TWGX3QNXGG=GS2.1.s1754250715$o1$g1$t1754250836$j36$l0$h0" \
      -H "origin: https://stake.com" \
      -H "priority: u=1, i" \
      -H "referer: https://stake.com/" \
      -H "sec-ch-ua: \"Opera GX\";v=\"120\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"" \
      -H "sec-ch-ua-mobile: ?0" \
      -H "sec-ch-ua-platform: \"Windows\"" \
      -H "sec-fetch-dest: empty" \
      -H "sec-fetch-mode: cors" \
      -H "sec-fetch-site: same-origin" \
      -H "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 OPR/120.0.0.0" \
      -H "x-access-token: 2775b505cccaee723e5c705ba552fea7c272f6d20f68d7224eb3ba23446ca295e80a9f1ba23a2dccd9699d93a6f819a4" \
      -H "x-language: en" \
      --data-raw '{"query":"query UserBalances {\n  user {\n    id\n    balances {\n      available {\n        amount\n        currency\n        __typename\n      }\n      vault {\n        amount\n        currency\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n","operationName":"UserBalances"}'
    '''
    
    # Extract access token
    access_token = AuthManager.extract_access_token_from_curl(curl_command)
    
    # Extract session cookie
    session_cookie = AuthManager.extract_session_from_curl(curl_command)
    
    return access_token, session_cookie


async def get_balance_example():
    """
    Example of getting user balance using the real GraphQL API.
    """
    # You can either extract from curl or set manually
    access_token, session_cookie = extract_credentials_from_curl()
    
    # Or set them manually if you have them
    # access_token = "your_access_token_here"
    # session_cookie = "your_session_cookie_here"
    
    if not access_token:
        print("❌ Could not extract access token from curl command")
        print("Please update the curl command with your actual tokens")
        return
    
    print("✅ Extracted credentials successfully")
    print(f"Access Token: {access_token[:20]}...")
    if session_cookie:
        print(f"Session Cookie: {session_cookie[:20]}...")
    
    # Create client with extracted credentials
    async with StakeAPI(access_token=access_token, session_cookie=session_cookie) as client:
        try:
            print("\n🔄 Fetching user balance...")
            balance = await client.get_user_balance()
            
            print("\n💰 Account Balance:")
            print("=" * 40)
            
            # Display available balances
            if balance["available"]:
                print("\n📊 Available Balances:")
                for currency, amount in balance["available"].items():
                    if amount > 0:  # Only show non-zero balances
                        print(f"  {currency.upper()}: {amount}")
            else:
                print("\n📊 Available Balances: None")
            
            # Display vault balances
            if balance["vault"]:
                print("\n🏦 Vault Balances:")
                for currency, amount in balance["vault"].items():
                    if amount > 0:  # Only show non-zero balances
                        print(f"  {currency.upper()}: {amount}")
            else:
                print("\n🏦 Vault Balances: None")
                
        except AuthenticationError:
            print("❌ Authentication failed. Your tokens may have expired.")
            print("Please get new tokens from stake.com and update the curl command.")
        except StakeAPIError as e:
            print(f"❌ API error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")


async def main():
    """
    Main function to run the balance example.
    """
    print("🎰 StakeAPI Balance Example")
    print("=" * 50)
    
    await get_balance_example()
    
    print("\n" + "=" * 50)
    print("📝 How to get your tokens:")
    print("1. Go to stake.com and log in")
    print("2. Open browser developer tools (F12)")
    print("3. Go to Network tab")
    print("4. Make any action that triggers a GraphQL request")
    print("5. Right-click on the request → Copy as cURL")
    print("6. Replace the curl command in this script")
    print("7. Run this script again")


if __name__ == "__main__":
    asyncio.run(main())
