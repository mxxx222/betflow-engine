# 🚀 Crypto Tracker - Whale Tracking & DEX Scraping System

**Advanced crypto trading intelligence platform based on veteran OG trader strategy**

## 🎯 Overview

Crypto Tracker is a comprehensive system for tracking smart money movements, discovering new tokens, and analyzing social sentiment in the crypto market. Based on real-world trading strategies from 2013+ veterans who consistently profit in crypto markets.

### Core Philosophy

- **S-TIER Strategy**: Whale tracking + DEX automation + Free social intel
- **Multi-Signal Confirmation**: Requires 3+ independent sources before alerting
- **Risk Management First**: Built-in position sizing and risk assessment
- **Semi-Automated**: Alerts for manual verification, not blind auto-trading
- **Public Data > Private Scams**: Free/cheap data sources beat expensive "alpha groups"

## 🔥 Key Features

### 1. Whale Wallet Tracking 🐋

Monitor smart money movements across chains:
- Real-time transaction monitoring
- Customizable minimum transaction values
- Multi-chain support (ETH, SOL, Base, etc.)
- Whale portfolio analysis

**Why it works**: Whales don't lie. Their on-chain transactions show real conviction.

### 2. DEX Scraping 📊

Discover new tokens early:
- 0-15 minute launch window detection
- Volume spike alerts (300%+ increases)
- Liquidity analysis
- Contract safety checks (honeypot, hidden mint)

**Why it works**: Early entry on legitimate projects = highest potential returns.

### 3. Social Sentiment Tracking 📱

Monitor community buzz:
- Twitter/X smart money tracking
- 4chan /biz/ scraping (filter noise)
- Telegram channel monitoring
- Mention velocity analysis

**Why it works**: Social momentum often precedes price action, if filtered correctly.

### 4. Multi-Signal Confirmation ✅

Combine signals for high-confidence alerts:
- Requires 3+ independent sources
- Weighted confidence scoring
- Risk-adjusted edge calculation
- Action recommendations (watch, small_buy, exit, avoid)

**Why it works**: Single signals = noise. Multiple confirming signals = edge.

### 5. Alert System 🚨

Instant notifications:
- Discord webhooks with rich embeds
- Telegram bot integration
- Customizable thresholds
- Position sizing recommendations

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- API keys (optional but recommended):
  - Etherscan API key
  - Moralis API key (for multi-chain tracking)
  - Twitter API key (for sentiment)
  - Alchemy/Infura (for real-time blockchain data)

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys and webhook URLs
nano .env
```

### Environment Variables

```bash
# Blockchain API Keys
ETHERSCAN_API_KEY=your_etherscan_key
MORALIS_API_KEY=your_moralis_key
ALCHEMY_API_KEY=your_alchemy_key

# Social API Keys
TWITTER_API_KEY=your_twitter_key

# Alert Configuration
DISCORD_WEBHOOK_URL=your_discord_webhook
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

## 🚀 Quick Start

### Basic Usage

```python
from crypto_tracker import CryptoTracker

# Initialize tracker (loads config from .env)
tracker = CryptoTracker()

# Start monitoring (runs continuously)
await tracker.start()
```

### Command Line

```bash
# Run the tracker
python -m crypto_tracker.tracker

# Or with custom config
DISCORD_WEBHOOK_URL=https://... python -m crypto_tracker.tracker
```

## 📊 Configuration

### Tracked Chains

Edit `crypto_tracker/config.py` to configure chains:

```python
tracked_chains: List[str] = ["eth", "sol", "base"]
```

### Whale Wallets

Add tracked whale wallets in `crypto_tracker/config.py`:

```python
DEFAULT_TRACKED_WHALES = [
    TrackedWhaleConfig(
        address="0x...",  # Whale wallet address
        chain="eth",
        label="Known Whale Name",
        min_tx_value=10000.0  # USD
    ),
    # Add more whales...
]
```

**How to find whales:**
- Arkham Intelligence (free tier)
- Nansen (paid, $150/mo)
- Etherscan/Solscan top holders
- 4chan /biz/ known wallet addresses

### Alert Thresholds

