"""
Vectorized bulk prediction API for BetFlow Engine v0.9.0
Handles batch processing of predictions with optimized performance.
"""

import time
import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field, validator
import structlog

from .core.security import get_current_user
from .services.engine_service import EngineService

logger = structlog.get_logger()

router = APIRouter()

class EVRequest(BaseModel):
    """Single EV calculation request."""
    probability: float = Field(..., gt=0, lt=1, description="True probability (0-1)")
    odds: float = Field(..., gt=1, description="Decimal odds (>1)")
    id: Optional[str] = Field(None, description="Optional request ID")

class PoissonRequest(BaseModel):
    """Single Poisson calculation request."""
    home_rate: float = Field(..., ge=0, description="Home team expected goals")
    away_rate: float = Field(..., ge=0, description="Away team expected goals")
    max_goals: int = Field(6, ge=1, le=20, description="Maximum goals to consider")
    id: Optional[str] = Field(None, description="Optional request ID")

class MatchPredictionRequest(BaseModel):
    """Single match prediction request."""
    home_team: str = Field(..., min_length=1, max_length=100)
    away_team: str = Field(..., min_length=1, max_length=100)
    league: str = Field(..., min_length=1, max_length=50)
    id: Optional[str] = Field(None, description="Optional request ID")

class BulkEVRequest(BaseModel):
    """Bulk EV calculation request."""
    requests: List[EVRequest] = Field(..., min_items=1, max_items=10000)
    
    @validator('requests')
    def validate_batch_size(cls, v):
        if len(v) > 10000:
            raise ValueError("Maximum batch size is 10,000 requests")
        return v

class BulkPoissonRequest(BaseModel):
    """Bulk Poisson calculation request."""
    requests: List[PoissonRequest] = Field(..., min_items=1, max_items=1000)
    
    @validator('requests')
    def validate_batch_size(cls, v):
        if len(v) > 1000:
            raise ValueError("Maximum batch size is 1,000 requests for Poisson calculations")
        return v

class BulkMatchPredictionRequest(BaseModel):
    """Bulk match prediction request."""
    requests: List[MatchPredictionRequest] = Field(..., min_items=1, max_items=1000)
    
    @validator('requests')
    def validate_batch_size(cls, v):
        if len(v) > 1000:
            raise ValueError("Maximum batch size is 1,000 requests for match predictions")
        return v

