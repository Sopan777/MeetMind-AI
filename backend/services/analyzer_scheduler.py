import asyncio
import logging
from datetime import datetime, timezone
import uuid
import difflib
from typing import List, Dict, Any

from core.config import settings
from .meeting_state import MeetingState
from .context_builder import ContextBuilder
from schemas.events import MeetingEvent, EventType, InsightType
from schemas.analysis import MeetingInsights, ActionItem, Decision, Risk
from providers.analysis.base import AnalyzerProvider

logger = logging.getLogger(__name__)

class AnalyzerScheduler:
    """
    Two-channel scheduler for LLM analysis.
    Channel 1: Extraction (Action Items, Decisions, Risks) - runs frequently
    Channel 2: Summary - runs less frequently, builds cumulative context
    """
    
    def __init__(self, meeting_id: str):
        self.meeting_id = meeting_id
        
        # Track when we last ran each channel
        self.last_extraction_utc: datetime = None
        self.last_summary_utc: datetime = None
        
        # Track utterances since last run
        self.utterances_since_extraction: int = 0
        self.utterances_since_summary: int = 0
        
        # Running tasks
        self._extraction_task: asyncio.Task = None
        self._summary_task: asyncio.Task = None
        
        # Current combined state to send to frontend
        self.current_insights = MeetingInsights(
            action_items=[], decisions=[], risks=[], summary=""
        )
        
    def on_speech_event(self, state: MeetingState, analyzer: AnalyzerProvider, websocket, persistence) -> None:
        """Called whenever a new speech event is added to the timeline."""
        self.utterances_since_extraction += 1
        
        now = datetime.now(timezone.utc)
        
        if self._should_run(now):
            self._trigger_agents(state, analyzer, websocket, persistence, now)
            
    def force_trigger(self, state: MeetingState, analyzer: AnalyzerProvider, websocket, persistence) -> None:
        """User pressed 'Analyze Now'. Bypasses all thresholds."""
        now = datetime.now(timezone.utc)
        self._trigger_agents(state, analyzer, websocket, persistence, now)

    def _should_run(self, now: datetime) -> bool:
        if self._extraction_task and not self._extraction_task.done():
            return False # Already running
            
        if self.utterances_since_extraction >= settings.EXTRACTION_UTTERANCE_THRESHOLD:
            if not self.last_extraction_utc or (now - self.last_extraction_utc).total_seconds() >= settings.ANALYZER_MIN_INTERVAL_SECONDS:
                return True
        return False
        
    def _trigger_agents(self, state: MeetingState, analyzer: AnalyzerProvider, websocket, persistence, now: datetime) -> None:
        self.utterances_since_extraction = 0
        self.last_extraction_utc = now

        entities = state.entity_registry.get_all()
        action_prompt = ContextBuilder.build_action_prompt(state.timeline, entities)
        decision_prompt = ContextBuilder.build_decision_prompt(state.timeline, entities)
        risk_prompt = ContextBuilder.build_risk_prompt(state.timeline, entities)
        summary_prompt = ContextBuilder.build_summary_prompt(state.timeline, self.current_insights.summary)

        self._extraction_task = asyncio.create_task(
            self._run_parallel_agents(action_prompt, decision_prompt, risk_prompt, summary_prompt, state, analyzer, websocket, persistence)
        )
        
    async def _run_parallel_agents(self, action_prompt: str, decision_prompt: str, risk_prompt: str, summary_prompt: str, state: MeetingState, analyzer: AnalyzerProvider, websocket, persistence=None) -> None:
        try:
            logger.info(f"Running parallel multi-agent pipeline for {self.meeting_id}...")

            action_schema = '{"action_items": [{"owner": "string", "task": "string", "deadline": "string", "quote": "string", "confidence": "float (0.0-1.0)"}]}'
            decision_schema = '{"decisions": [{"decision": "string", "timestamp": "string", "quote": "string", "confidence": "float (0.0-1.0)"}]}'
            risk_schema = '{"risks": [{"description": "string", "timestamp": "string", "quote": "string", "confidence": "float (0.0-1.0)"}]}'
            summary_schema = '{"summary": "string"}'

            tasks = []
            tasks.append(analyzer.analyze_agent(action_prompt, action_schema) if action_prompt else asyncio.sleep(0, result=None))
            tasks.append(analyzer.analyze_agent(decision_prompt, decision_schema) if decision_prompt else asyncio.sleep(0, result=None))
            tasks.append(analyzer.analyze_agent(risk_prompt, risk_schema) if risk_prompt else asyncio.sleep(0, result=None))
            tasks.append(analyzer.analyze_agent(summary_prompt, summary_schema) if summary_prompt else asyncio.sleep(0, result=None))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            action_result = results[0] if not isinstance(results[0], Exception) else None
            decision_result = results[1] if not isinstance(results[1], Exception) else None
            risk_result = results[2] if not isinstance(results[2], Exception) else None
            summary_result = results[3] if not isinstance(results[3], Exception) else None

            any_llm_failed = any(isinstance(r, Exception) for r in results)

            extraction_warnings = 0

            if action_result and "action_items" in action_result:
                for new_item in action_result["action_items"]:
                    if not new_item.get("quote"):
                        logger.warning(f"Action item dropped (no quote): {new_item.get('task', '<unknown>')}")
                        extraction_warnings += 1
                        continue
                    # Skip re-extraction of already-reviewed items
                    if any(
                        e.review_status in ("accepted", "rejected") and
                        difflib.SequenceMatcher(None, e.task.lower(), new_item.get("task", "").lower()).ratio() > 0.75
                        for e in self.current_insights.action_items
                    ):
                        continue
                    is_duplicate = False
                    for existing in self.current_insights.action_items:
                        task_sim = difflib.SequenceMatcher(None, existing.task.lower(), new_item.get("task", "").lower()).ratio()
                        owner_sim = difflib.SequenceMatcher(None, existing.owner.lower(), new_item.get("owner", "").lower()).ratio()
                        if task_sim > 0.75 or (task_sim > 0.6 and owner_sim > 0.8):
                            is_duplicate = True
                            new_conf = min(max(new_item.get("confidence", 0), 0.0), 1.0)
                            if new_conf > existing.confidence:
                                existing.confidence = new_conf
                            new_quote = new_item.get("quote", "")
                            if new_quote and new_quote not in existing.quote:
                                existing.quote = existing.quote + " | " + new_quote
                            break
                    if not is_duplicate:
                        try:
                            item = new_item.copy()
                            item["confidence"] = min(max(float(item.get("confidence", 0.5)), 0.0), 1.0)
                            self.current_insights.action_items.append(ActionItem(**item))
                        except Exception as e:
                            logger.warning(f"Skipping malformed action item: {e} — data: {new_item}")
                            extraction_warnings += 1

            if decision_result and "decisions" in decision_result:
                for new_item in decision_result["decisions"]:
                    if not new_item.get("quote"):
                        logger.warning(f"Decision dropped (no quote): {new_item.get('decision', '<unknown>')}")
                        extraction_warnings += 1
                        continue
                    is_duplicate = False
                    for existing in self.current_insights.decisions:
                        similarity = difflib.SequenceMatcher(None, existing.decision.lower(), new_item.get("decision", "").lower()).ratio()
                        if similarity > 0.75:
                            is_duplicate = True
                            new_conf = min(max(new_item.get("confidence", 0), 0.0), 1.0)
                            if new_conf > existing.confidence:
                                existing.confidence = new_conf
                            break
                    if not is_duplicate:
                        try:
                            item = new_item.copy()
                            item["confidence"] = min(max(float(item.get("confidence", 0.5)), 0.0), 1.0)
                            self.current_insights.decisions.append(Decision(**item))
                        except Exception as e:
                            logger.warning(f"Skipping malformed decision: {e} — data: {new_item}")
                            extraction_warnings += 1

            if risk_result and "risks" in risk_result:
                for new_item in risk_result["risks"]:
                    if not new_item.get("quote"):
                        logger.warning(f"Risk dropped (no quote): {new_item.get('description', '<unknown>')}")
                        extraction_warnings += 1
                        continue
                    is_duplicate = False
                    for existing in self.current_insights.risks:
                        similarity = difflib.SequenceMatcher(None, existing.description.lower(), new_item.get("description", "").lower()).ratio()
                        if similarity > 0.75:
                            is_duplicate = True
                            new_conf = min(max(new_item.get("confidence", 0), 0.0), 1.0)
                            if new_conf > existing.confidence:
                                existing.confidence = new_conf
                            break
                    if not is_duplicate:
                        try:
                            item = new_item.copy()
                            item["confidence"] = min(max(float(item.get("confidence", 0.5)), 0.0), 1.0)
                            self.current_insights.risks.append(Risk(**item))
                        except Exception as e:
                            logger.warning(f"Skipping malformed risk: {e} — data: {new_item}")
                            extraction_warnings += 1

            if summary_result and "summary" in summary_result:
                self.current_insights.summary = summary_result["summary"]

            insights_payload = self.current_insights.model_dump()
            if extraction_warnings:
                insights_payload["extraction_warnings"] = extraction_warnings

            await websocket.send_json({
                "type": "insights",
                "data": insights_payload,
            })

            if any_llm_failed:
                await websocket.send_json({
                    "type": "error",
                    "message": "One or more analysis agents failed. Results may be incomplete.",
                })

            if state.persistence:
                asyncio.create_task(state.persistence.save_insights(self.meeting_id, self.current_insights))

            insight_event = MeetingEvent(
                id=str(uuid.uuid4()),
                meeting_id=self.meeting_id,
                event_type=EventType.INSIGHT,
                sequence=-1,
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                insight_type=InsightType.SUMMARY,
                content_json=self.current_insights.model_dump_json()
            )
            state.timeline.append(insight_event)

        except Exception as e:
            logger.error(f"Multi-agent pipeline failed: {e}")
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": "Analysis pipeline encountered an unexpected error.",
                })
            except Exception:
                pass
