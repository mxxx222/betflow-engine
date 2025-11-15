"""
OpenTelemetry configuration for BetFlow Engine v0.9.0
Integrates tracing with Prometheus metrics for comprehensive observability.
"""

import os
import logging
from typing import Optional
from opentelemetry import trace, metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from prometheus_client import start_http_server

logger = logging.getLogger(__name__)

class OpenTelemetryConfig:
    """OpenTelemetry configuration and setup."""
    
    def __init__(self, service_name: str = "betflow-engine", service_version: str = "0.9.0"):
        self.service_name = service_name
        self.service_version = service_version
        self.resource = Resource.create({
            "service.name": service_name,
            "service.version": service_version,
            "service.instance.id": os.getenv("HOSTNAME", "unknown"),
            "deployment.environment": os.getenv("ENVIRONMENT", "development")
        })
        
    def setup_tracing(self) -> trace.Tracer:
        """Setup distributed tracing."""
        try:
            # Create tracer provider
            tracer_provider = TracerProvider(resource=self.resource)
            trace.set_tracer_provider(tracer_provider)
            
            # Configure exporters
            exporters = []
            
            # Jaeger exporter (if configured)
            jaeger_endpoint = os.getenv("JAEGER_ENDPOINT")
            if jaeger_endpoint:
                jaeger_exporter = JaegerExporter(
                    agent_host_name=os.getenv("JAEGER_AGENT_HOST", "localhost"),
                    agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
                    collector_endpoint=jaeger_endpoint,
                )
                exporters.append(jaeger_exporter)
                logger.info(f"Jaeger tracing enabled: {jaeger_endpoint}")
            
            # Console exporter (for development)
            if os.getenv("OTEL_CONSOLE_EXPORT", "false").lower() == "true":
                console_exporter = ConsoleSpanExporter()
                exporters.append(console_exporter)
                logger.info("Console tracing enabled")
            
            # Add span processors
            for exporter in exporters:
                span_processor = BatchSpanProcessor(exporter)
                tracer_provider.add_span_processor(span_processor)
            
            # Get tracer
            tracer = trace.get_tracer(self.service_name, self.service_version)
            logger.info(f"Tracing initialized for {self.service_name} v{self.service_version}")
            
            return tracer
            
        except Exception as e:
            logger.error(f"Failed to setup tracing: {e}")
            return trace.get_tracer(self.service_name, self.service_version)
    
    def setup_metrics(self) -> metrics.Meter:
        """Setup metrics collection with Prometheus integration."""
        try:
            # Create Prometheus metric reader
            prometheus_reader = PrometheusMetricReader()
            
            # Create meter provider
            meter_provider = MeterProvider(
                resource=self.resource,
                metric_readers=[prometheus_reader]
            )
            metrics.set_meter_provider(meter_provider)
            
            # Start Prometheus HTTP server
            prometheus_port = int(os.getenv("PROMETHEUS_PORT", "8080"))
            start_http_server(prometheus_port)
            logger.info(f"Prometheus metrics server started on port {prometheus_port}")
            
            # Get meter
            meter = metrics.get_meter(self.service_name, self.service_version)
            logger.info(f"Metrics initialized for {self.service_name} v{self.service_version}")
            
            return meter
            
        except Exception as e:
            logger.error(f"Failed to setup metrics: {e}")
            return metrics.get_meter(self.service_name, self.service_version)
    
    def instrument_fastapi(self, app):
        """Instrument FastAPI application."""
        try:
            FastAPIInstrumentor.instrument_app(
                app,
                tracer_provider=trace.get_tracer_provider(),
                excluded_urls="health,metrics,docs,redoc,openapi.json"
            )
            logger.info("FastAPI instrumentation enabled")
        except Exception as e:
            logger.error(f"Failed to instrument FastAPI: {e}")
    
    def instrument_dependencies(self):
        """Instrument common dependencies."""
        try:
            # Instrument HTTP requests
            RequestsInstrumentor().instrument()
            
            # Instrument SQLAlchemy (if available)
            try:
                SQLAlchemyInstrumentor().instrument()
                logger.info("SQLAlchemy instrumentation enabled")
            except Exception:
                pass
            
            # Instrument Redis (if available)
            try:
                RedisInstrumentor().instrument()
                logger.info("Redis instrumentation enabled")
            except Exception:
                pass
            
            logger.info("Dependency instrumentation completed")
            
        except Exception as e:
            logger.error(f"Failed to instrument dependencies: {e}")

