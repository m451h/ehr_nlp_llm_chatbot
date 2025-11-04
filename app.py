"""
Simple Streamlit Demo for EHR Chatbot
For PM Testing - No code visible, just chat interface

Setup:
1. pip install streamlit
2. streamlit run demo_app.py

Or add to requirements.txt:
streamlit>=1.28.0
"""

import streamlit as st
import sys
sys.path.insert(0, '.')

from src.search.search_engine import ChatbotSearchHandler
from src.database.vector_db import VectorDatabase
from src.models.fallback import call_llm_fallback
from src.models.condition_educator import generate_condition_note

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="چت‌بات سلامت",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better Persian support and styling
st.markdown("""
<style>
    .stApp {
        direction: rtl;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #000000;
        align-items: flex-start;
    }
    .bot-message {
        background-color: #000000;
        align-items: flex-start;
    }
    .confidence-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        font-weight: bold;
        margin-top: 0.5rem;
    }
    .high-confidence {
        background-color: #4caf50;
        color: white;
    }
    .medium-confidence {
        background-color: #ff9800;
        color: white;
    }
    .low-confidence {
        background-color: #f44336;
        color: white;
    }
    h1, h2, h3 {
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# INITIALIZE
# ============================================================================

@st.cache_resource
def load_chatbot():
    """Load chatbot (cached so it only loads once)"""
    try:
        handler = ChatbotSearchHandler()
        return handler, None
    except Exception as e:
        return None, str(e)

# Load chatbot
with st.spinner('🔄 در حال بارگذاری چت‌بات...'):
    handler, error = load_chatbot()

if error:
    st.error(f"❌ خطا در بارگذاری چت‌بات: {error}")
    st.info("💡 لطفا ابتدا دیتابیس را بسازید:\npython scripts/01_build_index.py build")
    st.stop()

# Get available conditions from database
@st.cache_data
def get_available_conditions():
    """Get list of conditions from vector DB"""
    try:
        db = VectorDatabase()
        db.get_collection()
        
        # Get a sample of items to extract unique conditions
        # This is a workaround - ideally you'd have a separate conditions table
        results = db.collection.get(limit=1000)
        
        conditions = {}
        for metadata in results['metadatas']:
            cond_id = metadata.get('condition_id')
            cond_name = metadata.get('condition_name')
            if cond_id and cond_name and cond_id not in conditions:
                conditions[cond_id] = cond_name
        
        return conditions
    except:
        return {
            "cond_type_2_diabetes": "دیابت نوع ۲",
            "cond_hypertension": "فشار خون بالا",
            "cond_asthma": "آسم"
        }

conditions = get_available_conditions()

# ============================================================================
# SESSION STATE
# ============================================================================

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'current_condition' not in st.session_state:
    st.session_state.current_condition = None

if 'stats' not in st.session_state:
    st.session_state.stats = {
        'total_queries': 0,
        'high_confidence': 0,
        'medium_confidence': 0,
        'low_confidence': 0
    }

# Mock clinical data (assuming user is logged in)
# In real app, this would come from user's account/database
if 'clinical_data' not in st.session_state:
    st.session_state.clinical_data = {
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

if 'educational_note' not in st.session_state:
    st.session_state.educational_note = None

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.title("🏥 چت‌بات پزشکی")
    st.markdown("---")
    
    # Condition selector
    st.subheader("📋 انتخاب بیماری")
    
    selected_condition = st.selectbox(
        "بیماری خود را انتخاب کنید:",
        options=list(conditions.keys()),
        format_func=lambda x: conditions[x],
        key="condition_selector"
    )
    
    # Start new chat button - also generates educational note
    if st.button("🆕 شروع چت جدید", use_container_width=True):
        st.session_state.current_condition = selected_condition
        st.session_state.messages = []
        
        # Generate educational note automatically
        condition_name = conditions[selected_condition]
        with st.spinner('📝 در حال تولید یادداشت آموزشی...'):
            note = generate_condition_note(
                condition_name=condition_name,
                clinical_data=st.session_state.clinical_data
            )
            if note:
                st.session_state.educational_note = {
                    'condition': selected_condition,
                    'condition_name': condition_name,
                    'note': note
                }
            else:
                st.session_state.educational_note = None
        
        st.rerun()
    
    st.markdown("---")
    
    # Stats
    st.subheader("📊 آمار")
    st.metric("تعداد سوالات", st.session_state.stats['total_queries'])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🟢", st.session_state.stats['high_confidence'], 
                 help="اطمینان بالا")
    with col2:
        st.metric("🟡", st.session_state.stats['medium_confidence'],
                 help="اطمینان متوسط")
    with col3:
        st.metric("🔴", st.session_state.stats['low_confidence'],
                 help="اطمینان پایین")
    
    st.markdown("---")
    
    # Info
    st.subheader("ℹ️ راهنما")
    st.info("""
    **نحوه استفاده:**
    1. یک بیماری را انتخاب کنید
    2. سوال خود را بپرسید
    3. پاسخ را دریافت کنید
    
    **مثال‌ها:**
    - چه غذاهایی خوبه؟
    - علائم چیه؟
    - دارو باید بخورم؟
    """)
    
    st.markdown("---")
    st.caption("نسخه آزمایشی - فقط برای تست")

# ============================================================================
# MAIN CHAT INTERFACE
# ============================================================================

# Header
st.title("💬 چت با دستیار پزشکی")

# Show current condition
if st.session_state.current_condition:
    condition_name = conditions[st.session_state.current_condition]
    st.success(f"📌 چت درباره: **{condition_name}**")
else:
    st.warning("⚠️ لطفا یک بیماری را از منوی کناری انتخاب کنید و روی 'شروع چت جدید' کلیک کنید")
    st.stop()

# Display educational note if available
if st.session_state.educational_note and st.session_state.educational_note['condition'] == st.session_state.current_condition:
    st.markdown("---")
    st.subheader("📚 یادداشت آموزشی شخصی‌سازی شده")
    with st.expander(f"📖 یادداشت آموزشی برای {st.session_state.educational_note['condition_name']}", expanded=True):
        st.markdown(st.session_state.educational_note['note'])
    if st.button("❌ بستن یادداشت"):
        st.session_state.educational_note = None
        st.rerun()

st.markdown("---")

# Display chat messages
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        if message['role'] == 'user':
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 شما:</strong><br>
                {message['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            confidence_class = message.get('confidence_level', 'medium-confidence')
            confidence_text = {
                'high-confidence': 'اطمینان بالا',
                'medium-confidence': 'اطمینان متوسط',
                'low-confidence': 'اطمینان پایین'
            }.get(confidence_class, 'متوسط')
            
            st.markdown(f"""
            <div class="chat-message bot-message">
                <strong>🤖 دستیار:</strong><br>
                {message['content']}
                <div class="confidence-badge {confidence_class}">
                    {confidence_text}
                </div>
            </div>
            """, unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("سوال خود را اینجا بنویسید...")

if user_input:
    # Add user message
    st.session_state.messages.append({
        'role': 'user',
        'content': user_input
    })
    
    # Get bot response
    with st.spinner('🔍 در حال جستجو...'):
        try:
            response = handler.handle_user_query(
                query=user_input,
                condition_id=st.session_state.current_condition
            )
            
            # Update stats
            st.session_state.stats['total_queries'] += 1
            
            # Handle different response types
            if response['response_type'] == 'direct_answer':
                bot_message = response['answer']
                confidence = 'high-confidence'
                st.session_state.stats['high_confidence'] += 1
                
                # Add follow-up if available
                if response.get('follow_up'):
                    bot_message += f"\n\n🤔 {response['follow_up']}"
            
            elif response['response_type'] == 'clarification':
                bot_message = response['message']
                confidence = 'medium-confidence'
                st.session_state.stats['medium_confidence'] += 1
            
            elif response['response_type'] == 'condition_mismatch':
                bot_message = f"⚠️ {response['message']}\n\n"
                bot_message += f"بیماری تشخیص داده شده: **{response['detected_condition_name']}**\n\n"
                bot_message += response['suggestion']
                confidence = 'medium-confidence'
                st.session_state.stats['medium_confidence'] += 1
            
            elif response['response_type'] == 'llm_fallback':
                # Try LLM fallback via external module
                condition_name = conditions.get(st.session_state.current_condition, "")
                llm_text = call_llm_fallback(
                    user_query=user_input,
                    condition_name=condition_name,
                    clinical_data=st.session_state.clinical_data,
                    chat_history=st.session_state.messages,
                )
                if llm_text:
                    bot_message = llm_text  
                    confidence = 'medium-confidence'
                    st.session_state.stats['medium_confidence'] += 1
                else:
                    bot_message = "❌ متأسفم، جواب دقیقی در اطلاعات موجود پیدا نکردم.\n\n"
                    bot_message += "💡 می‌توانید سوال خود را واضح‌تر بپرسید یا از کلمات دیگری استفاده کنید."
                    confidence = 'low-confidence'
                    st.session_state.stats['low_confidence'] += 1
            
            else:
                bot_message = "❌ خطا در پردازش سوال"
                confidence = 'low-confidence'
            
            # Add bot message
            st.session_state.messages.append({
                'role': 'bot',
                'content': bot_message,
                'confidence_level': confidence
            })
            
        except Exception as e:
            st.error(f"خطا: {str(e)}")
            st.session_state.messages.append({
                'role': 'bot',
                'content': f"❌ خطا در پردازش: {str(e)}",
                'confidence_level': 'low-confidence'
            })
    
    # Rerun to show new messages
    st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: 0.8rem;">
    <p>⚠️ این یک نسخه آزمایشی است. اطلاعات ارائه شده نباید جایگزین مشاوره پزشکی شود.</p>
    <p>برای تست عملکرد سیستم چت‌بات</p>
</div>
""", unsafe_allow_html=True)
