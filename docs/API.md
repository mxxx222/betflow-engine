# API Documentation

## Overview

The BetFlow Engine API provides analytics-only sports data insights. All endpoints return educational analytics data only.

## Base URL

```
http://localhost:8000
```

## Authentication

All API endpoints require authentication using API keys:

```bash
Authorization: Bearer YOUR_API_KEY
```

## Rate Limiting

- **Rate Limit**: 100 requests per minute per API key
- **Headers**: Rate limit information in response headers
- **Exceeded**: 429 status code when rate limit exceeded

## Endpoints

### Health Check

#### GET /health

Check system health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "engine": "healthy",
    "providers": "healthy"
  }
}
```

### Events

#### GET /v1/events

Get sports events with optional filtering.

**Query Parameters:**
- `sport` (optional): Filter by sport
- `date_from` (optional): Start date (YYYY-MM-DD)
- `date_to` (optional): End date (YYYY-MM-DD)
- `league` (optional): Filter by league

**Response:**
```json
[
  {
    "id": "evt_123",
    "sport": "football",
    "league": "premier_league",
    "home_team": "Arsenal",
    "away_team": "Chelsea",
    "start_time": "2024-01-15T15:00:00Z",
    "status": "scheduled",
    "home_score": null,
    "away_score": null,
    "venue": "Emirates Stadium",
    "weather": null
  }
]
```

#### GET /v1/odds

Get odds for a specific event.

**Query Parameters:**
- `event_id` (required): Event identifier
- `market` (optional): Filter by market type

**Response:**
```json
[
  {
    "id": "odds_123",
    "event_id": "evt_123",
    "book": "bet365",
    "market": "1X2",
    "selection": "home",
    "price": 2.10,
    "line": null,
    "implied_probability": 0.476,
    "vig": 0.05,
    "fetched_at": "2024-01-01T12:00:00Z"
  }
]
```

### Signals

#### POST /v1/signals/query

Query analytics signals with filtering.

**Request Body:**
```json
{
  "min_edge": 0.05,
  "max_edge": 0.20,
  "markets": ["1X2", "moneyline"],
  "sports": ["football", "basketball"],
  "leagues": ["premier_league", "nba"],
  "min_confidence": 0.70,
  "status": "active",
  "limit": 100,
  "offset": 0
}
```

**Response:**
```json
[
  {
    "id": "sig_123",
    "event_id": "evt_123",
    "market": "1X2",
    "signal_type": "edge",
    "implied_probability": 0.476,
    "fair_odds": 2.20,
    "best_book_odds": 2.10,
    "edge": 0.047,
    "confidence": 0.75,
    "risk_note": "Educational analytics only",
    "explanation": "Fair probability: 0.455, Edge: 0.047",
    "model_version": "1.0.0",
    "status": "active",
    "expires_at": "2024-01-02T12:00:00Z",
    "created_at": "2024-01-01T12:00:00Z"
  }
]
```

#### GET /v1/signals/{signal_id}

Get specific signal by ID.

**Response:**
```json
{
  "id": "sig_123",
  "event_id": "evt_123",
  "market": "1X2",
  "signal_type": "edge",
  "implied_probability": 0.476,
  "fair_odds": 2.20,
  "best_book_odds": 2.10,
  "edge": 0.047,
  "confidence": 0.75,
  "risk_note": "Educational analytics only",
  "explanation": "Fair probability: 0.455, Edge: 0.047",
  "model_version": "1.0.0",
  "status": "active",
  "expires_at": "2024-01-02T12:00:00Z",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### Webhooks

#### POST /v1/webhooks/ingest

Ingest data from external providers.

**Request Body:**
```json
{
  "provider": "odds_api",
  "data_type": "odds",
  "payload": {
    "event_id": "evt_123",
    "book": "bet365",
    "market": "1X2",
    "selection": "home",
    "price": 2.10
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Response:**
```json
{
  "status": "accepted",
  "message": "Data ingestion started"
}
```

### Models

#### GET /v1/models/status

Get model status and information.

**Response:**
```json
{
  "models": [
    {
      "id": "model_123",
      "name": "ELO Rating System",
      "version": "1.0.0",
      "type": "elo",
      "status": "active",
      "accuracy": 0.68,
      "last_trained": "2024-01-01T10:00:00Z",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ],
  "last_updated": "2024-01-01T12:00:00Z",
  "total_signals": 1250,
  "active_signals": 45
}
```

### Metrics

#### GET /metrics

Prometheus metrics endpoint.

**Response:**
```
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{method="GET",endpoint="/health",status="200"} 1

# HELP signals_generated_total Total signals generated
# TYPE signals_generated_total counter
signals_generated_total{market="1X2",sport="football"} 5
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid request parameters",
  "status_code": 400,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 401 Unauthorized
```json
{
  "error": "API key required",
  "status_code": 401,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 403 Forbidden
```json
{
  "error": "Access forbidden",
  "status_code": 403,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found",
  "status_code": 404,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "status_code": 429,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "status_code": 500,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## SDK Examples

### Python

```python
import requests

# Set up API client
api_key = "your-api-key"
base_url = "http://localhost:8000"
headers = {"Authorization": f"Bearer {api_key}"}

# Get events
response = requests.get(f"{base_url}/v1/events", headers=headers)
events = response.json()

# Query signals
signal_query = {
    "min_edge": 0.05,
    "status": "active",
    "limit": 10
}
response = requests.post(f"{base_url}/v1/signals/query", json=signal_query, headers=headers)
signals = response.json()
```

### JavaScript

```javascript
const apiKey = 'your-api-key';
const baseUrl = 'http://localhost:8000';

// Set up API client
const headers = {
  'Authorization': `Bearer ${apiKey}`,
  'Content-Type': 'application/json'
};

// Get events
const eventsResponse = await fetch(`${baseUrl}/v1/events`, { headers });
const events = await eventsResponse.json();

// Query signals
const signalQuery = {
  min_edge: 0.05,
  status: 'active',
  limit: 10
};
const signalsResponse = await fetch(`${baseUrl}/v1/signals/query`, {
  method: 'POST',
  headers,
  body: JSON.stringify(signalQuery)
});
const signals = await signalsResponse.json();
```

### cURL

```bash
# Get events
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8000/v1/events

# Query signals
curl -X POST \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"min_edge": 0.05, "status": "active", "limit": 10}' \
     http://localhost:8000/v1/signals/query
```

## Legal Notice

**EDUCATIONAL ANALYTICS ONLY**: This API provides educational analytics and data insights only. No betting facilitation, no fund movement, no tips or recommendations. All data is for informational purposes and educational analysis.

## Support

For API support:
- **Email**: api-support@betflow.local
- **Documentation**: https://docs.betflow.local
- **Status**: https://status.betflow.local
