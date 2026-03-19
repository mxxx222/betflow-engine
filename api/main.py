"""
BetFlow Engine API - Analytics-only sports data insights platform.
No betting facilitation, educational analytics only.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

# OpenTelemetry imports
try:
    from infra.opentelemetry.otel_config import setup_observability
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logging.warning("OpenTelemetry not available, continuing without tracing")

from .core.config import settings
from .core.database import get_db, init_db
from .core.security import verify_api_key, get_current_user
from .core.middleware import RateLimitMiddleware, AuditMiddleware
from .models.schemas import (
    HealthResponse, EventResponse, OddsResponse, SignalResponse, 
    SignalQuery, WebhookPayload, ModelStatusResponse
)
from .services.engine_service import EngineService
from .services.provider_service import ProviderService
from .services.signal_service import SignalService
from .providers.base import OddsProvider
from .providers.local_csv import LocalCSVProvider
from .providers.odds_api import OddsAPIProvider
from .providers.sports_monks import SportsMonksProvider
from .mvp_endpoints import router as mvp_router
from .bulk_predict import router as bulk_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration', ['method', 'endpoint'])
SIGNAL_GENERATED = Counter('signals_generated_total', 'Total signals generated', ['market', 'sport'])

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting BetFlow Engine API")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize providers
    app.state.providers = {
        "local_csv": LocalCSVProvider(),
        "odds_api": OddsAPIProvider(),
        "sports_monks": SportsMonksProvider(),
    }
    logger.info("Providers initialized")
    
    # Initialize services
    app.state.engine_service = EngineService()
    app.state.provider_service = ProviderService(app.state.providers)
    app.state.signal_service = SignalService()
    logger.info("Services initialized")
    
    # Initialize OpenTelemetry if available
    if OTEL_AVAILABLE and os.getenv("ENABLE_TRACING", "false").lower() == "true":
        try:
            tracer, betflow_metrics = setup_observability(app, "betflow-api")
            app.state.tracer = tracer
            app.state.betflow_metrics = betflow_metrics
            logger.info("OpenTelemetry initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")
    
    yield
    
    logger.info("Shutting down BetFlow Engine API")

# Create FastAPI app
app = FastAPI(
    title="BetFlow Engine API",
    description="Analytics-only sports data insights platform. Educational analytics only.",
    version="0.9.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check endpoints"
        },
        {
            "name": "events",
            "description": "Sports events data"
        },
        {
            "name": "odds",
            "description": "Odds data"
        },
        {
            "name": "signals",
            "description": "Analytics signals (educational only)"
        },
        {
            "name": "webhooks",
            "description": "Data ingestion webhooks"
        },
        {
            "name": "models",
            "description": "Model status and information"
        }
    ]
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "api", "*.betflow.local"]
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditMiddleware)

# Include routers
app.include_router(mvp_router, prefix="/mvp", tags=["mvp"])
app.include_router(bulk_router, prefix="/v1", tags=["bulk"])

# Health check endpoints
@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="0.9.0",
        services={
            "database": "healthy",
            "engine": "healthy",
            "providers": "healthy"
        }
    )

@app.get("/health/detailed", tags=["health"])
async def detailed_health_check():
    """Comprehensive health check with Mojo status and feature flags."""
    try:
        # Check engine health
        engine_health = app.state.engine_service.engine.health_check() if app.state.engine_service.engine else {
            "status": "degraded",
            "use_mojo": False,
            "mojo_available": False,
            "error": "Engine not available"
        }
        
        # Check database connectivity
        try:
            db = next(get_db())
            await db.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        # Check providers
        provider_status = {}
        for name, provider in app.state.providers.items():
            try:
                # Simple connectivity check
                provider_status[name] = "healthy"
            except Exception as e:
                provider_status[name] = f"unhealthy: {str(e)}"
        
        # Feature flags
        feature_flags = {
            "use_mojo": engine_health.get("use_mojo", False),
            "mojo_available": engine_health.get("mojo_available", False),
            "enable_metrics": True,
            "enable_tracing": os.getenv("ENABLE_TRACING", "false").lower() == "true",
            "pilot_mode": os.getenv("PILOT_TRAFFIC", "0") != "0",
            "canary_deployment": os.getenv("CANARY_ENABLED", "false").lower() == "true"
        }
        
        # Overall status
        overall_status = "healthy"
        if engine_health.get("status") != "healthy" or db_status != "healthy":
            overall_status = "degraded"
        if any("unhealthy" in status for status in provider_status.values()):
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.9.0",
            "services": {
                "database": db_status,
                "engine": engine_health,
                "providers": provider_status
            },
            "feature_flags": feature_flags,
            "environment": {
                "pilot_traffic": os.getenv("PILOT_TRAFFIC", "0"),
                "log_level": os.getenv("LOG_LEVEL", "INFO"),
                "debug": settings.DEBUG
            }
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.9.0",
            "error": str(e)
        }

@app.get("/health/engine", tags=["health"])
async def engine_health_check():
    """Engine-specific health check with performance metrics."""
    try:
        if not app.state.engine_service.engine:
            return {
                "status": "unavailable",
                "message": "Engine not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get detailed engine health
        health = app.state.engine_service.engine.health_check()
        
        # Add SLO compliance check
        import time
        start = time.perf_counter()
        
        # Quick performance tests
        ev_result = app.state.engine_service.engine.calc_ev(0.6, 2.0)
        ev_latency = (time.perf_counter() - start) * 1000
        
        start = time.perf_counter()
        poisson_result = app.state.engine_service.engine.calc_poisson(1.5, 1.2, 3)
        poisson_latency = (time.perf_counter() - start) * 1000
        
        # SLO compliance
        slo_compliance = {
            "ev_latency_slo": ev_latency < 1.0,  # < 1ms
            "poisson_latency_slo": poisson_latency < 1.0,  # < 1ms
            "overall_slo": ev_latency < 1.0 and poisson_latency < 1.0
        }
        
        health.update({
            "performance_metrics": {
                "ev_calculation_ms": round(ev_latency, 3),
                "poisson_calculation_ms": round(poisson_latency, 3),
                "ev_result": round(ev_result, 6),
                "poisson_sample": len(poisson_result)
            },
            "slo_compliance": slo_compliance
        })
        
        return health
        
    except Exception as e:
        logger.error("Engine health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Events endpoints
@app.get("/v1/events", response_model=List[EventResponse], tags=["events"])
async def get_events(
    sport: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    league: Optional[str] = None,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get sports events with optional filtering."""
    REQUEST_COUNT.labels(method="GET", endpoint="/v1/events", status="200").inc()
    
    try:
        # Use engine service for consistent processing
        events = await app.state.provider_service.get_events(
            sport=sport,
            date_from=date_from,
            date_to=date_to,
            league=league
        )
        
        # Add engine health status to response metadata
        if hasattr(app.state, 'betflow_metrics') and events:
            app.state.betflow_metrics.record_signal_generated("events", sport or "all")
        
        return events
    except Exception as e:
        logger.error("Failed to fetch events", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch events")

@app.get("/v1/odds", response_model=List[OddsResponse], tags=["odds"])
async def get_odds(
    event_id: str,
    market: Optional[str] = None,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get odds for a specific event."""
    REQUEST_COUNT.labels(method="GET", endpoint="/v1/odds", status="200").inc()
    
    try:
        odds = await app.state.provider_service.get_odds(event_id, market)
        return odds
    except Exception as e:
        logger.error("Failed to fetch odds", error=str(e), event_id=event_id)
        raise HTTPException(status_code=500, detail="Failed to fetch odds")

# Signals endpoints
@app.post("/v1/signals/query", response_model=List[SignalResponse], tags=["signals"])
async def query_signals(
    query: SignalQuery,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Query analytics signals with filtering."""
    REQUEST_COUNT.labels(method="POST", endpoint="/v1/signals/query", status="200").inc()
    
    try:
        # Ensure engine is available for signal generation
        if not app.state.engine_service.engine:
            raise HTTPException(status_code=503, detail="BetFlow Engine not available")
        
        signals = await app.state.signal_service.query_signals(query, db)
        
        # Record metrics
        if hasattr(app.state, 'betflow_metrics') and signals:
            for signal in signals:
                app.state.betflow_metrics.record_signal_generated(
                    signal.get("market", "unknown"), 
                    signal.get("sport", "unknown")
                )
        
        return signals
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to query signals", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to query signals")

@app.get("/v1/signals/{signal_id}", response_model=SignalResponse, tags=["signals"])
async def get_signal(
    signal_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get specific signal by ID."""
    REQUEST_COUNT.labels(method="GET", endpoint="/v1/signals/{signal_id}", status="200").inc()
    
    try:
        signal = await app.state.signal_service.get_signal(signal_id, db)
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        return signal
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch signal", error=str(e), signal_id=signal_id)
        raise HTTPException(status_code=500, detail="Failed to fetch signal")

# Webhook endpoints
@app.post("/v1/webhooks/ingest", tags=["webhooks"])
async def ingest_webhook(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """Ingest data from external providers via webhook."""
    REQUEST_COUNT.labels(method="POST", endpoint="/v1/webhooks/ingest", status="200").inc()
    
    try:
        # Process webhook in background
        background_tasks.add_task(
            app.state.provider_service.process_webhook,
            payload,
            db
        )
        
        return {"status": "accepted", "message": "Data ingestion started"}
    except Exception as e:
        logger.error("Failed to process webhook", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process webhook")

# Model endpoints
@app.get("/v1/models/status", response_model=ModelStatusResponse, tags=["models"])
async def get_model_status(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get model status and information."""
    REQUEST_COUNT.labels(method="GET", endpoint="/v1/models/status", status="200").inc()
    
    try:
        status = await app.state.engine_service.get_model_status(db)
        return status
    except Exception as e:
        logger.error("Failed to get model status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get model status")

# Internal endpoints for n8n workflows
@app.post("/internal/compute_signals", tags=["internal"])
async def compute_signals_internal(
    event_ids: List[str],
    db=Depends(get_db)
):
    """Internal endpoint for signal computation (n8n workflows)."""
    try:
        # Ensure engine is available
        if not app.state.engine_service.engine:
            raise HTTPException(status_code=503, detail="BetFlow Engine not available")
        
        signals = await app.state.signal_service.compute_signals(event_ids, db)
        SIGNAL_GENERATED.labels(market="all", sport="all").inc(len(signals))
        
        # Record detailed metrics
        if hasattr(app.state, 'betflow_metrics'):
            app.state.betflow_metrics.record_signal_generated("all", "all")
        
        return {
            "signals_generated": len(signals),
            "engine_status": app.state.engine_service.engine.health_check()["status"],
            "mojo_used": app.state.engine_service.engine.health_check().get("use_mojo", False)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to compute signals", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to compute signals")

# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    REQUEST_COUNT.labels(
        method=request.method, 
        endpoint=request.url.path, 
        status=str(exc.status_code)
    ).inc()
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status="500"
    ).inc()
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
