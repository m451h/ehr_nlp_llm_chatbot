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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
from datetime import datetime

from src.search.search_engine import ChatbotSearchHandler
from src.database.vector_db import VectorDatabase
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

# In-memory session store (for production, use Redis or database)
sessions: Dict[str, Dict] = {}

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
def start_chat(request: StartChatRequest):
    """Start a new chat session for a condition"""
    try:
        # Verify condition exists
        conditions = get_available_conditions()
        if request.condition_id not in conditions:
            raise HTTPException(status_code=400, detail=f"Invalid condition_id: {request.condition_id}")
        
        # Create new session
        session_id = str(uuid.uuid4())
        condition_name = conditions[request.condition_id]
        
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
        
        # Initialize session
        sessions[session_id] = {
            'session_id': session_id,
            'current_condition': request.condition_id,
            'condition_name': condition_name,
            'messages': [],
            'stats': {
                'total_queries': 0,
                'high_confidence': 0,
                'medium_confidence': 0,
                'low_confidence': 0
            },
            'clinical_data': clinical_data,
            'educational_note': None,
            'created_at': datetime.now().isoformat()
        }
        
        # Generate educational note if requested
        educational_note = None
        if request.generate_educational_note:
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
                sessions[session_id]['educational_note'] = educational_note
        
        return {
            "success": True,
            "session_id": session_id,
            "condition_id": request.condition_id,
            "condition_name": condition_name,
            "educational_note": educational_note
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start chat: {str(e)}")

@app.post("/api/chat/query")
def query_chat(request: QueryRequest):
    """Send a query to the chatbot"""
    try:
        # Get session
        if request.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[request.session_id]
        handler = get_handler()
        
        # Add user message to session
        user_message = {
            'role': 'user',
            'content': request.query
        }
        session['messages'].append(user_message)
        
        # Get bot response
        response = handler.handle_user_query(
            query=request.query,
            condition_id=session['current_condition']
        )
        
        # Update stats
        session['stats']['total_queries'] += 1
        
        # Handle different response types
        bot_message = None
        confidence = 'medium-confidence'
        
        if response['response_type'] == 'direct_answer':
            bot_message = response['answer']
            confidence = 'high-confidence'
            session['stats']['high_confidence'] += 1
            
            # Add follow-up if available
            if response.get('follow_up'):
                bot_message += f"\n\n🤔 {response['follow_up']}"
        
        elif response['response_type'] == 'clarification':
            bot_message = response['message']
            confidence = 'medium-confidence'
            session['stats']['medium_confidence'] += 1
        
        elif response['response_type'] == 'condition_mismatch':
            bot_message = f"⚠️ {response['message']}\n\n"
            bot_message += f"بیماری تشخیص داده شده: **{response['detected_condition_name']}**\n\n"
            bot_message += response['suggestion']
            confidence = 'medium-confidence'
            session['stats']['medium_confidence'] += 1
        
        elif response['response_type'] == 'llm_fallback':
            # Try LLM fallback
            condition_name = session['condition_name']
            llm_text = call_llm_fallback(
                user_query=request.query,
                condition_name=condition_name,
                clinical_data=session['clinical_data'],
                chat_history=session['messages'],
            )
            if llm_text:
                bot_message = llm_text
                confidence = 'medium-confidence'
                session['stats']['medium_confidence'] += 1
            else:
                bot_message = "❌ متأسفم، جواب دقیقی در اطلاعات موجود پیدا نکردم.\n\n"
                bot_message += "💡 می‌توانید سوال خود را واضح‌تر بپرسید یا از کلمات دیگری استفاده کنید."
                confidence = 'low-confidence'
                session['stats']['low_confidence'] += 1
        
        else:
            bot_message = "❌ خطا در پردازش سوال"
            confidence = 'low-confidence'
        
        # Add bot message to session
        bot_message_obj = {
            'role': 'bot',
            'content': bot_message,
            'confidence_level': confidence
        }
        session['messages'].append(bot_message_obj)
        
        return {
            "success": True,
            "message": bot_message,
            "confidence_level": confidence,
            "response_type": response.get('response_type'),
            "stats": session['stats']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

@app.get("/api/chat/history/{session_id}")
def get_chat_history(session_id: str):
    """Get chat history for a session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return {
        "success": True,
        "session_id": session_id,
        "current_condition": session['current_condition'],
        "condition_name": session['condition_name'],
        "messages": session['messages'],
        "stats": session['stats'],
        "educational_note": session.get('educational_note')
    }

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
def update_clinical_data(request: UpdateClinicalDataRequest):
    """Update clinical data for a session"""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[request.session_id]
    
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
    
    session['clinical_data'] = clinical_data
    
    return {
        "success": True,
        "session_id": request.session_id,
        "clinical_data": clinical_data
    }

@app.get("/api/stats/{session_id}")
def get_stats(session_id: str):
    """Get statistics for a session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "success": True,
        "session_id": session_id,
        "stats": sessions[session_id]['stats']
    }

@app.delete("/api/chat/session/{session_id}")
def delete_session(session_id: str):
    """Delete a chat session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del sessions[session_id]
    return {
        "success": True,
        "message": "Session deleted"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

