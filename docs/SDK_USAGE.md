# BetFlow Engine Python SDK v0.9.0

## Overview

The BetFlow Engine Python SDK provides high-performance sports analytics calculations with Mojo acceleration. This SDK is designed for educational analytics only and does not facilitate betting.

## Installation

### From Source
```bash
git clone https://github.com/betflow/betflow-engine.git
cd betflow-engine
pip install -e .
```

### From Wheel (Production)
```bash
pip install betflow-engine-0.9.0-py3-none-any.whl
```

## Quick Start

### Basic Usage

```python
from engine import BetFlowEngine

# Initialize the engine (with warmup enabled by default)
engine = BetFlowEngine()

# Check engine health
health = engine.health_check()
print(f"Engine status: {health['status']}")
print(f"Mojo available: {health['mojo_available']}")
print(f"Warmed up: {health['warmed_up']}")
```

### Expected Value Calculations

```python
# Calculate expected value for a bet
probability = 0.6  # 60% chance
odds = 2.0         # Decimal odds

ev = engine.calc_ev(probability, odds)
print(f"Expected Value: {ev:.4f}")

# Batch EV calculations
bets = [
    (0.5, 2.2),   # 50% chance, 2.2 odds
    (0.3, 3.5),   # 30% chance, 3.5 odds
    (0.7, 1.6),   # 70% chance, 1.6 odds
]

for prob, odds in bets:
    ev = engine.calc_ev(prob, odds)
    print(f"P={prob}, Odds={odds} → EV={ev:.4f}")
```

### Poisson Distribution Analysis

```python
# Calculate match outcome probabilities using Poisson distribution
home_rate = 1.5  # Expected goals for home team
away_rate = 1.2  # Expected goals for away team
max_goals = 6    # Maximum goals to consider

probabilities = engine.calc_poisson(home_rate, away_rate, max_goals)

# Display probability matrix
print("Poisson Probability Matrix:")
print("Away\\Home", end="")
for h in range(max_goals + 1):
    print(f"\t{h}", end="")
print()

for a in range(max_goals + 1):
    print(f"{a}", end="")
    for h in range(max_goals + 1):
        print(f"\t{probabilities[h][a]:.3f}", end="")
    print()

# Calculate specific outcomes
home_win_prob = sum(probabilities[h][a] 
                   for h in range(max_goals + 1) 
                   for a in range(max_goals + 1) 
                   if h > a)

draw_prob = sum(probabilities[h][h] for h in range(max_goals + 1))

away_win_prob = sum(probabilities[h][a] 
                   for h in range(max_goals + 1) 
                   for a in range(max_goals + 1) 
                   if a > h)

print(f"Home Win: {home_win_prob:.3f}")
print(f"Draw: {draw_prob:.3f}")
print(f"Away Win: {away_win_prob:.3f}")
```

### ELO Rating System

```python
from engine import MatchResult
from datetime import datetime

# Create match result
match = MatchResult(
    home_team="Arsenal",
    away_team="Chelsea",
    home_score=2,
    away_score=1,
    league="premier_league",
    date=datetime.utcnow()
)

# Update ELO ratings
elo_update = engine.update_elo(match)

print(f"Arsenal new rating: {elo_update.home_rating:.1f} (Δ{elo_update.home_change:+.1f})")
print(f"Chelsea new rating: {elo_update.away_rating:.1f} (Δ{elo_update.away_change:+.1f})")
```

### Match Outcome Predictions

```python
# Predict match outcome probabilities
home_win, draw, away_win = engine.predict_match(
    home_team="Manchester United",
    away_team="Liverpool",
    league="premier_league"
)

print(f"Manchester United win: {home_win:.1%}")
print(f"Draw: {draw:.1%}")
print(f"Liverpool win: {away_win:.1%}")

# Convert to odds
home_odds = 1.0 / home_win if home_win > 0 else float('inf')
draw_odds = 1.0 / draw if draw > 0 else float('inf')
away_odds = 1.0 / away_win if away_win > 0 else float('inf')

print(f"Implied odds - Home: {home_odds:.2f}, Draw: {draw_odds:.2f}, Away: {away_odds:.2f}")
```

### Signal Generation

```python
from engine import Signal

# Generate analytics signal
signal = engine.generate_signal(
    event_id="match_12345",
    market="match_winner",
    probability=0.65,
    best_odds=1.8
)

print(f"Signal ID: {signal.id}")
print(f"Fair odds: {signal.fair_odds:.2f}")
print(f"Best book odds: {signal.best_book_odds:.2f}")
print(f"Edge: {signal.edge:.4f}")
print(f"Risk note: {signal.risk_note}")
print(f"Explanation: {signal.explanation}")
```

## Advanced Usage

### Performance Optimization

