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
      -b "" \
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
      -H "x-access-token: " \
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
