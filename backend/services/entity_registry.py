import re
from typing import Set

class EntityRegistry:
    """
    A lightweight entity registry for an internship project.
    Instead of complex NER models or vector databases, this uses a fast regex 
    to track Title Cased words (likely names, systems, companies) that are 
    mentioned in the meeting to help the LLM resolve context.
    """
    
    def __init__(self):
        self._entities: Set[str] = set()
        
        # Stopwords to filter out common Title Cased words at start of sentences
        self._stopwords = {
            "I", "We", "They", "He", "She", "It", "The", "A", "An", "And", 
            "But", "Or", "So", "If", "Then", "Yes", "No", "Okay", "Right", 
            "Well", "Like", "Just", "Can", "Could", "Would", "Should", "Is", 
            "Are", "Was", "Were", "This", "That", "These", "Those", "Here", "There"
        }

    def process_text(self, text: str):
        """Extracts simple entities (Consecutive Title Case words) and stores them."""
        if not text:
            return
            
        # Matches one or more Title Cased words (e.g., "Rahul Singh", "Payment API")
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        matches = re.findall(pattern, text)
        
        for match in matches:
            match = match.strip()
            if match and match not in self._stopwords:
                self._entities.add(match)
                
    def get_all(self) -> list[str]:
        """Returns the list of known entities."""
        return sorted(list(self._entities))