```python
# Initialize with custom settings
engine = BetFlowEngine(
    enable_warmup=True,           # Enable warmup (default: True)
    cpu_affinity=[0, 1, 2, 3]     # Pin to specific CPU cores
)

# Check if engine is warmed up
if engine.is_warmed_up():
    print("Engine is ready for high-performance calculations")

# Batch processing for better performance
import time

# Time individual calculations
start = time.perf_counter()
for i in range(1000):
    ev = engine.calc_ev(0.6, 2.0)
duration = (time.perf_counter() - start) * 1000
print(f"1000 EV calculations: {duration:.1f}ms ({duration/1000:.3f}ms per calc)")
```

### Error Handling

```python
try:
    # Invalid probability (must be 0 < p < 1)
    ev = engine.calc_ev(1.5, 2.0)
except ValueError as e:
    print(f"Validation error: {e}")

try:
    # Invalid odds (must be > 1.0)
    ev = engine.calc_ev(0.5, 0.8)
except ValueError as e:
    print(f"Validation error: {e}")

try:
    # Check engine availability
    if not engine.health_check()['mojo_available']:
        print("Warning: Using Python fallback (Mojo not available)")
except Exception as e:
    print(f"Engine error: {e}")
```

### Concurrent Processing

```python
import asyncio
import concurrent.futures
from typing import List, Tuple

def calculate_ev_batch(prob_odds_pairs: List[Tuple[float, float]]) -> List[float]:
    """Calculate EV for multiple probability/odds pairs."""
    engine = BetFlowEngine()  # Each thread gets its own engine
    results = []
    
    for prob, odds in prob_odds_pairs:
        try:
            ev = engine.calc_ev(prob, odds)
            results.append(ev)
        except Exception as e:
            print(f"Error calculating EV for {prob}, {odds}: {e}")
            results.append(None)
    
    return results

# Process large batches concurrently
large_batch = [(0.5 + i*0.01, 2.0 + i*0.1) for i in range(1000)]

# Split into chunks for parallel processing
chunk_size = 100
chunks = [large_batch[i:i+chunk_size] for i in range(0, len(large_batch), chunk_size)]

# Process chunks in parallel
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    start = time.perf_counter()
    futures = [executor.submit(calculate_ev_batch, chunk) for chunk in chunks]
    results = []
    
    for future in concurrent.futures.as_completed(futures):
        results.extend(future.result())
    
    duration = (time.perf_counter() - start) * 1000
    print(f"Processed {len(large_batch)} calculations in {duration:.1f}ms")
```

## API Integration Examples

### Using with FastAPI

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from engine import BetFlowEngine

app = FastAPI()
engine = BetFlowEngine()

class EVRequest(BaseModel):
    probability: float
    odds: float

class EVResponse(BaseModel):
    expected_value: float
    probability: float
    odds: float

