import json
import logging
import re
import time

from openai import AsyncOpenAI

from models.schemas import MeetingInsights

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a meeting analysis AI. You analyze meeting transcripts and extract structured insights.

Given the meeting transcript so far, extract the following:

1. **Action Items**: Tasks assigned to specific people. Include the owner, the task description, and any mentioned deadline.
2. **Decisions**: Key decisions made during the meeting.
3. **Risks**: Blockers, risks, concerns, or dependencies mentioned.
4. **Summary**: A concise, continuously updated summary of the meeting so far. Write it as 2-5 sentences capturing the key points discussed.

Rules:
- Only extract information that is explicitly stated or clearly implied in the transcript.
- Do NOT invent or hallucinate information.
- If no items exist for a category, return an empty list.
- For timestamps, use the timestamp from the transcript where the item was mentioned.
- For deadlines, use "Not specified" if no deadline was mentioned.
- Keep the summary concise and factual.
- Respond ONLY with valid JSON. No explanation, no markdown, no code fences.

JSON schema:
{"action_items": [{"owner": "string", "task": "string", "deadline": "string"}], "decisions": [{"decision": "string", "timestamp": "string"}], "risks": [{"description": "string", "timestamp": "string"}], "summary": "string"}"""


class LLMAnalyzer:
    """Analyzes meeting transcripts using NVIDIA Build API LLMs."""

    def __init__(self, api_key: str, api_url: str, model: str):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_url,
        )
        self.model = model
        self._transcript_history: list[dict] = []
        self._last_analysis_time: float = 0
        self._analysis_interval: float = 15  # seconds between analyses
        self._last_insights: MeetingInsights | None = None

    def add_transcript(self, segment: dict) -> None:
        """Add a transcript segment to the history."""
        self._transcript_history.append(segment)

    def should_analyze(self) -> bool:
        """Check if enough time has passed and there is new transcript data."""
        if not self._transcript_history:
            return False
        return (time.time() - self._last_analysis_time) >= self._analysis_interval

    def _build_transcript_text(self) -> str:
        """Build a formatted transcript string from history."""
        lines = []
        for seg in self._transcript_history:
            lines.append(f"[{seg['timestamp']}] {seg['speaker']}: {seg['text']}")
        return "\n".join(lines)

    @staticmethod
    def _extract_json(text: str) -> dict | None:
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

    async def analyze(self) -> MeetingInsights | None:
        """Run LLM analysis on the current transcript.

        Returns MeetingInsights or None on failure.
        """
        if not self._transcript_history:
            return self._last_insights

        transcript_text = self._build_transcript_text()
        self._last_analysis_time = time.time()

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Analyze the following meeting transcript:\n\n{transcript_text}",
                    },
                ],
                temperature=0.1,
                max_tokens=2048,
            )

            content = response.choices[0].message.content
            if not content:
                return self._last_insights

            logger.info(f"LLM raw response (first 300 chars): {content[:300]}")

            parsed = self._extract_json(content)
            if parsed is None:
                logger.error(f"Could not extract JSON from LLM response: {content[:500]}")
                return self._last_insights

            insights = MeetingInsights(**parsed)
            self._last_insights = insights
            return insights

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return self._last_insights
        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            return self._last_insights

    def get_last_insights(self) -> MeetingInsights | None:
        """Return the most recent analysis results."""
        return self._last_insights