class BetFlowMetrics:
    """Custom metrics for BetFlow Engine."""
    
    def __init__(self, meter: metrics.Meter):
        self.meter = meter
        
        # Engine performance metrics
        self.ev_calculation_duration = meter.create_histogram(
            name="betflow_ev_calculation_duration_seconds",
            description="Duration of EV calculations",
            unit="s"
        )
        
        self.poisson_calculation_duration = meter.create_histogram(
            name="betflow_poisson_calculation_duration_seconds",
            description="Duration of Poisson calculations",
            unit="s"
        )
        
        self.elo_calculation_duration = meter.create_histogram(
            name="betflow_elo_calculation_duration_seconds",
            description="Duration of ELO calculations",
            unit="s"
        )
        
        # Engine usage metrics
        self.mojo_usage_counter = meter.create_counter(
            name="betflow_mojo_usage_total",
            description="Total Mojo engine usage count"
        )
        
        self.fallback_usage_counter = meter.create_counter(
            name="betflow_fallback_usage_total",
            description="Total fallback to Python implementation count"
        )
        
        # SLO compliance metrics
        self.slo_violation_counter = meter.create_counter(
            name="betflow_slo_violations_total",
            description="Total SLO violations",
        )
        
        # Signal generation metrics
        self.signals_generated_counter = meter.create_counter(
            name="betflow_signals_generated_total",
            description="Total signals generated"
        )
        
        # Memory usage gauge
        self.memory_usage_gauge = meter.create_up_down_counter(
            name="betflow_memory_usage_bytes",
            description="Current memory usage in bytes"
        )
    
    def record_ev_calculation(self, duration: float, use_mojo: bool = False):
        """Record EV calculation metrics."""
        self.ev_calculation_duration.record(duration, {"engine": "mojo" if use_mojo else "python"})
        if use_mojo:
            self.mojo_usage_counter.add(1, {"operation": "ev_calculation"})
        else:
            self.fallback_usage_counter.add(1, {"operation": "ev_calculation"})
    
    def record_poisson_calculation(self, duration: float, use_mojo: bool = False):
        """Record Poisson calculation metrics."""
        self.poisson_calculation_duration.record(duration, {"engine": "mojo" if use_mojo else "python"})
        if use_mojo:
            self.mojo_usage_counter.add(1, {"operation": "poisson_calculation"})
        else:
            self.fallback_usage_counter.add(1, {"operation": "poisson_calculation"})
    
    def record_elo_calculation(self, duration: float, use_mojo: bool = False):
        """Record ELO calculation metrics."""
        self.elo_calculation_duration.record(duration, {"engine": "mojo" if use_mojo else "python"})
        if use_mojo:
            self.mojo_usage_counter.add(1, {"operation": "elo_calculation"})
        else:
            self.fallback_usage_counter.add(1, {"operation": "elo_calculation"})
    
    def record_slo_violation(self, violation_type: str, value: float, threshold: float):
        """Record SLO violation."""
        self.slo_violation_counter.add(1, {
            "violation_type": violation_type,
            "value": str(value),
            "threshold": str(threshold)
        })
    
    def record_signal_generated(self, market: str, sport: str):
        """Record signal generation."""
        self.signals_generated_counter.add(1, {"market": market, "sport": sport})
    
    def update_memory_usage(self, bytes_used: int):
        """Update memory usage gauge."""
        self.memory_usage_gauge.add(bytes_used)

def setup_observability(app, service_name: str = "betflow-api") -> tuple[trace.Tracer, BetFlowMetrics]:
    """Setup complete observability stack."""
    # Initialize OpenTelemetry
    otel_config = OpenTelemetryConfig(service_name)
    
    # Setup tracing and metrics
    tracer = otel_config.setup_tracing()
    meter = otel_config.setup_metrics()
    
    # Instrument FastAPI
    otel_config.instrument_fastapi(app)
    
    # Instrument dependencies
    otel_config.instrument_dependencies()
    
    # Create custom metrics
    betflow_metrics = BetFlowMetrics(meter)
    
    logger.info("Observability stack initialized successfully")
    return tracer, betflow_metrics
