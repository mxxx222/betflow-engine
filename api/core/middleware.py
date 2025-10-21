"""
Custom middleware for BetFlow Engine API.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import structlog

logger = structlog.get_logger()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, calls_per_minute: int = 100):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.clients = {}  # In production, use Redis
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting."""
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old entries
        self.clients = {
            ip: times for ip, times in self.clients.items()
            if any(t > current_time - 60 for t in times)
        }
        
        # Check rate limit
        if client_ip in self.clients:
            recent_calls = [t for t in self.clients[client_ip] if t > current_time - 60]
            if len(recent_calls) >= self.calls_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded", "retry_after": 60}
                )
        else:
            self.clients[client_ip] = []
        
        # Record this call
        self.clients[client_ip].append(current_time)
        
        response = await call_next(request)
        return response

class AuditMiddleware(BaseHTTPMiddleware):
    """Audit logging middleware."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log all requests for audit trail."""
        start_time = time.time()
        
        # Extract request info
        client_ip = request.client.host
        method = request.method
        path = request.url.path
        user_agent = request.headers.get("user-agent", "")
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log audit entry
        logger.info(
            "API request",
            method=method,
            path=path,
            status_code=response.status_code,
            client_ip=client_ip,
            duration=duration,
            user_agent=user_agent
        )
        
        return response

class ComplianceMiddleware(BaseHTTPMiddleware):
    """Compliance and legal compliance middleware."""
    
    def __init__(self, app):
        super().__init__(app)
        self.blocked_patterns = [
            "bet", "stake", "wager", "gamble", "tip", "prediction"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check for compliance violations."""
        # Check request body for prohibited terms
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                body_text = body.decode("utf-8", errors="ignore").lower()
                
                for pattern in self.blocked_patterns:
                    if pattern in body_text:
                        return JSONResponse(
                            status_code=400,
                            content={
                                "error": "Content violates compliance policy",
                                "message": "Educational analytics only. No betting facilitation."
                            }
                        )
            except Exception:
                pass  # Continue if body parsing fails
        
        response = await call_next(request)
        
        # Add compliance headers
        response.headers["X-Legal-Mode"] = "analytics-only"
        response.headers["X-Compliance"] = "educational-only"
        
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
