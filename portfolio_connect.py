import os
import time
from dotenv import load_dotenv
from eth_account import Account
from hyperliquid.info import Info
from hyperliquid.utils import constants

# Prefer new google.genai SDK, fall back to legacy google.generativeai
try:
    import google.genai as genai  # type: ignore
except Exception:
    try:
        import google.generativeai as genai  # type: ignore
    except Exception:
        genai = None


def check_hyperliquid_account():
    """Main function to check Hyperliquid account status"""
    # 1. Load your keys
    load_dotenv()
    key = os.getenv("HYPERLIQUID_KEY")
    address = os.getenv("ACCOUNT_ADDRESS")
    
    # Gemini key (optional)
    gemini_key = os.getenv("GEMINI_KEY")
    
    if not key or not address:
        print("❌ Error: Keys not found in .env file!")
        return
    
    print(f"✅ Keys detected. Testing connection for address: {address}...")
    
    try:
        # 2. Connect to Hyperliquid Info API (Public Data)
        info = Info(constants.MAINNET_API_URL, skip_ws=True)
        user_state = info.user_state(address)
        
        # 3. Print Account Balance
        margin_summary = user_state.get("marginSummary", {})
        balance = margin_summary.get("accountValue", "0")
        print(f"\n💰 Account Value: ${balance}")
        
        # 4. Check for Open Positions
        positions = user_state.get("assetPositions", [])
        if not positions:
            print("Unknown positions or empty.")
        else:
            print(f"📊 Open Positions: {len(positions)}")
            for p in positions:
                pos = p.get("position", {})
                coin = pos.get("coin", "Unknown")
                size = pos.get("szi", "0")
                print(f"   - {coin}: {size}")
        
        print("\n✅ SUCCESS: Connection established! You are ready to trade.")
    
    except Exception as e:
        print(f"\n❌ CONNECTION FAILED: {e}")
        print("Double check your ACCOUNT_ADDRESS and ensure your API Wallet is funded.")


if __name__ == "__main__":
    print("🔄 Starting Hyperliquid monitoring script...")
    print("📅 Script will check your account every 5 minutes.")
    
    while True:
        try:
            # Print separator and timestamp
            print("\n" + "="*60)
            print(f"⏰ Check started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*60 + "\n")
            
            # Run the check
            check_hyperliquid_account()
            
            # Wait 5 minutes before next check
            print("\n⏳ Waiting 5 minutes until next check...")
            print(f"💤 Next check at: {time.strftime('%H:%M:%S', time.localtime(time.time() + 300))}")
            time.sleep(300)  # 300 seconds = 5 minutes
            
        except KeyboardInterrupt:
            print("\n\n🛑 Script stopped by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n⚠️ Unexpected error: {e}")
            print("⏳ Retrying in 5 minutes...")
            time.sleep(300)