```python
# Minimum sources for multi-signal confirmation
alert_min_sources: int = 3

# Time window for signal correlation (1 hour default)
alert_confirmation_window: int = 3600

# Minimum whale transaction value
whale_min_tx_value: float = 10000.0

# Minimum liquidity to track
dex_min_liquidity: float = 10000.0
```

## 📈 Usage Examples

### Example 1: Basic Monitoring

```python
import asyncio
from crypto_tracker import CryptoTracker

async def main():
    tracker = CryptoTracker()
    
    # Get current status
    status = tracker.get_status()
    print(f"Tracking {status['whale_tracker']['tracked_wallets']} whales")
    print(f"Monitoring {status['dex_scraper']['monitored_chains']} chains")
    
    # Start monitoring
    await tracker.start()

asyncio.run(main())
```

### Example 2: Custom Whale Tracking

```python
from crypto_tracker import CryptoTracker
from crypto_tracker.models.whale_activity import WhaleWallet

tracker = CryptoTracker()

# Add custom whale
whale = WhaleWallet(
    address="0x1234...",
    chain="eth",
    label="Tetherio (SOL Whale)",
    min_tx_value=50000.0
)
tracker.whale_tracker.add_wallet(whale)
```

### Example 3: Manual Signal Processing

```python
from crypto_tracker.services.alert_manager import AlertManager
from crypto_tracker.models.signal import Signal, SignalType

manager = AlertManager(min_sources=3)

# Add signals from different sources
signal1 = Signal(...)  # Whale buy
signal2 = Signal(...)  # Volume spike  
signal3 = Signal(...)  # Social buzz

# Check for confirmation
confirmed = manager.add_signal(signal1)
confirmed = manager.add_signal(signal2)
confirmed = manager.add_signal(signal3)  # Should trigger alert

if confirmed:
    await manager.send_alert(confirmed)
```

## 🔒 Risk Management

### Built-In Safeguards

1. **Position Sizing**: Default 1-2% of portfolio
2. **Stop Loss**: -30% automatic recommendation
3. **Daily Loss Limit**: -5% portfolio cap
4. **Risk Levels**: Automatic calculation based on:
   - Token age (0-1h = extreme risk)
   - Holder concentration (top 10 > 60% = high risk)
   - Contract safety (honeypot, hidden mint)
   - Liquidity status (locked vs unlocked)

### Recommended Workflow

```
1. Receive multi-signal alert (3+ sources)
2. Manual verification:
   - Check DEXScreener link
   - Verify contract on explorer
   - Check holder distribution
   - Read community sentiment
3. Decision:
   - Position size: 1-2% portfolio MAX
   - Stop loss: -30%
   - Take profit: 50% @ 2x, 30% @ 5x
4. Execute manually (no auto-trading)
5. Monitor and adjust
```

## 📊 Signal Tier List

Based on real trading results:

### S-TIER (Highest Edge)
- Multi-whale buy (3+ whales, same token, 24h window)
- New token + whale buy + social buzz (all within 1h)
- Volume spike + whale accumulation + liquidity locked

### A-TIER (Good Edge)
- Whale buy + volume spike (2 sources)
- New token + social buzz + verified contract
- Single whale buy (>$100k, new token)

### B-TIER (Watch)
- Social buzz alone (10+ mentions/hour)
- Volume spike alone (3x+ increase)
- New token with good metrics

### C-TIER (Noise)
- Single source signals
- Unverified contracts
- No liquidity lock
- Top 10 holders >60%

## 🎓 Learning Resources

Based on the original Finnish problem statement, these are the key concepts:

### Key Strategies

1. **Whale Tracking** (S-TIER)
   - Track 10-20 consistently profitable wallets
   - 30% of them buy same token in 24h = STRONG signal
   - When they SELL = get out immediately

2. **DEX Activity Monitoring** (S-TIER)
   - New pairs on DEXScreener (0-15min old)
   - Volume/Liquidity ratio >2.0 = hype
   - Holder concentration <40% top 10 = healthier

3. **Free Social Intel** (A-TIER)
   - Twitter smart money (cobie, DegenSpartan, etc.)
   - 4chan /biz/ (95% schizo, 5% alpha - filter it)
   - Telegram (official channels only, no "VIP alpha")

