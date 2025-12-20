from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

chatbot_router = APIRouter(prefix="/chatbot")

# System message for the chatbot
SYSTEM_MESSAGE = """
You are a helpful assistant for TROA (The Retreat Owners Association), a premium residential community.

You can help with:
1. **Amenities Information**: Swimming Pool, Club House, Fitness Center, Sports Courts, Landscaped Gardens, Children's Play Area
2. **Booking Questions**: How to book amenities, booking policies, cancellation
3. **Membership Inquiries**: How to become a member, membership benefits
4. **Committee Information**: Information about the committee members and their roles
5. **Contact Information**: How to reach TROA management
6. **General Community Questions**: Rules, events, facilities

**Important Guidelines:**
- Be friendly, professional, and helpful
- Keep responses concise but informative
- For complex issues or things you cannot answer, suggest contacting TROA via email at troa.systems@gmail.com
- Never make up information - if unsure, direct them to contact TROA
- For booking amenities, users need to login first via Google authentication

**Key Information:**
- Amenities are available from 6 AM to 10 PM
- Bookings can be made for 30 minutes or 1 hour slots
- Landscaped Gardens and Children's Play Area are open to all residents without booking
- For payments (Move-in, Move-out, Membership fees), users should visit the Help Desk or Contact page
- For urgent matters, email: troa.systems@gmail.com
"""

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

# In-memory chat history (for simplicity - in production use database)
chat_histories = {}

@chatbot_router.post("/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    """Handle chatbot messages"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.getenv('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="Chatbot not configured")
        
        # Generate or use existing session ID
        session_id = chat_message.session_id or f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Initialize chat
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=SYSTEM_MESSAGE
        ).with_model("openai", "gpt-4o")
        
        # Create user message
        user_message = UserMessage(text=chat_message.message)
        
        # Get response
        response = await chat.send_message(user_message)
        
        logger.info(f"Chatbot response for session {session_id}: {response[:100]}...")
        
        return ChatResponse(
            response=response,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Chatbot error: {str(e)}")
        # Fallback response
        return ChatResponse(
            response="I apologize, but I'm having trouble processing your request right now. For immediate assistance, please email us at troa.systems@gmail.com.",
            session_id=chat_message.session_id or "error"
        )
