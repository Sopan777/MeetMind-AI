import json
import logging
import re
from typing import Optional, Dict, Any

from openai import AsyncOpenAI
from core.config import settings
from schemas.analysis import MeetingInsights
from .base import AnalyzerProvider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a meeting analysis AI. You analyze meeting transcripts and extract structured insights.

Rules:
- Only extract information that is explicitly stated or clearly implied in the transcript.
- Do NOT invent or hallucinate information.
- If no items exist for a category, return an empty list.
- For timestamps, use the timestamp from the transcript where the item was mentioned.
- For deadlines, use "Not specified" if no deadline was mentioned.
- Keep the summary concise and factual.
- Respond ONLY with valid JSON. No explanation, no markdown, no code fences."""

class NVIDIAAnalyzer(AnalyzerProvider):
    """Analyzes meeting transcripts using NVIDIA Build API LLMs."""
    
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY must be set in environment variables")
            
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=settings.NVIDIA_API_URL,
        )
        self.model = settings.NVIDIA_MODEL
        logger.info(f"Initialized NVIDIAAnalyzer with model {self.model}")

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response, handling code fences and extra text."""
        # Try 1: Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try 2: Strip markdown code fences (```json ... ``` or ``` ... ```)
        fence_pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
        match = re.search(fence_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try 3: Find first { ... } block using brace matching
        start = text.find("{")
        if start != -1:
            depth = 0
            for i in range(start, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start : i + 1])
                        except json.JSONDecodeError:
                            break

        return None

    async def analyze(self, transcript_text: str) -> Optional[MeetingInsights]:
        """Legacy method for full extraction. Use analyze_agent instead."""
        pass
        
    async def analyze_agent(self, agent_prompt: str, json_schema: str) -> Optional[Dict[str, Any]]:
        """Run a specialized agent prompt."""
        try:
            full_system_prompt = f"{SYSTEM_PROMPT}\n\nJSON schema to follow strictly:\n{json_schema}"
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": full_system_prompt},
                    {"role": "user", "content": agent_prompt},
                ],
                temperature=0.1,
                max_tokens=1024,
            )

            content = response.choices[0].message.content
            if not content:
                return None

            parsed = self._extract_json(content)
            if parsed is None:
                logger.error(f"Could not extract JSON from LLM response: {content[:500]}")
                return None

            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM analysis error: {e}", extra={"operation": "analyze_nvidia"})
            return None

    async def health_check(self) -> Dict[str, Any]:
        return {
            "provider": "nvidia",
            "model": self.model,
            "configured": bool(self.api_key)
        }
