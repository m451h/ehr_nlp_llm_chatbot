# EHR Chatbot API Documentation

REST API for the EHR Medical Chatbot. This API exposes all functionality from `app.py` as REST endpoints.

## Base URL

```
http://localhost:8000
```

For production, replace with your production server URL.

## Quick Start

1. **Start the API server:**
   ```bash
   uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

2. **View API documentation:**
   Open your browser and go to: `http://localhost:8000/docs`

   This will show the interactive Swagger UI documentation.

3. **Use the JavaScript client:**
   ```javascript
   import { EHRChatbotAPI } from './api_example.js';
   
   const api = new EHRChatbotAPI('http://localhost:8000');
   ```

## API Endpoints

### 1. Health Check

**GET** `/api/health`

Check if the API and chatbot are loaded correctly.

**Response:**
```json
{
  "status": "healthy",
  "chatbot_loaded": true
}
```

---

### 2. Get Available Conditions

**GET** `/api/conditions`

Get all available medical conditions.

**Response:**
```json
{
  "success": true,
  "conditions": {
    "cond_type_2_diabetes": "دیابت نوع ۲",
    "cond_hypertension": "فشار خون بالا",
    "cond_asthma": "آسم"
  }
}
```

---

### 3. Start Chat Session

**POST** `/api/chat/start`

Start a new chat session for a specific condition.

**Request Body:**
```json
{
  "condition_id": "cond_type_2_diabetes",
  "clinical_data": {
    "age": "45 سال",
    "gender": "مرد",
    "weight": "78 کیلوگرم",
    "height": "175 سانتی‌متر",
    "blood_pressure": "140/90 mmHg",
    "fasting_blood_sugar": "95 mg/dL",
    "cholesterol": "220 mg/dL",
    "current_medications": "متفورمین 500mg",
    "medical_history": "فشار خون بالا"
  },
  "generate_educational_note": true
}
```

**Note:** You can use either Persian keys (like `"سن"`, `"جنسیت"`) or English keys (like `"age"`, `"gender"`). The API will automatically convert them.

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "condition_id": "cond_type_2_diabetes",
  "condition_name": "دیابت نوع ۲",
  "educational_note": {
    "condition": "cond_type_2_diabetes",
    "condition_name": "دیابت نوع ۲",
    "note": "یادداشت آموزشی شخصی‌سازی شده..."
  }
}
```

---

### 4. Send Query

**POST** `/api/chat/query`

Send a question to the chatbot.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "query": "چه غذاهایی برای دیابت خوبه؟"
}
```

**Response:**
```json
{
  "success": true,
  "message": "برای دیابت نوع ۲، غذاهای مناسب شامل...",
  "confidence_level": "high-confidence",
  "response_type": "direct_answer",
  "stats": {
    "total_queries": 1,
    "high_confidence": 1,
    "medium_confidence": 0,
    "low_confidence": 0
  }
}
```

**Confidence Levels:**
- `high-confidence`: Direct answer from knowledge base
- `medium-confidence`: Clarification needed or LLM fallback
- `low-confidence`: No good match found

**Response Types:**
- `direct_answer`: High confidence match from knowledge base
- `clarification`: Medium confidence, asking for clarification
- `condition_mismatch`: Question seems to be about different condition
- `llm_fallback`: Low confidence, using LLM to generate answer

---

### 5. Get Chat History

**GET** `/api/chat/history/{session_id}`

Get full chat history for a session.

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_condition": "cond_type_2_diabetes",
  "condition_name": "دیابت نوع ۲",
  "messages": [
    {
      "role": "user",
      "content": "چه غذاهایی برای دیابت خوبه؟"
    },
    {
      "role": "bot",
      "content": "برای دیابت نوع ۲...",
      "confidence_level": "high-confidence"
    }
  ],
  "stats": {
    "total_queries": 1,
    "high_confidence": 1,
    "medium_confidence": 0,
    "low_confidence": 0
  },
  "educational_note": {
    "condition": "cond_type_2_diabetes",
    "condition_name": "دیابت نوع ۲",
    "note": "..."
  }
}
```

---

### 6. Generate Educational Note

**POST** `/api/chat/educational-note`

Generate an educational note for a condition without starting a chat.

**Request Body:**
```json
{
  "condition_id": "cond_type_2_diabetes",
  "clinical_data": {
    "age": "45 سال",
    "gender": "مرد",
    ...
  }
}
```

**Response:**
```json
{
  "success": true,
  "condition_id": "cond_type_2_diabetes",
  "condition_name": "دیابت نوع ۲",
  "note": "یادداشت آموزشی جامع..."
}
```

---

### 7. Update Clinical Data

**POST** `/api/chat/update-clinical-data`

Update clinical data for an existing session.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "clinical_data": {
    "age": "46 سال",
    "weight": "80 کیلوگرم",
    ...
  }
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "clinical_data": {
    "age": "46 سال",
    "weight": "80 کیلوگرم",
    ...
  }
}
```