class BulkResponse(BaseModel):
    """Bulk operation response."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    processing_time_ms: float
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]

class BulkProcessor:
    """Handles bulk processing with performance optimization."""
    
    def __init__(self, engine_service: EngineService):
        self.engine_service = engine_service
        
    async def process_bulk_ev(self, requests: List[EVRequest]) -> BulkResponse:
        """Process bulk EV calculations with vectorization."""
        start_time = time.perf_counter()
        results = []
        errors = []
        
        try:
            # Process in chunks for better memory management
            chunk_size = 1000
            for i in range(0, len(requests), chunk_size):
                chunk = requests[i:i + chunk_size]
                chunk_results, chunk_errors = await self._process_ev_chunk(chunk)
                results.extend(chunk_results)
                errors.extend(chunk_errors)
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            return BulkResponse(
                total_requests=len(requests),
                successful_requests=len(results),
                failed_requests=len(errors),
                processing_time_ms=processing_time,
                results=results,
                errors=errors
            )
            
        except Exception as e:
            logger.error("Bulk EV processing failed", error=str(e))
            raise HTTPException(status_code=500, detail=f"Bulk processing failed: {str(e)}")
    
    async def _process_ev_chunk(self, chunk: List[EVRequest]) -> tuple[List[Dict], List[Dict]]:
        """Process a chunk of EV requests."""
        results = []
        errors = []
        
        # Use asyncio.gather for concurrent processing
        tasks = []
        for req in chunk:
            task = self._calculate_single_ev(req)
            tasks.append(task)
        
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(chunk_results):
            req = chunk[i]
            if isinstance(result, Exception):
                errors.append({
                    "id": req.id,
                    "error": str(result),
                    "request_index": i
                })
            else:
                results.append({
                    "id": req.id,
                    "request_index": i,
                    "probability": req.probability,
                    "odds": req.odds,
                    "expected_value": result
                })
        
        return results, errors
    
    async def _calculate_single_ev(self, req: EVRequest) -> float:
        """Calculate single EV with error handling."""
        try:
            return await self.engine_service.calculate_ev(req.probability, req.odds)
        except Exception as e:
            logger.error(f"EV calculation failed for request {req.id}", error=str(e))
            raise
    
    async def process_bulk_poisson(self, requests: List[PoissonRequest]) -> BulkResponse:
        """Process bulk Poisson calculations."""
        start_time = time.perf_counter()
        results = []
        errors = []
        
        try:
            # Process sequentially for Poisson (more memory intensive)
            for i, req in enumerate(requests):
                try:
                    probabilities = await self.engine_service.calculate_poisson_probabilities(
                        req.home_rate, req.away_rate, req.max_goals
                    )
                    
                    results.append({
                        "id": req.id,
                        "request_index": i,
                        "home_rate": req.home_rate,
                        "away_rate": req.away_rate,
                        "max_goals": req.max_goals,
                        "probabilities": probabilities
                    })
                    
                except Exception as e:
                    errors.append({
                        "id": req.id,
                        "error": str(e),
                        "request_index": i
                    })
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            return BulkResponse(
                total_requests=len(requests),
                successful_requests=len(results),
                failed_requests=len(errors),
                processing_time_ms=processing_time,
                results=results,
                errors=errors
            )
            
        except Exception as e:
            logger.error("Bulk Poisson processing failed", error=str(e))
            raise HTTPException(status_code=500, detail=f"Bulk processing failed: {str(e)}")
    
    async def process_bulk_match_predictions(self, requests: List[MatchPredictionRequest]) -> BulkResponse:
        """Process bulk match predictions."""
        start_time = time.perf_counter()
        results = []
        errors = []
        
        try:
            # Process with limited concurrency to avoid overwhelming the engine
            semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent predictions
            
            async def process_single_prediction(req: MatchPredictionRequest, index: int):
                async with semaphore:
                    try:
                        prediction = await self.engine_service.predict_match_outcome(
                            req.home_team, req.away_team, req.league
                        )
                        
                        return {
                            "id": req.id,
                            "request_index": index,
                            "home_team": req.home_team,
                            "away_team": req.away_team,
                            "league": req.league,
                            "predictions": prediction
                        }
                        
                    except Exception as e:
                        return {
                            "id": req.id,
                            "error": str(e),
                            "request_index": index
                        }
            
            # Process all predictions concurrently
            tasks = [process_single_prediction(req, i) for i, req in enumerate(requests)]
            prediction_results = await asyncio.gather(*tasks)
            
            # Separate results and errors
            for result in prediction_results:
                if "error" in result:
                    errors.append(result)
                else:
                    results.append(result)
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            return BulkResponse(
                total_requests=len(requests),
                successful_requests=len(results),
                failed_requests=len(errors),
                processing_time_ms=processing_time,
                results=results,
                errors=errors
            )
            
        except Exception as e:
            logger.error("Bulk match prediction processing failed", error=str(e))
            raise HTTPException(status_code=500, detail=f"Bulk processing failed: {str(e)}")

# API endpoints
@router.post("/bulk/ev", response_model=BulkResponse, tags=["bulk"])
async def bulk_calculate_ev(
    request: BulkEVRequest,
    background_tasks: BackgroundTasks,
    engine_service: EngineService = Depends(),
    current_user=Depends(get_current_user)
):
    """
    Bulk calculate expected values for multiple probability/odds pairs.
    Optimized for high-throughput processing with vectorization.
    """
    logger.info(f"Bulk EV calculation requested", count=len(request.requests), user=current_user.get("id"))
    
    processor = BulkProcessor(engine_service)
    
    try:
        result = await processor.process_bulk_ev(request.requests)
        
        # Log performance metrics in background
        background_tasks.add_task(
            log_bulk_performance,
            "bulk_ev",
            len(request.requests),
            result.processing_time_ms,
            result.successful_requests,
            result.failed_requests
        )
        
        return result
        
    except Exception as e:
        logger.error("Bulk EV calculation failed", error=str(e))
        raise

@router.post("/bulk/poisson", response_model=BulkResponse, tags=["bulk"])
async def bulk_calculate_poisson(
    request: BulkPoissonRequest,
    background_tasks: BackgroundTasks,
    engine_service: EngineService = Depends(),
    current_user=Depends(get_current_user)
):
    """
    Bulk calculate Poisson probabilities for multiple rate pairs.
    Memory-optimized processing for complex calculations.
    """
    logger.info(f"Bulk Poisson calculation requested", count=len(request.requests), user=current_user.get("id"))
    
    processor = BulkProcessor(engine_service)
    
    try:
        result = await processor.process_bulk_poisson(request.requests)
        
        # Log performance metrics in background
        background_tasks.add_task(
            log_bulk_performance,
            "bulk_poisson",
            len(request.requests),
            result.processing_time_ms,
            result.successful_requests,
            result.failed_requests
        )
        
        return result
        
    except Exception as e:
        logger.error("Bulk Poisson calculation failed", error=str(e))
        raise

@router.post("/bulk/predict", response_model=BulkResponse, tags=["bulk"])
async def bulk_predict_matches(
    request: BulkMatchPredictionRequest,
    background_tasks: BackgroundTasks,
    engine_service: EngineService = Depends(),
    current_user=Depends(get_current_user)
):
    """
    Bulk predict match outcomes for multiple team pairs.
    Concurrency-limited processing for resource management.
    """
    logger.info(f"Bulk match prediction requested", count=len(request.requests), user=current_user.get("id"))
    
    processor = BulkProcessor(engine_service)
    
    try:
        result = await processor.process_bulk_match_predictions(request.requests)
        
        # Log performance metrics in background
        background_tasks.add_task(
            log_bulk_performance,
            "bulk_predict",
            len(request.requests),
            result.processing_time_ms,
            result.successful_requests,
            result.failed_requests
        )
        
        return result
        
    except Exception as e:
        logger.error("Bulk match prediction failed", error=str(e))
        raise

async def log_bulk_performance(operation: str, total_requests: int, processing_time_ms: float,
                             successful: int, failed: int):
    """Log bulk operation performance metrics."""
    throughput = total_requests / (processing_time_ms / 1000) if processing_time_ms > 0 else 0
    
    logger.info(
        "Bulk operation completed",
        operation=operation,
        total_requests=total_requests,
        successful_requests=successful,
        failed_requests=failed,
        processing_time_ms=processing_time_ms,
        throughput_per_second=throughput,
        success_rate=successful / total_requests if total_requests > 0 else 0
    )