@app.post("/calculate-ev", response_model=EVResponse)
async def calculate_ev(request: EVRequest):
    try:
        ev = engine.calc_ev(request.probability, request.odds)
        return EVResponse(
            expected_value=ev,
            probability=request.probability,
            odds=request.odds
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Calculation failed")

@app.get("/health")
async def health_check():
    return engine.health_check()
```

### Data Analysis with Pandas

```python
import pandas as pd
import numpy as np

# Create sample betting data
data = {
    'match_id': range(1, 101),
    'home_team': [f'Team_{i}' for i in range(1, 101)],
    'away_team': [f'Team_{i+100}' for i in range(1, 101)],
    'home_prob': np.random.uniform(0.2, 0.8, 100),
    'draw_prob': np.random.uniform(0.15, 0.35, 100),
    'away_prob': np.random.uniform(0.2, 0.8, 100),
    'home_odds': np.random.uniform(1.5, 4.0, 100),
    'draw_odds': np.random.uniform(2.5, 5.0, 100),
    'away_odds': np.random.uniform(1.5, 4.0, 100),
}

df = pd.DataFrame(data)

# Normalize probabilities
prob_sum = df['home_prob'] + df['draw_prob'] + df['away_prob']
df['home_prob'] = df['home_prob'] / prob_sum
df['draw_prob'] = df['draw_prob'] / prob_sum
df['away_prob'] = df['away_prob'] / prob_sum

# Calculate expected values
engine = BetFlowEngine()

df['home_ev'] = df.apply(lambda row: engine.calc_ev(row['home_prob'], row['home_odds']), axis=1)
df['draw_ev'] = df.apply(lambda row: engine.calc_ev(row['draw_prob'], row['draw_odds']), axis=1)
df['away_ev'] = df.apply(lambda row: engine.calc_ev(row['away_prob'], row['away_odds']), axis=1)

# Find positive EV opportunities
positive_ev = df[(df['home_ev'] > 0) | (df['draw_ev'] > 0) | (df['away_ev'] > 0)]
print(f"Found {len(positive_ev)} matches with positive expected value")

# Display top opportunities
best_opportunities = df.loc[df[['home_ev', 'draw_ev', 'away_ev']].max(axis=1).nlargest(5).index]
print("\nTop 5 opportunities:")
for _, row in best_opportunities.iterrows():
    best_market = ['home_ev', 'draw_ev', 'away_ev'][np.argmax([row['home_ev'], row['draw_ev'], row['away_ev']])]
    print(f"Match {row['match_id']}: {best_market} = {row[best_market]:.4f}")
```

### Machine Learning Integration

```python
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import numpy as np

# Generate training data using BetFlow Engine
engine = BetFlowEngine()

# Create features (team stats, historical data, etc.)
n_samples = 1000
features = np.random.rand(n_samples, 10)  # 10 features per match

# Generate target probabilities using engine predictions
targets = []
for i in range(n_samples):
    # Simulate match prediction based on features
    home_strength = features[i, 0] * 2000 + 1000  # ELO-like rating
    away_strength = features[i, 1] * 2000 + 1000
    
    # Use engine to get baseline probabilities
    home_win, draw, away_win = engine.predict_match(
        f"Team_{i}_home", f"Team_{i}_away", "premier_league"
    )
    
    targets.append([home_win, draw, away_win])

targets = np.array(targets)

# Train model
X_train, X_test, y_train, y_test = train_test_split(features, targets, test_size=0.2)

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Make predictions and calculate EV
predictions = model.predict(X_test)

# Calculate expected values for predictions
sample_odds = np.array([[2.0, 3.5, 2.2]])  # Sample odds

for i in range(min(5, len(predictions))):
    pred = predictions[i]
    print(f"Prediction {i+1}:")
    print(f"  Home: {pred[0]:.3f} (EV: {engine.calc_ev(pred[0], sample_odds[0][0]):.4f})")
    print(f"  Draw: {pred[1]:.3f} (EV: {engine.calc_ev(pred[1], sample_odds[0][1]):.4f})")
    print(f"  Away: {pred[2]:.3f} (EV: {engine.calc_ev(pred[2], sample_odds[0][2]):.4f})")
```

## Configuration

### Environment Variables

```bash
# Enable/disable warmup
export BETFLOW_ENABLE_WARMUP=1

# Set CPU affinity (comma-separated core numbers)
export BETFLOW_CPU_AFFINITY="0,1,2,3"

# Mojo optimization level
export MOJO_OPTIMIZATION_LEVEL=3
```

### Docker Usage

```dockerfile
FROM python:3.11-slim

# Install BetFlow Engine
COPY betflow-engine-0.9.0-py3-none-any.whl /tmp/
RUN pip install /tmp/betflow-engine-0.9.0-py3-none-any.whl

# Set environment
ENV BETFLOW_ENABLE_WARMUP=1
ENV BETFLOW_CPU_AFFINITY="0,1"

# Your application code
COPY app.py /app/
WORKDIR /app

CMD ["python", "app.py"]
```

## Performance Guidelines

### Best Practices

1. **Engine Initialization**: Initialize once and reuse
2. **Warmup**: Enable warmup for production workloads
3. **CPU Affinity**: Pin to specific cores for consistent performance
4. **Batch Processing**: Process multiple calculations together
5. **Error Handling**: Always validate inputs and handle exceptions

### Performance Benchmarks

Typical performance on modern hardware (4-core CPU):

| Operation | Mojo (p95) | Python Fallback (p95) |
|-----------|------------|------------------------|
| EV Calculation | < 0.1ms | < 0.5ms |
| Poisson (6x6) | < 0.5ms | < 2.0ms |
| ELO Update | < 0.2ms | < 1.0ms |
| Match Prediction | < 0.3ms | < 1.5ms |

### Memory Usage

- Base engine: ~50MB
- With warmup: ~75MB
- Per calculation: ~1KB temporary

## Troubleshooting

### Common Issues

1. **Mojo Not Available**
   ```python
   health = engine.health_check()
   if not health['mojo_available']:
       print("Using Python fallback - performance may be reduced")
   ```

2. **Validation Errors**
   ```python
   # Ensure probabilities are in valid range
   probability = max(0.001, min(0.999, probability))
   
   # Ensure odds are valid
   odds = max(1.001, odds)
   ```

3. **Performance Issues**
   ```python
   # Check if engine is warmed up
   if not engine.is_warmed_up():
       print("Engine not warmed up - first calculations may be slower")
   
   # Monitor calculation times
   import time
   start = time.perf_counter()
   result = engine.calc_ev(0.6, 2.0)
   duration = (time.perf_counter() - start) * 1000
   if duration > 1.0:  # > 1ms
       print(f"Slow calculation detected: {duration:.2f}ms")
   ```

## Support

For issues and questions:
- GitHub Issues: https://github.com/betflow/betflow-engine/issues
- Documentation: https://docs.betflow-engine.com
- Email: support@betflow-engine.com

## License

Proprietary - Internal Use Only

---

**Disclaimer**: This SDK is for educational analytics only. It does not facilitate betting or gambling activities.