---

### 8. Get Statistics

**GET** `/api/stats/{session_id}`

Get statistics for a session.

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "stats": {
    "total_queries": 5,
    "high_confidence": 3,
    "medium_confidence": 1,
    "low_confidence": 1
  }
}
```

---

### 9. Delete Session

**DELETE** `/api/chat/session/{session_id}`

Delete a chat session.

**Response:**
```json
{
  "success": true,
  "message": "Session deleted"
}
```

---

## Error Responses

All endpoints may return errors in the following format:

```json
{
  "detail": "Error message here"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (session not found, etc.)
- `500`: Internal Server Error

---

## JavaScript Usage Examples

### Basic Usage

```javascript
import { EHRChatbotAPI } from './api_example.js';

const api = new EHRChatbotAPI('http://localhost:8000');

// Start a chat
const startResponse = await api.startChat(
  'cond_type_2_diabetes',
  {
    age: '45 سال',
    gender: 'مرد',
    weight: '78 کیلوگرم'
  }
);

const sessionId = startResponse.session_id;

// Send a query
const response = await api.queryChat(
  sessionId,
  'چه غذاهایی خوبه؟'
);

console.log(response.message);
```

### React Hook Example

```javascript
import { useEHRChatbot } from './api_example.js';

function ChatComponent() {
  const { sessionId, messages, loading, startChat, sendMessage } = useEHRChatbot();

  const handleStart = async () => {
    await startChat('cond_type_2_diabetes', {
      age: '45 سال',
      gender: 'مرد'
    });
  };

  const handleSend = async (query) => {
    await sendMessage(query);
  };

  return (
    <div>
      {!sessionId && (
        <button onClick={handleStart}>Start Chat</button>
      )}
      
      {messages.map((msg, idx) => (
        <div key={idx}>
          {msg.role === 'user' ? '👤' : '🤖'} {msg.content}
        </div>
      ))}
      
      {sessionId && (
        <input 
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              handleSend(e.target.value);
              e.target.value = '';
            }
          }}
        />
      )}
    </div>
  );
}
```

---

## Clinical Data Format

You can use either Persian or English keys for clinical data:

**Persian Keys:**
```json
{
  "سن": "45 سال",
  "جنسیت": "مرد",
  "وزن": "78 کیلوگرم",
  "قد": "175 سانتی‌متر",
  "فشار خون": "140/90 mmHg",
  "قند خون ناشتا": "95 mg/dL",
  "کلسترول": "220 mg/dL",
  "داروهای فعلی": "متفورمین 500mg",
  "سابقه بیماری": "فشار خون بالا"
}
```

**English Keys (automatically converted):**
```json
{
  "age": "45 سال",
  "gender": "مرد",
  "weight": "78 کیلوگرم",
  "height": "175 سانتی‌متر",
  "blood_pressure": "140/90 mmHg",
  "fasting_blood_sugar": "95 mg/dL",
  "cholesterol": "220 mg/dL",
  "current_medications": "متفورمین 500mg",
  "medical_history": "فشار خون بالا"
}
```

---

## CORS Configuration

The API is configured to allow CORS from all origins. For production, update the CORS settings in `api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Session Management

Sessions are stored in-memory by default. In production, you may want to:

1. Use Redis for session storage
2. Use a database for persistence
3. Add session expiration
4. Add authentication/authorization

---

## Testing

You can test the API using:

1. **Swagger UI:** `http://localhost:8000/docs`
2. **Postman/Insomnia:** Import the endpoints
3. **JavaScript client:** See `api_example.js`
4. **cURL:**
   ```bash
   curl -X POST http://localhost:8000/api/chat/start \
     -H "Content-Type: application/json" \
     -d '{"condition_id": "cond_type_2_diabetes", "generate_educational_note": true}'
   ```

---

## Notes

- The chatbot handler is loaded once at startup and reused for all requests
- Sessions are stored in-memory (not persistent across server restarts)
- Clinical data is used to personalize LLM responses
- The API automatically converts English keys to Persian keys for clinical data
- All text responses are in Persian (Farsi)

