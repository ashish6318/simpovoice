"""
AI processing module using Groq's Llama 3 model.
Handles natural language understanding and response generation with tool calling.
Implements hybrid approach: rule-based responses with AI enhancement.
"""

from database import get_rooms, log_query
from nlu_processor import NLUProcessor, Intent
from response_generator import ResponseGenerator, ResponseContext, get_response_generator
from config import config
from groq import Groq
import json
import time
from typing import Optional

# Initialize components based on configuration
if config.ai.use_ai and config.ai.groq_api_key:
    client = Groq(api_key=config.ai.groq_api_key)
else:
    client = None

nlu_processor = NLUProcessor()
response_generator = get_response_generator()

# Define the tool schema for get_rooms function
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_rooms",
            "description": "Get available hotel rooms with pricing information including rack rates (OTA prices) and direct booking rates (15% cheaper)",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

def get_agent_response(user_text: str, use_ai: Optional[bool] = None) -> str:
    """
    Process user query and generate response.
    Uses hybrid approach: rule-based with optional AI enhancement.
    
    Args:
        user_text: User input query
        use_ai: Force AI usage (True) or rule-based (False). None = auto-detect
        
    Returns:
        Generated response string
    """
    start_time = time.time()
    
    # Step 1: NLU Processing - Intent Recognition & Entity Extraction
    nlu_result = nlu_processor.process(user_text)
    
    # Step 2: Get room data if needed
    room_data = None
    if nlu_result.intent in [Intent.QUERY_ROOMS, Intent.QUERY_PRICES, 
                              Intent.CHECK_AVAILABILITY, Intent.COMPARE_RATES]:
        room_data = get_rooms()
    
    # Convert entities to dict format
    entities = [{'type': e.type, 'value': e.value, 'confidence': e.confidence} 
                for e in nlu_result.entities]
    
    # Step 3: Decide between rule-based and AI generation
    # Prefer rule-based to showcase actual development work
    # AI is only used as optional enhancement for complex queries
    should_use_ai = use_ai if use_ai is not None else False  # Disable AI by default to show real logic
    
    # Step 4: Generate response
    if should_use_ai and client:
        response = _generate_ai_response(user_text, nlu_result, room_data, entities)
    else:
        # Use rule-based response generation
        context = ResponseContext(
            intent=nlu_result.intent,
            entities=entities,
            user_query=user_text,
            room_data=room_data
        )
        response = response_generator.generate_response(context)
    
    # Step 5: Log query for analytics
    response_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
    log_query(user_text, nlu_result.intent.value, nlu_result.confidence, response_time)
    
    return response


def _generate_ai_response(user_text: str, nlu_result, room_data, entities: list) -> str:
    """
    Generate response using AI model with tool calling.
    Fallback to rule-based on error.
    """
    try:
        # Build context-aware prompt
        context_prompt = response_generator.build_context_prompt(nlu_result.intent, entities)
        
        messages = [
            {"role": "system", "content": context_prompt},
            {"role": "user", "content": user_text}
        ]
        
        # Add room data context if available
        if room_data:
            data_context = f"\n\nAvailable rooms data: {json.dumps(room_data)}"
            messages[0]["content"] += data_context
        
        # API call to Groq
        response = client.chat.completions.create(
            model=config.ai.model_name,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=config.ai.max_tokens,
            temperature=config.ai.temperature
        )
        
        response_message = response.choices[0].message
        
        # Handle tool calling if needed
        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            
            if tool_call.function.name == "get_rooms":
                rooms_data = get_rooms()
                
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }]
                })
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": json.dumps(rooms_data)
                })
                
                final_response = client.chat.completions.create(
                    model=config.ai.model_name,
                    messages=messages,
                    max_tokens=config.ai.max_tokens,
                    temperature=config.ai.temperature
                )
                
                return final_response.choices[0].message.content
        
        return response_message.content if response_message.content else _fallback_response(nlu_result, entities, room_data)
    
    except Exception as e:
        # Fallback to rule-based on error
        return _fallback_response(nlu_result, entities, room_data)


def _fallback_response(nlu_result, entities: list, room_data) -> str:
    """Fallback to rule-based response on AI failure"""
    context = ResponseContext(
        intent=nlu_result.intent,
        entities=entities,
        user_query=nlu_result.original_text,
        room_data=room_data
    )
    return response_generator.generate_response(context)

if __name__ == "__main__":
    # Test the brain
    test_query = "What rooms do you have available?"
    print(f"User: {test_query}")
    print(f"Agent: {get_agent_response(test_query)}")
