"""
Demo script showing crypto tracker usage.

This demonstrates the key features without requiring actual API keys.
"""

import asyncio
from crypto_tracker import CryptoTracker
from crypto_tracker.models.whale_activity import WhaleWallet
from crypto_tracker.models.token_data import TokenData
from crypto_tracker.models.signal import Signal, SignalType


def demo_models():
    """Demonstrate data models."""
    print("\n" + "="*60)
    print("📊 DEMO: Data Models")
    print("="*60)
    
    # Token data example
    token = TokenData(
        address="0x1234567890abcdef",
        symbol="DEMO",
        name="Demo Token",
        chain="eth",
        price=0.001,
        volume_24h=500000.0,
        liquidity=100000.0,
        dex="uniswap",
        age_hours=2.0,
        contract_verified=True,
        liquidity_locked=True,
        price_change_1h=25.0,
    )
    
    print(f"\n💎 Token: ${token.symbol}")
    print(f"   Price: ${token.price:.6f}")
    print(f"   24h Volume: ${token.volume_24h:,.0f}")
    print(f"   Liquidity: ${token.liquidity:,.0f}")
    print(f"   Age: {token.age_hours:.1f} hours")
    
    # Calculate metrics
    risk = token.calculate_risk_level()
    edge = token.calculate_edge_score()
    
    print(f"\n📈 Calculated Metrics:")
    print(f"   Risk Level: {risk.upper()}")
    print(f"   Edge Score: {edge:.1f}/10")
    
    # Whale wallet example
    whale = WhaleWallet(
        address="0xwhale123456789",
        chain="eth",
        label="Known Whale",
        min_tx_value=50000.0,
        track_buys=True,
        track_sells=True,
    )
    
    print(f"\n🐋 Tracked Whale:")
    print(f"   Label: {whale.label}")
    print(f"   Chain: {whale.chain.upper()}")
    print(f"   Min TX: ${whale.min_tx_value:,.0f}")
    
    # Signal example
    signal = Signal(
        id="demo_signal_1",
        signal_type=SignalType.MULTI_WHALE,
        token_address="0x1234567890abcdef",
        token_symbol="DEMO",
        chain="eth",
        confidence=0.85,
        edge_score=8.5,
        sources=["whale_tracker", "dex_scraper", "sentiment_tracker"],
        source_count=3,
        market_cap=5000000.0,
        volume_24h=500000.0,
        risk_level="medium",
        rug_check_passed=True,
        contract_verified=True,
        recommended_action="small_buy",
        position_size_pct=1.5,
        alert_message="🚨 Multi-signal confirmation for $DEMO",
    )
    
    print(f"\n🚨 Multi-Signal Confirmation:")
    print(f"   Token: ${signal.token_symbol}")
    print(f"   Sources: {len(signal.sources)} ({', '.join(signal.sources)})")
    print(f"   Confidence: {signal.confidence:.1%}")
    print(f"   Edge Score: {signal.edge_score:.1f}/10")
    print(f"   Risk: {signal.risk_level.upper()}")
    print(f"   Action: {signal.recommended_action.upper()}")
    print(f"   Position Size: {signal.position_size_pct}%")


def demo_configuration():
    """Demonstrate configuration."""
    print("\n" + "="*60)
    print("⚙️  DEMO: Configuration")
    print("="*60)
    
    print("\n📝 Required Environment Variables:")
    print("   DISCORD_WEBHOOK_URL      - Discord webhook for alerts")
    print("   TELEGRAM_BOT_TOKEN       - Telegram bot token")
    print("   ETHERSCAN_API_KEY        - Etherscan API key")
    print("   MORALIS_API_KEY          - Moralis API key")
    print("   TWITTER_API_KEY          - Twitter API key")
    
    print("\n🎯 Key Configuration:")
    print("   - Tracked Chains: ETH, SOL, Base")
    print("   - Min Sources: 3 (whale + dex + sentiment)")
    print("   - Whale Min TX: $10,000")
    print("   - DEX Min Liquidity: $10,000")
    print("   - Sentiment Min Mentions: 10/hour")
    
    print("\n💰 Risk Management:")
    print("   - Max Position Size: 2% of portfolio")
    print("   - Stop Loss: -30%")
    print("   - Daily Loss Limit: -5% of portfolio")


def demo_workflow():
    """Demonstrate typical workflow."""
    print("\n" + "="*60)
    print("🔄 DEMO: Typical Workflow")
    print("="*60)
    
    print("\n1️⃣  Signal Detection:")
    print("   ├─ WhaleTracker: Whale buys $50k of token")
    print("   ├─ DEXScraper: Volume spike +400% on same token")
    print("   └─ SentimentTracker: 15 mentions in last hour")
    
    print("\n2️⃣  Multi-Signal Confirmation:")
    print("   ├─ 3 independent sources ✅")
    print("   ├─ Confidence: 85% ✅")
    print("   ├─ Edge Score: 8.5/10 ✅")
    print("   └─ Risk: MEDIUM ✅")
    
    print("\n3️⃣  Alert Generation:")
    print("   ├─ Discord: Rich embed sent")
    print("   ├─ Telegram: Message sent")
    print("   └─ Action: SMALL_BUY (1-2% position)")
    
    print("\n4️⃣  Manual Verification:")
    print("   ├─ Check DEXScreener link")
    print("   ├─ Verify contract on explorer")
    print("   ├─ Check holder distribution")
    print("   └─ Read community sentiment")
    
    print("\n5️⃣  Execution (Manual):")
    print("   ├─ Position size: 1.5% of portfolio")
    print("   ├─ Stop loss: -30%")
    print("   ├─ Take profit: 50% @ 2x, 30% @ 5x")
    print("   └─ Moon bag: 20%")


def demo_statistics():
    """Show example statistics."""
    print("\n" + "="*60)
    print("📊 DEMO: Example Statistics")
    print("="*60)
    
    print("\n🐋 Whale Tracker:")
    print("   - Tracked Wallets: 20")
    print("   - Recent Activities: 45 (24h)")
    print("   - Signals Generated: 8")
    
    print("\n🔍 DEX Scraper:")
    print("   - Monitored Chains: 3 (ETH, SOL, Base)")
    print("   - Tokens Discovered: 127 (24h)")
    print("   - High-edge Tokens: 12")
    
    print("\n📱 Sentiment Tracker:")
    print("   - Tracked Accounts: 15 (Twitter)")
    print("   - Total Mentions: 450 (24h)")
    print("   - High-velocity Tokens: 8")
    
    print("\n🚨 Alert Manager:")
    print("   - Multi-Signal Confirmations: 5 (24h)")
    print("   - Alerts Sent: 5")
    print("   - Avg Sources per Alert: 3.4")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("🚀 CRYPTO TRACKER DEMO")
    print("="*60)
    print("\nBased on veteran OG trader strategy:")
    print("- S-TIER: Whale tracking + DEX scraping + Free social intel")
    print("- Multi-signal confirmation (3+ sources)")
    print("- Semi-automated alerts (manual verification)")
    print("- Risk management built-in")
    
    demo_models()
    demo_configuration()
    demo_workflow()
    demo_statistics()
    
    print("\n" + "="*60)
    print("💡 NEXT STEPS")
    print("="*60)
    print("\n1. Copy .env.example to .env")
    print("2. Add your API keys and webhook URLs")
    print("3. Configure tracked whale wallets in config.py")
    print("4. Run: python -m crypto_tracker.tracker")
    print("\n📚 See README.md for complete documentation")
    print("\n" + "="*60)
    print("✅ Demo Complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
