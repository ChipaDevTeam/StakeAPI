---
layout: default
title: User Account
parent: Guides
nav_order: 3
---

# User Account API
{: .fs-9 }

Manage your profile, check balances, view statistics, and track transactions.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Overview

The User Account API lets you access your Stake.com profile, check balances across all cryptocurrencies, view your betting statistics, and track your transaction history.

## Get User Profile

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(access_token="your_token") as client:
        user = await client.get_user_profile()
        
        print(f"👤 Username: {user.username}")
        print(f"📧 Email: {user.email or 'Not set'}")
        print(f"✅ Verified: {user.verified}")
        print(f"💵 Currency: {user.currency}")
        print(f"🌍 Country: {user.country or 'Not set'}")
        print(f"📅 Member since: {user.created_at}")

asyncio.run(main())
```

## Check Account Balance

This is probably the most commonly used API call. Get your balance across all cryptocurrencies:

```python
async def check_balance():
    async with StakeAPI(access_token="your_token") as client:
        balance = await client.get_user_balance()
        
        print("💰 ACCOUNT BALANCE")
        print("=" * 40)
        
        # Available balance (ready to use)
        print("\n📊 Available:")
        total_available = 0
        for currency, amount in balance["available"].items():
            if amount > 0:
                print(f"  {currency.upper():8s} {amount:.8f}")
                total_available += 1
        
        if total_available == 0:
            print("  No available balance")
        
        # Vault balance (locked/saved)
        print("\n🏦 Vault:")
        total_vault = 0
        for currency, amount in balance["vault"].items():
            if amount > 0:
                print(f"  {currency.upper():8s} {amount:.8f}")
                total_vault += 1
        
        if total_vault == 0:
            print("  No vault balance")

asyncio.run(check_balance())
```

## Balance Monitoring

Build a script that monitors your balance over time:

```python
import asyncio
from datetime import datetime
from stakeapi import StakeAPI

async def monitor_balance(interval_seconds: int = 60):
    """Monitor balance changes in real-time."""
    previous_balances = {}
    
    async with StakeAPI(access_token="your_token") as client:
        while True:
            balance = await client.get_user_balance()
            current = balance["available"]
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            for currency, amount in current.items():
                if amount <= 0:
                    continue
                    
                prev = previous_balances.get(currency, amount)
                change = amount - prev
                
                if change != 0:
                    direction = "📈" if change > 0 else "📉"
                    print(f"[{timestamp}] {direction} {currency.upper()}: "
                          f"{prev:.8f} → {amount:.8f} "
                          f"({change:+.8f})")
                else:
                    print(f"[{timestamp}] ➖ {currency.upper()}: {amount:.8f} (no change)")
            
            previous_balances = current
            await asyncio.sleep(interval_seconds)

# Monitor every 30 seconds
asyncio.run(monitor_balance(30))
```

## User Profile via GraphQL

For more detailed profile information:

```python
from stakeapi.endpoints import GraphQLQueries

async with StakeAPI(access_token="your_token") as client:
    data = await client._graphql_request(
        query=GraphQLQueries.USER_PROFILE,
        operation_name="UserProfile"
    )
    
    user = data.get("user", {})
    print(f"ID: {user.get('id')}")
    print(f"Name: {user.get('name')}")
    print(f"Email Verified: {user.get('isEmailVerified')}")
    print(f"Country: {user.get('country')}")
    print(f"VIP Level: {user.get('level')}")
```

## The User Model

```python
class User(BaseModel):
    id: str                          # Unique user ID
    username: str                    # Display name
    email: Optional[str]             # Email address
    verified: bool                   # Email verification status
    created_at: datetime             # Account creation date
    country: Optional[str]           # User's country
    currency: str                    # Preferred currency
```

## Balance Response Format

The `get_user_balance()` method returns a dictionary:

```python
{
    "available": {
        "btc": 0.00150000,
        "eth": 0.05000000,
        "ltc": 1.50000000,
        "doge": 500.00000000,
        "usd": 100.00,
        "eur": 0.00,
        # ... more currencies
    },
    "vault": {
        "btc": 0.01000000,
        "eth": 0.00000000,
        # ... more currencies
    }
}
```

| Key | Description |
|:----|:------------|
| `available` | Funds ready to use for betting |
| `vault` | Funds locked in the vault (savings) |

## Combining Profile and Balance Data

```python
async def full_account_summary():
    async with StakeAPI(access_token="your_token") as client:
        # Fetch both in parallel
        import asyncio
        user, balance = await asyncio.gather(
            client.get_user_profile(),
            client.get_user_balance()
        )
        
        print(f"╔{'═' * 48}╗")
        print(f"║  ACCOUNT SUMMARY                                ║")
        print(f"╠{'═' * 48}╣")
        print(f"║  User: {user.username:40s} ║")
        print(f"║  Verified: {'✅ Yes' if user.verified else '❌ No':38s} ║")
        print(f"║  Currency: {user.currency:38s} ║")
        print(f"╠{'═' * 48}╣")
        
        available = {k: v for k, v in balance["available"].items() if v > 0}
        vault = {k: v for k, v in balance["vault"].items() if v > 0}
        
        print(f"║  Available Balances: {len(available):27d} ║")
        for cur, amt in available.items():
            print(f"║    {cur.upper():6s} {amt:>38.8f} ║")
        
        print(f"║  Vault Balances: {len(vault):31d} ║")
        for cur, amt in vault.items():
            print(f"║    {cur.upper():6s} {amt:>38.8f} ║")
        
        print(f"╚{'═' * 48}╝")

asyncio.run(full_account_summary())
```

{% include affiliate-banner.html %}

---

{: .note }
> Track your Stake.com balance and statistics programmatically. [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) and start building with real account data!
