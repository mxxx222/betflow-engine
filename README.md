# BetFlow Engine

**Analytics-only sports data insights platform. No betting facilitation.**

## Quick Start

```bash
# Clone and setup
git clone <repo-url> betflow-engine
cd betflow-engine

# Start the entire stack
make up

# Access services
# API: http://localhost:8000
# Web Dashboard: http://localhost:3000
# n8n Workflows: http://localhost:5678
# Grafana: http://localhost:3001
```

## Legal Mode

This platform provides **educational analytics only**. All data insights are for informational purposes. No tips, no betting facilitation, no fund movement capabilities.

## Architecture

- `/engine`: Mojo-powered calculation core (EV, ELO, Poisson)
- `/api`: FastAPI backend with REST + webhooks
- `/worker`: n8n workflows for data ingestion
- `/db`: PostgreSQL with Alembic migrations
- `/web`: Next.js 14 analytics dashboard
- `/infra`: Docker infrastructure and monitoring

## Extending Providers

To add new data providers, implement the `OddsProvider` interface in `/api/providers/`:

```python
class NewProvider(OddsProvider):
    def fetch_events(self, sport: str, date_range: DateRange) -> List[Event]:
        # Implementation
        pass

    def fetch_odds(self, event_ids: List[str]) -> List[Odds]:
        # Implementation
        pass
```

## Development

```bash
# Run tests
make test

# Run linting
make lint

# Build all services
make build

# View logs
make logs
```

## License

Proprietary – Internal Use Only
