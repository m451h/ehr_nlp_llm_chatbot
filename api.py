"""
FastAPI REST API for EHR Chatbot
Exposes all functionality from app.py as REST endpoints

Usage:
    uvicorn api:app --reload --host 0.0.0.0 --port 8000

For production:
    uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
"""

import sys
sys.path.insert(0, '.')

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
from datetime import datetime

from src.search.search_engine import ChatbotSearchHandler
from src.database.vector_db import VectorDatabase
from src.database.chat_db import ChatDatabase
from src.models.fallback import call_llm_fallback
from src.models.condition_educator import generate_condition_note

# ============================================================================
# INITIALIZE
# ============================================================================

app = FastAPI(
    title="EHR Chatbot API",
    description="REST API for EHR Medical Chatbot",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chatbot handler (singleton)
handler: Optional[ChatbotSearchHandler] = None

def get_handler():
    """Get or initialize chatbot handler"""
    global handler
    if handler is None:
        try:
            handler = ChatbotSearchHandler()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load chatbot: {str(e)}")
    return handler

# Get available conditions from database
def get_available_conditions():
    """Get list of conditions from vector DB"""
    try:
        db = VectorDatabase()
        db.get_collection()
        
        # Get a sample of items to extract unique conditions
        results = db.collection.get(limit=1000)
        
        conditions = {}
        for metadata in results['metadatas']:
            cond_id = metadata.get('condition_id')
            cond_name = metadata.get('condition_name')
            if cond_id and cond_name and cond_id not in conditions:
                conditions[cond_id] = cond_name
        
        return conditions
    except:
        # Fallback conditions
        return {
            "cond_type_2_diabetes": "دیابت نوع ۲",
            "cond_hypertension": "فشار خون بالا",
            "cond_asthma": "آسم"
        }

# Initialize SQLite database for chat history
chat_db = ChatDatabase()

# Default clinical data structure
DEFAULT_CLINICAL_DATA = {
    'سن': '45 سال',
    'جنسیت': 'مرد',
    'وزن': '78 کیلوگرم',
    'قد': '175 سانتی‌متر',
    'فشار خون': '140/90 mmHg',
    'قند خون ناشتا': '95 mg/dL',
    'کلسترول': '220 mg/dL',
    'داروهای فعلی': 'متفورمین 500mg',
    'سابقه بیماری': 'فشار خون بالا'
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_user_id(request: Request, x_user_id: Optional[str] = Header(None)) -> int:
    """
    Extract user_id from request headers.
    The backend should send user_id in the 'X-User-ID' header as a 13-digit integer.
    
    Args:
        request: FastAPI request object
        x_user_id: User ID from X-User-ID header
        
    Returns:
        User ID as integer
        
    Raises:
        HTTPException: If user_id is missing or invalid
    """
    # Try to get from X-User-ID header first
    user_id_str = x_user_id
    
    # If not in header, try to get from request headers directly
    if not user_id_str:
        user_id_str = request.headers.get('X-User-ID') or request.headers.get('x-user-id')
    
    if not user_id_str:
        raise HTTPException(
            status_code=401,
            detail="User ID is required. Please provide X-User-ID header with a 13-digit integer."
        )
    
    try:
        user_id = int(user_id_str)
        # Validate it's a 13-digit integer
        if len(str(user_id)) != 13:
            raise HTTPException(
                status_code=400,
                detail=f"User ID must be a 13-digit integer. Received: {user_id_str}"
            )
        return user_id
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid user ID format. Must be a 13-digit integer. Received: {user_id_str}"
        )

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ChatMessage(BaseModel):
    role: str  # 'user' or 'bot'
    content: str
    confidence_level: Optional[str] = None

class ClinicalData(BaseModel):
    age: Optional[str] = None
    gender: Optional[str] = None
    weight: Optional[str] = None
    height: Optional[str] = None
    blood_pressure: Optional[str] = None
    fasting_blood_sugar: Optional[str] = None
    cholesterol: Optional[str] = None
    current_medications: Optional[str] = None
    medical_history: Optional[str] = None
    # Allow additional fields
    class Config:
        extra = "allow"

class StartChatRequest(BaseModel):
    condition_id: str
    clinical_data: Optional[Dict[str, str]] = None
    generate_educational_note: bool = True

class QueryRequest(BaseModel):
    session_id: str
    query: str

class UpdateClinicalDataRequest(BaseModel):
    session_id: str
    clinical_data: Dict[str, str]

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "EHR Chatbot API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    try:
        get_handler()
        return {"status": "healthy", "chatbot_loaded": True}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/api/conditions")
def get_conditions():
    """Get all available conditions"""
    try:
        conditions = get_available_conditions()
        return {
            "success": True,
            "conditions": conditions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conditions: {str(e)}")

@app.post("/api/chat/start")
def start_chat(request: StartChatRequest, req: Request, x_user_id: Optional[str] = Header(None)):
    """Start a new chat session for a condition"""
    try:
        # Get user_id from headers
        user_id = get_user_id(req, x_user_id)
        
        # Check if condition exists in database
        conditions = get_available_conditions()
        condition_exists = request.condition_id in conditions
        
        # Create new session
        session_id = str(uuid.uuid4())
        
        # Use condition name from database if exists, otherwise use condition_id as name
        if condition_exists:
            condition_name = conditions[request.condition_id]
        else:
            # Convert condition_id to a readable name (remove 'cond_' prefix if present)
            condition_name = request.condition_id.replace('cond_', '').replace('_', ' ')
            # Capitalize first letter of each word
            condition_name = ' '.join(word.capitalize() for word in condition_name.split())
        
        # Use provided clinical data or default
        clinical_data = request.clinical_data or DEFAULT_CLINICAL_DATA
        
        # Convert ClinicalData format to Persian keys if needed
        if clinical_data and not any(key in clinical_data for key in ['سن', 'جنسیت']):
            # Convert English keys to Persian
            persian_data = {}
            key_mapping = {
                'age': 'سن',
                'gender': 'جنسیت',
                'weight': 'وزن',
                'height': 'قد',
                'blood_pressure': 'فشار خون',
                'fasting_blood_sugar': 'قند خون ناشتا',
                'cholesterol': 'کلسترول',
                'current_medications': 'داروهای فعلی',
                'medical_history': 'سابقه بیماری'
            }
            for eng_key, persian_key in key_mapping.items():
                if eng_key in clinical_data:
                    persian_data[persian_key] = clinical_data[eng_key]
            # Add any extra fields
            for key, value in clinical_data.items():
                if key not in key_mapping:
                    persian_data[key] = value
            clinical_data = persian_data
        
        # Generate educational note
        # For unknown conditions, ALWAYS generate educational note with patient JSON data
        # For known conditions, generate if requested
        educational_note = None
        if not condition_exists or request.generate_educational_note:
            note = generate_condition_note(
                condition_name=condition_name,
                clinical_data=clinical_data
            )
            if note:
                educational_note = {
                    'condition': request.condition_id,
                    'condition_name': condition_name,
                    'note': note
                }
        
        # Create session in database with user_id
        chat_db.create_session(
            session_id=session_id,
            user_id=user_id,
            condition_id=request.condition_id,
            condition_name=condition_name,
            clinical_data=clinical_data,
            educational_note=educational_note
        )

        # Store educational note as the first bot message for session history
        if educational_note and educational_note.get('note'):
            chat_db.add_message(
                session_id=session_id,
                role='bot',
                content=educational_note['note'],
                confidence_level='educational-note'
            )
 
        return {
            "success": True,
            "session_id": session_id,
            "condition_id": request.condition_id,
            "condition_name": condition_name,
            "educational_note": educational_note,
            "condition_in_database": condition_exists
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start chat: {str(e)}")

@app.post("/api/chat/query")
def query_chat(request: QueryRequest, req: Request, x_user_id: Optional[str] = Header(None)):
    """Send a query to the chatbot"""
    try:
        # Get user_id from headers
        user_id = get_user_id(req, x_user_id)
        
        # Get session from database (validates user ownership)
        session = chat_db.get_session(request.session_id, user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or access denied")
        
        # Add user message to database
        chat_db.add_message(
            session_id=request.session_id,
            role='user',
            content=request.query
        )
        
        # Get chat history for LLM fallback
        chat_history = chat_db.get_messages(request.session_id)
        
        # Check if condition exists in database
        conditions = get_available_conditions()
        condition_exists = session['condition_id'] in conditions
        
        # Update stats
        stats = session['stats'].copy()
        stats['total_queries'] += 1
        
        # If condition is not in database, use fallback directly
        if not condition_exists:
            # Use LLM fallback directly for unknown conditions
            condition_name = session['condition_name']
            llm_text = call_llm_fallback(
                user_query=request.query,
                condition_name=condition_name,
                clinical_data=session['clinical_data'],
                chat_history=chat_history,
            )
            if llm_text:
                bot_message = llm_text
                confidence = 'medium-confidence'
                stats['medium_confidence'] += 1
            else:
                bot_message = "❌ متأسفم، جواب دقیقی در اطلاعات موجود پیدا نکردم.\n\n"
                bot_message += "💡 می‌توانید سوال خود را واضح‌تر بپرسید یا از کلمات دیگری استفاده کنید."
                confidence = 'low-confidence'
                stats['low_confidence'] += 1
            
            # Add bot message to database
            chat_db.add_message(
                session_id=request.session_id,
                role='bot',
                content=bot_message,
                confidence_level=confidence
            )
            
            # Update stats in database
            chat_db.update_session_stats(request.session_id, user_id, stats)
            
            return {
                "success": True,
                "message": bot_message,
                "confidence_level": confidence,
                "response_type": "llm_fallback",
                "stats": stats
            }
        
        # Condition exists in database - use NLP only if confidence > 0.89
        handler = get_handler()
        response = handler.handle_user_query(
            query=request.query,
            condition_id=session['condition_id']
        )

        bot_message = None
        confidence = 'medium-confidence'
        response_type = 'llm_fallback'

        # Determine whether to trust the knowledge base answer
        kb_confidence = response.get('confidence', 0)
        use_direct_answer = (
            response.get('response_type') == 'direct_answer' and
            isinstance(kb_confidence, (int, float)) and
            kb_confidence >= 0.89
        )

        if use_direct_answer:
            bot_message = response['answer']
            confidence = 'high-confidence'
            response_type = 'direct_answer'
            stats['high_confidence'] += 1

            if response.get('follow_up'):
                bot_message += f"\n\n🤔 {response['follow_up']}"
        else:
            # Build optional context from retrieval result
            fallback_context = ""
            if response.get('response_type') == 'condition_mismatch':
                fallback_context = (
                    f"⚠️ {response['message']}\n\n"
                    f"بیماری تشخیص داده شده: **{response['detected_condition_name']}**\n\n"
                )
            elif response.get('response_type') == 'clarification':
                fallback_context = response.get('message', '') + "\n\n"

            condition_name = session['condition_name']
            llm_text = call_llm_fallback(
                user_query=request.query,
                condition_name=condition_name,
                clinical_data=session['clinical_data'],
                chat_history=chat_history,
            )

            if llm_text:
                bot_message = f"{fallback_context}{llm_text}" if fallback_context else llm_text
                confidence = 'medium-confidence'
                stats['medium_confidence'] += 1
            else:
                bot_message = (
                    "❌ متأسفم، جواب دقیقی در اطلاعات موجود پیدا نکردم.\n\n"
                    "💡 می‌توانید سوال خود را واضح‌تر بپرسید یا از کلمات دیگری استفاده کنید."
                )
                confidence = 'low-confidence'
                stats['low_confidence'] += 1
 
        # Add bot message to database
        chat_db.add_message(
            session_id=request.session_id,
            role='bot',
            content=bot_message,
            confidence_level=confidence
        )
        
        # Update stats in database
        chat_db.update_session_stats(request.session_id, user_id, stats)
        
        return {
            "success": True,
            "message": bot_message,
            "confidence_level": confidence,
            "response_type": response_type,
            "stats": stats
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

@app.get("/api/chat/history/{session_id}")
def get_chat_history(session_id: str, req: Request, x_user_id: Optional[str] = Header(None)):
    """Get chat history for a session"""
    # Get user_id from headers
    user_id = get_user_id(req, x_user_id)
    
    session = chat_db.get_full_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or access denied")
    
    return {
        "success": True,
        "session_id": session_id,
        "current_condition": session['condition_id'],
        "condition_name": session['condition_name'],
        "messages": session['messages'],
        "stats": session['stats'],
        "educational_note": session.get('educational_note')
    }

@app.get("/api/chat/sessions")
def list_all_sessions(req: Request, x_user_id: Optional[str] = Header(None)):
    """Get list of all chat sessions for the current user (for sidebar/history display)"""
    try:
        # Get user_id from headers
        user_id = get_user_id(req, x_user_id)
        
        session_list = chat_db.list_all_sessions(user_id)
        
        return {
            "success": True,
            "sessions": session_list,
            "total": len(session_list)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

@app.post("/api/chat/educational-note")
def generate_educational_note(request: StartChatRequest):
    """Generate educational note for a condition"""
    try:
        conditions = get_available_conditions()
        if request.condition_id not in conditions:
            raise HTTPException(status_code=400, detail=f"Invalid condition_id: {request.condition_id}")
        
        condition_name = conditions[request.condition_id]
        clinical_data = request.clinical_data or DEFAULT_CLINICAL_DATA
        
        # Convert to Persian keys if needed
        if clinical_data and not any(key in clinical_data for key in ['سن', 'جنسیت']):
            persian_data = {}
            key_mapping = {
                'age': 'سن',
                'gender': 'جنسیت',
                'weight': 'وزن',
                'height': 'قد',
                'blood_pressure': 'فشار خون',
                'fasting_blood_sugar': 'قند خون ناشتا',
                'cholesterol': 'کلسترول',
                'current_medications': 'داروهای فعلی',
                'medical_history': 'سابقه بیماری'
            }
            for eng_key, persian_key in key_mapping.items():
                if eng_key in clinical_data:
                    persian_data[persian_key] = clinical_data[eng_key]
            for key, value in clinical_data.items():
                if key not in key_mapping:
                    persian_data[key] = value
            clinical_data = persian_data
        
        note = generate_condition_note(
            condition_name=condition_name,
            clinical_data=clinical_data
        )
        
        if not note:
            raise HTTPException(status_code=500, detail="Failed to generate educational note")
        
        return {
            "success": True,
            "condition_id": request.condition_id,
            "condition_name": condition_name,
            "note": note
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate educational note: {str(e)}")

@app.post("/api/chat/update-clinical-data")
def update_clinical_data(request: UpdateClinicalDataRequest, req: Request, x_user_id: Optional[str] = Header(None)):
    """Update clinical data for a session"""
    # Get user_id from headers
    user_id = get_user_id(req, x_user_id)
    
    # Verify session exists and belongs to user
    session = chat_db.get_session(request.session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or access denied")
    
    # Convert to Persian keys if needed
    clinical_data = request.clinical_data
    if clinical_data and not any(key in clinical_data for key in ['سن', 'جنسیت']):
        persian_data = {}
        key_mapping = {
            'age': 'سن',
            'gender': 'جنسیت',
            'weight': 'وزن',
            'height': 'قد',
            'blood_pressure': 'فشار خون',
            'fasting_blood_sugar': 'قند خون ناشتا',
            'cholesterol': 'کلسترول',
            'current_medications': 'داروهای فعلی',
            'medical_history': 'سابقه بیماری'
        }
        for eng_key, persian_key in key_mapping.items():
            if eng_key in clinical_data:
                persian_data[persian_key] = clinical_data[eng_key]
        for key, value in clinical_data.items():
            if key not in key_mapping:
                persian_data[key] = value
        clinical_data = persian_data
    
    # Update clinical data in database
    chat_db.update_session_clinical_data(request.session_id, user_id, clinical_data)
    
    return {
        "success": True,
        "session_id": request.session_id,
        "clinical_data": clinical_data
    }

@app.get("/api/stats/{session_id}")
def get_stats(session_id: str, req: Request, x_user_id: Optional[str] = Header(None)):
    """Get statistics for a session"""
    # Get user_id from headers
    user_id = get_user_id(req, x_user_id)
    
    session = chat_db.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or access denied")
    
    return {
        "success": True,
        "session_id": session_id,
        "stats": session['stats']
    }

@app.delete("/api/chat/session/{session_id}")
def delete_session(session_id: str, req: Request, x_user_id: Optional[str] = Header(None)):
    """Delete a chat session"""
    # Get user_id from headers
    user_id = get_user_id(req, x_user_id)
    
    deleted = chat_db.delete_session(session_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found or access denied")
    
    return {
        "success": True,
        "message": "Session deleted"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

