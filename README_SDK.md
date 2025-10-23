# BetFlow Engine Python SDK

**Version 0.9.0** - Production-ready sports analytics with Mojo acceleration

## Quick Start

```python
from betflow import BetFlowEngine

# Initialize engine (automatically uses Mojo if available)
engine = BetFlowEngine()

# Calculate expected value
ev = engine.calc_ev(probability=0.6, odds=2.0)
print(f"Expected value: {ev:.3f}")  # 0.200

# Calculate Poisson match probabilities
probs = engine.calc_poisson(home_rate=1.5, away_rate=1.2, max_goals=6)
home_win_prob = sum(sum(row[i] for row in probs) for i in range(7) if i > 3)  # Home scores more than 3

# Update ELO ratings
from betflow import MatchResult
from datetime import datetime

match = MatchResult(
    home_team="Arsenal",
    away_team="Chelsea",
    home_score=2,
    away_score=1,
    league="premier_league",
    date=datetime.utcnow()
)

update = engine.update_elo(match)
print(f"Home rating change: {update.home_change:.1f}")

# Predict match outcome
home_win, draw, away_win = engine.predict_match("Arsenal", "Chelsea", "premier_league")
print(f"Predicted: Home {home_win:.1%}, Draw {draw:.1%}, Away {away_win:.1%}")
```

## Batch Processing

```python
# Batch EV calculations
probabilities = [0.6, 0.55, 0.7, 0.45]
odds = [2.0, 2.2, 1.8, 2.5]

evs = [engine.calc_ev(p, o) for p, o in zip(probabilities, odds)]
print(f"Batch EVs: {evs}")

# Bulk match predictions
matches = [
    ("Arsenal", "Chelsea", "premier_league"),
    ("Man City", "Liverpool", "premier_league"),
    ("Real Madrid", "Barcelona", "la_liga")
]

predictions = [engine.predict_match(*match) for match in matches]
for i, (home, draw, away) in enumerate(predictions):
    print(f"Match {i+1}: Home {home:.1%}, Draw {draw:.1%}, Away {away:.1%}")
```

## Health Check & Monitoring

```python
# Check engine health
health = engine.health_check()
print(f"Status: {health['status']}")
print(f"Mojo enabled: {health['use_mojo']}")
print(f"Performance test: {health['performance_test']['ev_calculation_ms']:.3f}ms")
```

## Performance Benchmarks

Current SLO targets (all met in v0.9.0):

- **EV Calculation**: P95 < 1ms, P99 < 5ms
- **Poisson Calculation**: P95 < 1ms, P99 < 5ms
- **Error Rate**: < 0.1%

Run benchmarks:
```bash
cd engine && python benchmarks.py
```

## Installation

```bash
# From PyPI (coming soon)
pip install betflow-engine

# From source
git clone <repo>
cd betflow-engine
pip install -e .
```

## Architecture

- **Mojo Core**: High-performance calculations (ELO, EV, Poisson)
- **Python Interface**: Easy-to-use API with automatic fallbacks
- **Hybrid Mode**: Uses Mojo when available, falls back to Python
- **Production Ready**: SLO monitoring, health checks, input validation

## API Reference

### BetFlowEngine

#### Methods

- `calc_ev(probability: float, odds: float) -> float`
  - Calculate expected value
  - SLO: P95 < 1ms

- `calc_poisson(home_rate: float, away_rate: float, max_goals: int = 6) -> List[List[float]]`
  - Calculate match outcome probabilities using Poisson distribution
  - SLO: P95 < 1ms

- `update_elo(match: MatchResult) -> EloUpdate`
  - Update ELO ratings based on match result
  - SLO: P95 < 1ms

- `predict_match(home_team: str, away_team: str, league: str) -> Tuple[float, float, float]`
  - Predict match outcome probabilities
  - SLO: P95 < 1ms

- `generate_signal(event_id: str, market: str, probability: float, best_odds: float) -> Signal`
  - Generate trading signal
  - SLO: P95 < 1ms

- `health_check() -> Dict[str, Any]`
  - System health and performance metrics

### Data Classes

- `MatchResult`: Match data for ELO updates
- `EloUpdate`: ELO rating change results
- `Signal`: Analytics signal output

## Configuration

Environment variables:
- `USE_MOJO`: Force enable/disable Mojo (default: auto-detect)
- `MOJO_DEBUG`: Enable debug logging (default: false)

## Troubleshooting

**Mojo not available:**
- Engine automatically falls back to Python implementations
- Check `health_check()` for Mojo availability status

**Performance issues:**
- Run `benchmarks.py` to check SLO compliance
- Ensure sufficient CPU cores for Mojo acceleration

**Memory issues:**
- Monitor with health checks
- Mojo uses CPU affinity for optimal performance

## License

Proprietary - Internal Use Only