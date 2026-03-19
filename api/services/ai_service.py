"""
AI service for multi-provider AI integration (OpenRouter, Venice AI).
"""

import logging
import json
import os
from typing import Dict, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered predictions using OpenRouter or Venice API."""

    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "openrouter").lower()

        if self.provider == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY")
            base_url = "https://openrouter.ai/api/v1"
            self.model = os.getenv("OPENROUTER_MODEL", "cognitivecomputations/dolphin-mistral-7b")
        elif self.provider == "venice":
            api_key = os.getenv("VENICE_API_KEY")
            base_url = "https://api.venice.ai/api/v1"
            self.model = os.getenv("VENICE_MODEL", "venice-uncensored")
        else:
            logger.error(f"Unknown AI provider: {self.provider}")
            api_key = None
            base_url = None
            self.model = None

        if not api_key:
            logger.warning(f"{self.provider.upper()}_API_KEY not found, AI service will be disabled")
            self.client = None
        else:
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url
            )
            logger.info(f"AI service initialized with provider: {self.provider}, model: {self.model}")

    async def predict_match_outcome(self, home_team: str, away_team: str, league: str) -> Optional[Dict[str, float]]:
        """Predict match outcome using AI."""
        if not self.client:
            logger.warning("AI client not available")
            return None

        prompt = f"""You are an expert sports analyst specializing in soccer predictions.

Predict the outcome of the soccer match between {home_team} and {away_team} in the {league} league.

Based on current form, historical data, and league context, provide realistic probabilities for the three possible outcomes.

Respond ONLY with a JSON object in this exact format:
{{"home_win": 0.45, "draw": 0.25, "away_win": 0.30}}

Ensure the probabilities sum to 1.0 and are realistic for soccer."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise sports prediction AI that responds only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3  # Lower temperature for more consistent predictions
            )

            content = response.choices[0].message.content.strip()
            logger.info(f"AI response: {content}")

            # Parse JSON
            try:
                result = json.loads(content)
                # Validate structure
                if all(key in result for key in ["home_win", "draw", "away_win"]):
                    # Normalize probabilities
                    total = sum(result.values())
                    if total > 0:
                        result = {k: v/total for k, v in result.items()}
                    return result
                else:
                    logger.error(f"Invalid AI response structure: {result}")
                    return None
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {content}, error: {e}")
                return None

        except Exception as e:
            logger.error(f"AI prediction failed: {e}")
            return None