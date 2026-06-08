import logging
from typing import Optional
from core.config import settings
from .meeting_timeline import MeetingTimeline
from schemas.events import EventType

logger = logging.getLogger(__name__)

class ContextBuilder:
    """Builds hierarchical context prompts for the LLM analyzer from the MeetingTimeline."""
    
    @staticmethod
    def build_action_prompt(timeline: MeetingTimeline, entities: Optional[list[str]] = None) -> Optional[str]:
        """Builds the prompt for the Action Item Agent."""
        recent_speech = timeline.get_recent(settings.TIER1_MAX_EVENTS, types=[EventType.SPEECH])
        if not recent_speech:
            return None
            
        prompt_lines = ["=== RECENT TRANSCRIPT ==="]
        prompt_lines.append(timeline.get_speech_text(since_seq=recent_speech[0].sequence - 1))
        
        if entities:
            prompt_lines.append("\n=== KNOWN ENTITIES ===")
            prompt_lines.append(f"The following entities/people have been mentioned: {', '.join(entities)}")
            
        prompt_lines.append("\n=== TASK ===")
        prompt_lines.append("Extract any NEW Action Items from the recent transcript.")
        prompt_lines.append("RULES:")
        prompt_lines.append("1. Only extract tasks that have an explicit or strongly implied owner and action.")
        prompt_lines.append("2. EVIDENCE REQUIRED: You MUST provide the exact verbatim quote from the transcript that supports this action item. Do not paraphrase the quote.")
        prompt_lines.append("3. CONFIDENCE SCORE: Provide a confidence score from 0.0 to 1.0 based on how certain you are this is a real task assignment.")
        return "\n".join(prompt_lines)

    @staticmethod
    def build_decision_prompt(timeline: MeetingTimeline, entities: Optional[list[str]] = None) -> Optional[str]:
        """Builds the prompt for the Decision Agent."""
        recent_speech = timeline.get_recent(settings.TIER1_MAX_EVENTS, types=[EventType.SPEECH])
        if not recent_speech:
            return None
            
        prompt_lines = ["=== RECENT TRANSCRIPT ==="]
        prompt_lines.append(timeline.get_speech_text(since_seq=recent_speech[0].sequence - 1))
        
        if entities:
            prompt_lines.append("\n=== KNOWN ENTITIES ===")
            prompt_lines.append(f"The following entities/people have been mentioned: {', '.join(entities)}")
            
        prompt_lines.append("\n=== TASK ===")
        prompt_lines.append("Extract any NEW Decisions made in the recent transcript.")
        prompt_lines.append("RULES:")
        prompt_lines.append("1. Only extract firm decisions, not just suggestions or ideas.")
        prompt_lines.append("2. EVIDENCE REQUIRED: You MUST provide the exact verbatim quote from the transcript that supports this decision. Do not paraphrase the quote.")
        prompt_lines.append("3. CONFIDENCE SCORE: Provide a confidence score from 0.0 to 1.0 based on how certain you are this is a final decision.")
        return "\n".join(prompt_lines)
        
    @staticmethod
    def build_summary_prompt(timeline: MeetingTimeline, current_summary: Optional[str]) -> Optional[str]:
        """
        Builds the prompt for Channel 2 (summary generation).
        Combines the previous summary with all new speech since that summary was created.
        """
        # If we have no previous summary, just summarize all speech so far
        if not current_summary:
            all_speech = timeline.get_speech_text()
            if not all_speech.strip():
                return None
            
            prompt_lines = ["=== MEETING TRANSCRIPT SO FAR ==="]
            prompt_lines.append(all_speech)
            prompt_lines.append("\n=== TASK ===")
            prompt_lines.append("Write a concise, running summary of the meeting so far. 2-5 sentences capturing key points.")
            return "\n".join(prompt_lines)
            
        # If we DO have a previous summary, combine it with recent speech
        # Find the last time we generated an insight (which includes summary generation)
        recent_speech_text = timeline.get_speech_text(since_seq=timeline.last_insight_seq)
        
        if not recent_speech_text.strip():
            # No new speech since last summary
            return None
            
        prompt_lines = ["=== PREVIOUS SUMMARY ==="]
        prompt_lines.append(current_summary)
        
        prompt_lines.append("\n=== NEW TRANSCRIPT ===")
        prompt_lines.append(recent_speech_text)
        
        prompt_lines.append("\n=== TASK ===")
        prompt_lines.append("Update the previous summary with the new information. Keep it concise, 2-5 sentences.")
        
        return "\n".join(prompt_lines)
