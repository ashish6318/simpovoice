"""
Response generation module for handling both rule-based and AI-powered responses.
Implements a hybrid approach with fallback mechanisms for production reliability.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from nlu_processor import Intent
from database import (
    get_rooms, get_room_by_type, check_room_availability,
    get_faqs, search_faqs, create_booking
)
from config import config
import json


@dataclass
class ResponseContext:
    """Context for response generation"""
    intent: Intent
    entities: List[Dict]
    user_query: str
    room_data: Optional[List[Dict]] = None


class ResponseGenerator:
    """
    Production-grade response generator with rule-based fallbacks.
    Handles response generation for various intents with business logic.
    """
    
    def __init__(self):
        self.templates = self._initialize_templates()
        self.business_rules = self._initialize_business_rules()
    
    def _initialize_templates(self) -> Dict[Intent, List[str]]:
        """Initialize response templates for rule-based fallback"""
        return {
            Intent.GREETING: [
                "Hi there! 👋 I'm your booking assistant. I can show you rooms, prices, and help you save 15% by booking direct. What are you looking for?",
                "Hello! 🏨 Ready to find your perfect room at the best price? Ask me about our rooms, rates, or availability!",
            ],
            Intent.GOODBYE: [
                "Thanks for chatting! 🙌 Remember, book direct to save 15%. Have a wonderful day!",
                "Goodbye! 👋 Don't forget - direct bookings always get the best price. See you soon!",
            ],
            Intent.HELP: [
                "I can help you with:\n• View rooms & amenities\n• Check prices & compare rates\n• Book rooms directly\n• Answer FAQs\n\nWhat would you like to know?",
            ],
        }
    
    def _initialize_business_rules(self) -> Dict:
        """Initialize business logic rules from configuration"""
        return {
            'direct_discount_percentage': config.business.direct_discount_percentage,
            'min_confidence_threshold': config.business.min_confidence_threshold,
            'price_format': f'{config.business.currency_symbol}{{:,.0f}}',
            'savings_highlight': True,
        }
    
    def generate_response(self, context: ResponseContext) -> str:
        """
        Generate appropriate response based on context.
        Uses rule-based approach as primary method.
        
        Args:
            context: ResponseContext with intent, entities, and data
            
        Returns:
            Generated response string
        """
        # Route to appropriate handler based on intent
        handler_map = {
            Intent.GREETING: self._handle_greeting,
            Intent.GOODBYE: self._handle_goodbye,
            Intent.HELP: self._handle_help,
            Intent.QUERY_ROOMS: self._handle_room_query,
            Intent.QUERY_PRICES: self._handle_price_query,
            Intent.CHECK_AVAILABILITY: self._handle_availability,
            Intent.COMPARE_RATES: self._handle_rate_comparison,
            Intent.BOOK_ROOM: self._handle_booking,
        }
        
        handler = handler_map.get(context.intent, self._handle_unknown)
        return handler(context)
    
    def _handle_greeting(self, context: ResponseContext) -> str:
        """Handle greeting intent"""
        return self.templates[Intent.GREETING][0]
    
    def _handle_goodbye(self, context: ResponseContext) -> str:
        """Handle goodbye intent"""
        return self.templates[Intent.GOODBYE][0]
    
    def _handle_help(self, context: ResponseContext) -> str:
        """Handle help intent with FAQs"""
        # Check if user is asking about specific topic
        query_lower = context.user_query.lower()
        
        # Try to find relevant FAQ with more comprehensive keywords
        faq_keywords = {
            'check-in': ['check-in', 'check in', 'checkin', 'check out', 'checkout', 'time', 'hour'],
            'WiFi': ['wifi', 'internet', 'wi-fi', 'password', 'network'],
            'cancellation': ['cancel', 'cancellation', 'refund'],
            'parking': ['parking', 'park', 'vehicle', 'car'],
            'breakfast': ['breakfast', 'food', 'meal', 'dining'],
            'payment': ['payment', 'pay', 'credit', 'cash', 'card'],
            'pets': ['pet', 'pets', 'dog', 'cat', 'animal'],
            'airport': ['airport', 'pickup', 'transport', 'shuttle']
        }
        
        faqs = []
        for search_term, keywords in faq_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                faqs = search_faqs(search_term)
                if faqs:
                    break
        
        if faqs:
            # Return specific FAQ answer
            faq = faqs[0]
            return f"**{faq['question']}**\n\n{faq['answer']}\n\nNeed help with something else?"
        
        # Return general help
        return self.templates[Intent.HELP][0]
    
    def _handle_room_query(self, context: ResponseContext) -> str:
        """Handle room query with actual data"""
        if not context.room_data:
            context.room_data = get_rooms()
        
        if not context.room_data:
            return "I apologize, but we don't have any rooms available at the moment. Please check back later."
        
        # Filter by room type if entity exists
        room_type_entities = [e for e in context.entities if e['type'] == 'room_type']
        if room_type_entities:
            room_type = room_type_entities[0]['value']
            context.room_data = [r for r in context.room_data if room_type.lower() in r['name'].lower()]
        
        if len(context.room_data) == 1:
            # Single room response - more conversational
            room = context.room_data[0]
            savings = room['rack_rate'] - room['direct_rate']
            return (
                f"Great choice! Our **{room['name']}** is available ({room['inventory']} rooms left).\n\n"
                f"💰 **Pricing:** OTA sites charge {self._format_price(room['rack_rate'])}/night, "
                f"but book direct for just {self._format_price(room['direct_rate'])} - save {self._format_price(savings)}!\n\n"
                f"Ready to book?"
            )
        
        # Multiple rooms - show comparison
        response = f"We have {len(context.room_data)} room types available:\n\n"
        for room in context.room_data:
            savings = room['rack_rate'] - room['direct_rate']
            response += f"**{room['name']}** - {self._format_price(room['direct_rate'])}/night "
            response += f"(save {self._format_price(savings)}!) • {room['inventory']} available\n"
        
        response += f"\n✨ *All prices are 15% off OTA rates when you book direct!*"
        return response
    
    def _handle_price_query(self, context: ResponseContext) -> str:
        """Handle price queries"""
        if not context.room_data:
            context.room_data = get_rooms()
        
        # Check for specific room type
        room_type_entities = [e for e in context.entities if e['type'] == 'room_type']
        
        if room_type_entities:
            room_type = room_type_entities[0]['value']
            matching_rooms = [r for r in context.room_data if room_type.lower() in r['name'].lower()]
            
            if matching_rooms:
                room = matching_rooms[0]
                savings = room['rack_rate'] - room['direct_rate']
                return (
                    f"**{room['name']} Pricing:**\n\n"
                    f"🏷️ OTA Platforms: {self._format_price(room['rack_rate'])}\n"
                    f"✨ Direct Booking: {self._format_price(room['direct_rate'])}\n\n"
                    f"💰 **You save {self._format_price(savings)}** by booking directly!\n\n"
                    f"That's a {self.business_rules['direct_discount_percentage']}% discount compared to Booking.com, Expedia, etc."
                )
        
        # Show all prices in a clean format
        response = "**Direct Booking Prices** (15% off OTA rates):\n\n"
        for room in context.room_data:
            savings = room['rack_rate'] - room['direct_rate']
            response += f"• **{room['name']}:** {self._format_price(room['direct_rate'])}/night "
            response += f"*(save {self._format_price(savings)})*\n"
        
        response += f"\n💡 These are direct booking prices - all 15% cheaper than Booking.com/MakeMyTrip!"
        return response
    
    def _handle_availability(self, context: ResponseContext) -> str:
        """Handle availability checks"""
        if not context.room_data:
            context.room_data = get_rooms()
        
        room_type_entities = [e for e in context.entities if e['type'] == 'room_type']
        
        if room_type_entities:
            room_type = room_type_entities[0]['value']
            matching_rooms = [r for r in context.room_data if room_type.lower() in r['name'].lower()]
            
            if matching_rooms:
                room = matching_rooms[0]
                if room['inventory'] > 0:
                    return (
                        f"Yes! We have **{room['inventory']} {room['name']}(s)** available.\n\n"
                        f"Direct booking rate: {self._format_price(room['direct_rate'])}\n"
                        f"(Save {self._format_price(room['savings'])} vs OTA platforms)\n\n"
                        f"Would you like to proceed with booking?"
                    )
                else:
                    return f"Sorry, {room['name']} is currently sold out. Can I suggest another room type?"
        
        # General availability
        available = [r for r in context.room_data if r['inventory'] > 0]
        if available:
            response = f"We have {len(available)} room types available:\n\n"
            for room in available:
                response += f"- {room['name']}: {room['inventory']} rooms at {self._format_price(room['direct_rate'])}\n"
            response += "\n💡 Book directly to save 15%!"
            return response
        else:
            return "Unfortunately, we're fully booked at the moment. Would you like me to check alternative dates?"
    
    def _handle_rate_comparison(self, context: ResponseContext) -> str:
        """Handle rate comparison requests"""
        if not context.room_data:
            context.room_data = get_rooms()
        
        response = "**Direct Booking vs OTA Platforms:**\n\n"
        response += "Here's how much you save by booking directly:\n\n"
        
        total_ota = sum(r['rack_rate'] for r in context.room_data)
        total_direct = sum(r['direct_rate'] for r in context.room_data)
        total_savings = total_ota - total_direct
        
        for room in context.room_data:
            savings = room['rack_rate'] - room['direct_rate']
            response += f"**{room['name']}:**\n"
            response += f"- Booking.com/Expedia: {self._format_price(room['rack_rate'])}\n"
            response += f"- Our Direct Rate: {self._format_price(room['direct_rate'])}\n"
            response += f"- Your Savings: {self._format_price(savings)}\n\n"
        
        response += (
            f"🎯 **Bottom Line:** By booking directly, you avoid OTA commissions "
            f"and get {self.business_rules['direct_discount_percentage']}% off!\n\n"
            f"No hidden fees. No middleman. Just better prices."
        )
        
        return response
    
    def _handle_booking(self, context: ResponseContext) -> str:
        """Handle booking requests"""
        room_type_entities = [e for e in context.entities if e['type'] == 'room_type']
        
        if room_type_entities:
            # User specified room type
            room_type = room_type_entities[0]['value']
            if not context.room_data:
                context.room_data = get_rooms()
            
            matching_rooms = [r for r in context.room_data if room_type.lower() in r['name'].lower()]
            if matching_rooms:
                room = matching_rooms[0]
                savings = room['rack_rate'] - room['direct_rate']
                return (
                    f"Perfect! Let me help you book the **{room['name']}**.\n\n"
                    f"📞 **Call us at: +91-XXXX-XXXX** (24/7 booking line)\n"
                    f"💻 **Or book online at: www.simplotel.com/direct-booking**\n\n"
                    f"💰 **Your Price:** {self._format_price(room['direct_rate'])}/night (save {self._format_price(savings)}!)\n"
                    f"✅ **Mention code:** DIRECT15 to confirm your discount\n\n"
                    f"Ready to book now? Just call or visit our website!"
                )
        
        # No specific room mentioned - show options
        if not context.room_data:
            context.room_data = get_rooms()
        
        # Build room list
        room_list = "\n".join([
            f"• **{r['name']}** - {self._format_price(r['direct_rate'])}/night ({r['inventory']} available)"
            for r in context.room_data
        ])
        
        return (
            f"Absolutely! I'd be happy to help you book directly and save 15%! 🎉\n\n"
            f"**Available rooms:**\n{room_list}\n\n"
            f"📞 **Book now:** Call +91-XXXX-XXXX or visit www.simplotel.com\n"
            f"💰 **Use code DIRECT15** for your 15% discount!\n\n"
            f"Which room type interests you?"
        )
    
    def _handle_unknown(self, context: ResponseContext) -> str:
        """Handle unknown intents"""
        return (
            "I'm not sure I understood that correctly. I can help you with:\n\n"
            "- Viewing available rooms and prices\n"
            "- Comparing direct booking vs OTA rates\n"
            "- Checking room availability\n"
            "- Making reservations\n\n"
            "What would you like to know?"
        )
    
    def _format_price(self, price: float) -> str:
        """Format price according to business rules"""
        return self.business_rules['price_format'].format(price)
    
    def build_context_prompt(self, intent: Intent, entities: List[Dict]) -> str:
        """
        Build context-aware prompt for AI model.
        Used when AI generation is preferred over rule-based.
        
        Args:
            intent: Detected intent
            entities: Extracted entities
            
        Returns:
            Enhanced system prompt with context
        """
        base_prompt = (
            "You are a quick, helpful hotel booking assistant. Keep responses SHORT (1-3 sentences) and NATURAL.\n\n"
            "RULES:\n"
            "- Show room name, key feature, and BOTH prices (OTA vs Direct)\n"
            "- Direct booking is 15% cheaper - mention the ₹ saved\n"
            "- Be friendly and conversational, not robotic\n"
            "- Don't repeat yourself or over-explain\n\n"
            "Example: \"Our Deluxe Room has a king bed and city view. OTA price: ₹3,000/night. Book direct: ₹2,550 (save ₹450!). Want to book?\""
        )
        
        # Add intent-specific guidance
        intent_guidance = {
            Intent.QUERY_ROOMS: "\n\nUser wants to see available rooms. List all rooms with names, key features, and BOTH prices with savings.",
            Intent.QUERY_PRICES: "\n\nUser asking about prices. Show BOTH Rack Rate and Direct Rate with exact savings amount.",
            Intent.COMPARE_RATES: "\n\nUser comparing prices. Show side-by-side comparison with OTA vs Direct rates and total savings.",
            Intent.CHECK_AVAILABILITY: "\n\nUser checking availability. Confirm available rooms with prices and offer to book.",
            Intent.BOOK_ROOM: "\n\nUser wants to book. Ask for: room type (if not mentioned), dates, guest name. Confirm the direct booking savings.",
            Intent.GREETING: "\n\nGreet warmly and briefly mention you can help with rooms, prices, and bookings.",
            Intent.HELP: "\n\nList what you can help with: view rooms, check prices, compare rates, make bookings. Ask what they need."
        }
        
        if intent in intent_guidance:
            base_prompt += intent_guidance[intent]
        
        # Add entity context
        room_entities = [e for e in entities if e['type'] == 'room_type']
        if room_entities:
            rooms = ", ".join([e['value'] for e in room_entities])
            base_prompt += f"\n\nUser mentioned room type: {rooms}. Focus on this room."
        
        return base_prompt


# Singleton instance
_response_generator = None

def get_response_generator() -> ResponseGenerator:
    """Get singleton response generator instance"""
    global _response_generator
    if _response_generator is None:
        _response_generator = ResponseGenerator()
    return _response_generator
