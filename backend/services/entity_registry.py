import re
from typing import Set

class EntityRegistry:
    """
    A lightweight entity registry that tracks names, systems, companies, and
    technical terms mentioned in the meeting to help the LLM resolve context.
    Detects Title Case multi-word phrases, ALL-CAPS acronyms, and camelCase identifiers.
    """

    def __init__(self):
        self._entities: Set[str] = set()

        self._stopwords = {
            "I", "We", "They", "He", "She", "It", "The", "A", "An", "And",
            "But", "Or", "So", "If", "Then", "Yes", "No", "Okay", "Right",
            "Well", "Like", "Just", "Can", "Could", "Would", "Should", "Is",
            "Are", "Was", "Were", "This", "That", "These", "Those", "Here", "There",
            # Common acronyms that aren't meaningful entities
            "OK", "ID", "UI", "UX", "PM",
        }

        # Title Case: one or more consecutive Title-cased words (e.g. "Rahul Singh", "Payment API")
        self._title_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')
        # ALL-CAPS acronyms: 2+ uppercase letters, optionally followed by digits (e.g. AWS, JWT, API, NVIDIA, S3)
        self._acronym_pattern = re.compile(r'\b[A-Z]{2,}[0-9]*\b')
        # camelCase identifiers: starts lowercase, has at least one uppercase interior letter (e.g. iPhone, FastAPI, PostgreSQL)
        self._camel_pattern = re.compile(r'\b[a-z]+[A-Z][a-zA-Z0-9]*\b')

    def process_text(self, text: str):
        """Extracts entities from text and stores them."""
        if not text:
            return

        for match in self._title_pattern.findall(text):
            match = match.strip()
            if match and match not in self._stopwords:
                self._entities.add(match)

        for match in self._acronym_pattern.findall(text):
            if match not in self._stopwords:
                self._entities.add(match)

        for match in self._camel_pattern.findall(text):
            self._entities.add(match)

    def get_all(self) -> list[str]:
        """Returns the list of known entities."""
        return sorted(list(self._entities))
