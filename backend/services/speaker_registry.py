import logging
import time
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Used for clustering voice embeddings
# 0.75 is recommended for lossy/compressed audio (like Google Meet)
MERGE_THRESHOLD = 0.75 
TEMPORAL_DRIFT_THRESHOLD = 0.60
MIN_UTTERANCE_LENGTH = 1.5  # seconds
MIN_SAMPLES_FOR_UPDATE = 3  # minimum utterances before we trust the centroid
EMA_ALPHA = 0.1  # learning rate for exponential moving average

@dataclass
class SpeakerProfile:
    label: str
    display_name: Optional[str]
    centroid: Optional[np.ndarray]
    sample_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    total_speaking_seconds: float
    is_enrolled: bool

class SpeakerRegistry:
    """
    Manages speaker identities and voice embeddings (centroids) for a single meeting.
    Responsible for tracking speakers across utterances and resolving temporary labels
    (SPEAKER_00) to global labels (Speaker_0).
    """
    
    def __init__(self, meeting_id: str, max_speakers: int = 10):
        self.meeting_id = meeting_id
        self.max_speakers = max_speakers
        self.speakers: Dict[str, SpeakerProfile] = {}
        self.speaker_counter = 0

    def resolve(self, embedding: np.ndarray, duration_sec: float) -> str:
        """
        Takes an embedding vector and returns the globally consistent speaker label.
        Updates the internal centroid if the match is confident.
        """
        now = datetime.now(timezone.utc)
        
        # 1. If embedding is None or too short, return Unknown
        # We can't trust the embedding, but we might trust a temporal hint
        # For this basic implementation, we just skip updating.
        if embedding is None or duration_sec < MIN_UTTERANCE_LENGTH:
            return "Unknown"

        # Normalize embedding just in case
        embedding = embedding / np.linalg.norm(embedding)

        # 2. Find closest match
        best_match_label = None
        best_similarity = -1.0

        for label, profile in self.speakers.items():
            if profile.centroid is None:
                continue
            
            # Cosine similarity since vectors are normalized
            sim = np.dot(profile.centroid, embedding)
            
            # Check temporal continuity for drift recovery
            # If this speaker spoke recently, we lower the threshold
            time_since_last_speech = (now - profile.last_seen_at).total_seconds()
            effective_threshold = TEMPORAL_DRIFT_THRESHOLD if time_since_last_speech < 30 else MERGE_THRESHOLD
            
            if sim > effective_threshold and sim > best_similarity:
                best_similarity = sim
                best_match_label = label

        # 3. Handle matches vs new speakers
        if best_match_label:
            # We found a match
            profile = self.speakers[best_match_label]
            profile.last_seen_at = now
            profile.total_speaking_seconds += duration_sec
            profile.sample_count += 1
            
            # Update centroid via EMA
            # We delay updates until we have a few samples to avoid initial bad reads
            if profile.sample_count >= MIN_SAMPLES_FOR_UPDATE:
                new_centroid = (1 - EMA_ALPHA) * profile.centroid + EMA_ALPHA * embedding
                profile.centroid = new_centroid / np.linalg.norm(new_centroid)
                
            return best_match_label
            
        else:
            # Create a new speaker profile
            if self.speaker_counter >= self.max_speakers:
                logger.warning(f"Meeting {self.meeting_id} reached max speakers ({self.max_speakers}). Force-assigning to Unknown.")
                return "Unknown"
                
            new_label = f"Speaker_{self.speaker_counter}"
            self.speaker_counter += 1
            
            self.speakers[new_label] = SpeakerProfile(
                label=new_label,
                display_name=None,
                centroid=embedding,
                sample_count=1,
                first_seen_at=now,
                last_seen_at=now,
                total_speaking_seconds=duration_sec,
                is_enrolled=False
            )
            
            logger.info(f"Meeting {self.meeting_id} registered new speaker: {new_label}")
            return new_label