4. **Multi-Signal Confirmation** (CRITICAL)
   - Never buy on 1 signal
   - Need 3+ independent confirmations:
     * Whale activity
     * Volume spike
     * Social mention
     * Technical (contract safe)

### Trading Rules (Veteran Wisdom)

```
✅ DO:
- Start small (1-2% positions)
- Take profit consistently (50% @ 2x)
- Use stop losses (-30%)
- Manual verification always
- Track results and iterate

❌ DON'T:
- Auto-execute (botti ei näe rug pulleja)
- FOMO into pumps
- Revenge trade after loss
- Hold shitcoins (trade them)
- Trust "insider alpha groups"
```

## 📁 Project Structure

```
crypto_tracker/
├── __init__.py              # Main exports
├── config.py                # Configuration
├── tracker.py               # Main orchestrator
├── models/                  # Data models
│   ├── signal.py           # Signal & filter models
│   ├── whale_activity.py   # Whale tracking models
│   └── token_data.py       # Token data models
├── services/               # Core services
│   ├── whale_tracker.py    # Whale monitoring
│   ├── dex_scraper.py      # DEX scraping
│   ├── sentiment_tracker.py # Social sentiment
│   └── alert_manager.py    # Multi-signal + alerts
└── scrapers/               # Specific scrapers
    └── (custom scrapers)
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/test_crypto_tracker.py -v

# Run specific test class
pytest tests/test_crypto_tracker.py::TestWhaleTracker -v

# Run with coverage
pytest tests/test_crypto_tracker.py --cov=crypto_tracker
```

## 🔧 Development

### Adding a New Chain

1. Update `config.py`:
```python
tracked_chains: List[str] = ["eth", "sol", "base", "arbitrum"]
```

2. Add chain support in `whale_tracker.py`:
```python
async def _fetch_arbitrum_transactions(self, wallet, since):
    # Implementation
    pass
```

### Adding a New Signal Source

1. Create new service in `services/`:
```python
class CustomTracker:
    async def start_monitoring(self, callback):
        # Generate signals
        signal = Signal(...)
        await callback(signal)
```

2. Add to main orchestrator:
```python
self.custom_tracker = CustomTracker()
await self.custom_tracker.start_monitoring(self.handle_signal)
```

## 💎 Pro Tips

### Setup Optimization

**Cheap Setup ($0-50/mo):**
- Free DEXScreener API
- Free Etherscan webhooks (3 wallets)
- Manual Twitter checking
- Discord webhooks (free)
- **Potential**: 20-50% monthly

**Mid Setup ($50-300/mo):**
- Moralis Streams ($50/mo) - 20 wallets
- Nansen Lite ($150/mo) - smart money dashboard
- Private RPC node ($50/mo) - speed
- **Potential**: 50-100% monthly

**Pro Setup ($500-2000/mo):**
- Nansen Pro ($500/mo)
- Arkham Intel ($100/mo)
- Dedicated infra ($300/mo)
- MEV infrastructure ($500-1000/mo)
- **Potential**: 100-300% monthly

### Best Practices

1. **Start with paper trading** (no real money)
2. **Track every signal** (what worked, what didn't)
3. **Iterate based on results** (adjust thresholds)
4. **Scale slowly** (proven strategy first)
5. **Never full-auto** (manual verification always)

## 📞 Support

For issues, questions, or contributions:
- GitHub Issues: [betflow-engine/issues](https://github.com/mxxx222/betflow-engine/issues)
- Documentation: This README + code comments

## ⚖️ Legal Disclaimer

This tool is for **educational and research purposes only**. 

- Not financial advice
- High risk of loss in crypto trading
- Do your own research (DYOR)
- Never invest more than you can afford to lose
- Past performance ≠ future results

## 📝 License

Proprietary - Internal Use Only

---

**🔐 Crypto Tracker - Where Smart Money Goes**

_Built on veteran trader wisdom from 2013+ OGs who actually profit consistently._

**Bottom Line**: Rakenna systemisi. Testaa. Iterate. Scale. This is work, but if you love the game? Best job in the world. 🚀💰
