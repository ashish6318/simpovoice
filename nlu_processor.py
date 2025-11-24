"""
Natural Language Understanding module for intent recognition and entity extraction.
Processes user queries to identify intents and extract relevant entities.
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class Intent(Enum):
    """Supported user intents"""
    QUERY_ROOMS = "query_rooms"
    QUERY_PRICES = "query_prices"
    CHECK_AVAILABILITY = "check_availability"
    COMPARE_RATES = "compare_rates"
    BOOK_ROOM = "book_room"
    GREETING = "greeting"
    GOODBYE = "goodbye"
    HELP = "help"
    UNKNOWN = "unknown"

class RoomType(Enum):
    """Room type entities"""
    DELUXE = "deluxe"
    SUITE = "suite"
    STANDARD = "standard"
    ANY = "any"

@dataclass
class Entity:
    """Extracted entity from user query"""
    type: str
    value: str
    confidence: float

@dataclass
class NLUResult:
    """Result of NLU processing"""
    intent: Intent
    confidence: float
    entities: List[Entity]
    original_text: str

class NLUProcessor:
    """
    Natural Language Understanding processor for intent recognition
    and entity extraction without external API dependencies.
    """
    
    def __init__(self):
        self.intent_patterns = self._initialize_intent_patterns()
        self.entity_patterns = self._initialize_entity_patterns()
    
    def _initialize_intent_patterns(self) -> Dict[Intent, List[str]]:
        """Define regex patterns for intent recognition - Trained for hotel booking domain"""
        return {
            Intent.GREETING: [
                r'\b(hello|hi|hey|greetings|good\s+(morning|afternoon|evening)|hola|namaste)\b',
                r'^(hi|hello|hey)[\s\!]*$',
            ],
            Intent.GOODBYE: [
                r'\b(bye|goodbye|see\s+you|take\s+care|have\s+a\s+good|thank\s*you|thanks|thnx|cheers)\b',
                r'\b(bye|cya|see\s+ya|later|thank)\b',
            ],
            Intent.QUERY_ROOMS: [
                # Common room queries
                r'\b(what|which|show|list|tell|display).*(rooms?|types?|options?|accommodations?)\b',
                r'\b(available|have).*(rooms?|suites?|accommodations?)\b',
                r'\brooms?\s+(available|do\s+you\s+have|types?)\b',
                r'\b(can\s+you\s+)?(show|tell|describe).*(rooms?|options?)\b',
                # Natural variations
                r'\b(i\s+want\s+to\s+see|looking\s+for).*(rooms?|options?)\b',
                r'\b(what\s+kind|what\s+types?).*(rooms?|accommodations?)\b',
            ],
            Intent.QUERY_PRICES: [
                # Price-related queries
                r'\b(what|how\s+much|tell\s+me).*(price|cost|rate|charge|tariff|fee)\b',
                r'\b(price|cost|rate|charge|tariff).*(room|deluxe|suite|standard|night)\b',
                r'\bhow\s+much\s+(is|are|does|do|for|per)\b',
                r'\b(what\'?s|what\s+is).*(price|cost|rate)\b',
                # Natural variations
                r'\b(how\s+expensive|how\s+costly|pricing|rates?)\b',
                r'\b(can\s+you\s+tell).*(price|cost|rate)\b',
            ],
            Intent.CHECK_AVAILABILITY: [
                # Availability checks
                r'\b(available|availability|vacant|free|open).*(room|tonight|today|tomorrow)\b',
                r'\bdo\s+you\s+have\s+(any\s+)?(rooms?|deluxe|suite|standard|vacancy)\b',
                r'\b(is|are).*(room|deluxe|suite|standard).*(available|vacant|free|open)\b',
                r'\b(any|got).*(rooms?|vacancies|availability).*(available|free|left)\b',
                # Natural variations
                r'\b(can\s+i\s+get|looking\s+for).*(room|vacancy)\b',
            ],
            Intent.COMPARE_RATES: [
                # Comparison queries
                r'\b(difference|compare|comparison|vs|versus).*(rate|price|cost)\b',
                r'\b(direct|booking\.com|ota|online|makemytrip|agoda).*(rate|price|booking|vs)\b',
                r'\b(cheaper|discount|save|saving|deal|offer)\b',
                r'\b(why\s+)?(book\s+direct|direct\s+booking)\b',
                # Natural variations
                r'\b(better\s+deal|best\s+price|lowest\s+rate)\b',
            ],
            Intent.BOOK_ROOM: [
                # Booking intent
                r'\b(book|reserve|reservation|make\s+a\s+booking)\b',
                r'\bi\s+want\s+(to\s+book|to\s+reserve|a\s+room)\b',
                r'\b(can\s+i|how\s+to|how\s+do\s+i).*(book|reserve)\b',
                r'\b(direct\s+book|book\s+direct|book\s+from\s+here)\b',
                # Natural variations
                r'\b(need\s+a\s+room|want\s+a\s+room|get\s+a\s+room)\b',
                r'\b(proceed|go\s+ahead).*(booking|reservation)\b',
            ],
            Intent.HELP: [
                r'\b(help|assist|support)\b',
                r'\b(what|when|where|how).*(check[ -]?in|check[ -]?out|time|hour)\b',
                r'\b(wifi|internet|wi[ -]?fi|password)\b',
                r'\b(parking|park)\b',
                r'\b(breakfast|food|meal|dining)\b',
                r'\b(cancel|cancellation|refund)\b',
                r'\b(payment|pay|credit|cash)\b',
                r'\b(pet|pets|dog|cat|animal)\b',
                r'\b(allow|accept|permit)\b',
                r'\b(do you (have|offer|provide)|is there|can i|are.*allowed)\b',
                r'\b(policy|policies|rule|rules)\b',
                r'\b(pickup|airport|transport)\b',
            ],
        }
    
    def _initialize_entity_patterns(self) -> Dict[str, List[Tuple[str, str]]]:
        """Define patterns for entity extraction - Hotel-specific entities"""
        return {
            'room_type': [
                # Exact matches
                (r'\bdeluxe\s+room\b', 'deluxe'),
                (r'\bdeluxe\b', 'deluxe'),
                (r'\bsuite\s+room\b', 'suite'),
                (r'\bsuite\b', 'suite'),
                (r'\bstandard\s+room\b', 'standard'),
                (r'\bstandard\b', 'standard'),
                (r'\bexecutive\s+room\b', 'executive'),
                (r'\bexecutive\b', 'executive'),
                # Natural variations
                (r'\bluxury\s+room\b', 'deluxe'),
                (r'\bpremium\s+room\b', 'deluxe'),
                (r'\bbasic\s+room\b', 'standard'),
                (r'\bregular\s+room\b', 'standard'),
            ],
            'number': [
                (r'\b(\d+)\b', None),  # Extract numbers
                (r'\b(one|two|three|four|five|six|seven|eight|nine|ten)\b', None),
            ],
            'date': [
                (r'\b(today|tomorrow|tonight)\b', None),
                (r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', None),
            ],
            'booking_source': [
                (r'\b(booking\.com|airbnb|expedia|ota|online)\b', 'ota'),
                (r'\b(direct|directly|website)\b', 'direct'),
            ],
        }
    
    def process(self, text: str) -> NLUResult:
        """
        Process user input to extract intent and entities.
        
        Args:
            text: User input text
            
        Returns:
            NLUResult containing intent, entities, and confidence scores
        """
        text_lower = text.lower().strip()
        
        # Intent recognition
        intent, intent_confidence = self._recognize_intent(text_lower)
        
        # Entity extraction
        entities = self._extract_entities(text_lower)
        
        return NLUResult(
            intent=intent,
            confidence=intent_confidence,
            entities=entities,
            original_text=text
        )
    
    def _recognize_intent(self, text: str) -> Tuple[Intent, float]:
        """
        Recognize user intent from text using pattern matching.
        
        Args:
            text: Preprocessed user input
            
        Returns:
            Tuple of (Intent, confidence_score)
        """
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 1
            
            if score > 0:
                # Calculate confidence based on number of pattern matches
                confidence = min(score / len(patterns), 1.0)
                intent_scores[intent] = confidence
        
        if not intent_scores:
            return Intent.UNKNOWN, 0.0
        
        # Return intent with highest confidence
        best_intent = max(intent_scores, key=intent_scores.get)
        return best_intent, intent_scores[best_intent]
    
    def _extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities from text using pattern matching.
        
        Args:
            text: Preprocessed user input
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern, default_value in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    value = default_value if default_value else match.group(0)
                    entities.append(Entity(
                        type=entity_type,
                        value=value,
                        confidence=0.9  # High confidence for pattern matches
                    ))
        
        return entities
    
    def get_intent_description(self, intent: Intent) -> str:
        """Get human-readable description of intent"""
        descriptions = {
            Intent.QUERY_ROOMS: "User wants to see available rooms",
            Intent.QUERY_PRICES: "User wants to know pricing information",
            Intent.CHECK_AVAILABILITY: "User checking room availability",
            Intent.COMPARE_RATES: "User wants to compare pricing",
            Intent.BOOK_ROOM: "User wants to make a booking",
            Intent.GREETING: "User greeting",
            Intent.GOODBYE: "User ending conversation",
            Intent.HELP: "User needs assistance",
            Intent.UNKNOWN: "Unable to determine user intent",
        }
        return descriptions.get(intent, "Unknown intent")


def analyze_query(text: str) -> Dict:
    """
    Convenience function to analyze a query and return structured results.
    
    Args:
        text: User query text
        
    Returns:
        Dictionary containing intent, entities, and metadata
    """
    processor = NLUProcessor()
    result = processor.process(text)
    
    return {
        'intent': result.intent.value,
        'intent_confidence': result.confidence,
        'entities': [
            {
                'type': e.type,
                'value': e.value,
                'confidence': e.confidence
            }
            for e in result.entities
        ],
        'original_text': result.original_text,
        'description': processor.get_intent_description(result.intent)
    }


if __name__ == "__main__":
    # Test the NLU processor
    test_queries = [
        "What rooms do you have available?",
        "How much is the deluxe room?",
        "Show me the price difference between direct and booking.com",
        "I want to book a suite",
        "Do you have any standard rooms available?",
    ]
    
    processor = NLUProcessor()
    
    print("NLU Processor Test")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = processor.process(query)
        print(f"Intent: {result.intent.value} (confidence: {result.confidence:.2f})")
        print(f"Entities: {[(e.type, e.value) for e in result.entities]}")
        print("-" * 60)
