# Startup Guide - EHR Chatbot with SQLite Database

## Quick Start

### 1. **Install Dependencies** (if not already installed)

```bash
pip install -r requirements.txt
```

**Note:** SQLite is built into Python, so no additional database installation is needed!

---

## Starting the API Server (with Database)

### Option 1: Development Mode (with auto-reload)

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

**What happens:**
- ✅ API server starts on `http://localhost:8000`
- ✅ SQLite database `chat_history.db` is **automatically created** in project root
- ✅ Database tables are **automatically created** if they don't exist
- ✅ Server reloads automatically when you change code

### Option 2: Production Mode

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

**What happens:**
- ✅ API server starts with 4 worker processes
- ✅ Database is created automatically (same as above)
- ⚠️ No auto-reload (for production use)

### Verify It's Working

1. **Check API is running:**
   ```bash
   curl http://localhost:8000/api/health
   ```
   Should return:
   ```json
   {"status": "healthy", "chatbot_loaded": true}
   ```

2. **View API Documentation:**
   Open in browser: `http://localhost:8000/docs`
   - Interactive Swagger UI
   - Test endpoints directly
   - See all available endpoints

3. **Check Database File:**
   ```bash
   ls chat_history.db  # Linux/Mac
   dir chat_history.db  # Windows
   ```
   The file should exist after first API call.

---

## Starting the Streamlit App (Optional)

If you want to use the Streamlit interface instead of the API:

```bash
streamlit run app.py
```

**Note:** The Streamlit app (`app.py`) still uses in-memory storage. If you want it to use the database too, you'd need to update it to use the API endpoints or integrate `ChatDatabase` directly.

---

## What Happens Automatically

### On First Start:

1. **Database File Creation:**
   - When `ChatDatabase()` is initialized, it creates `chat_history.db` in the project root
   - If the file already exists, it connects to it

2. **Table Creation:**
   - `sessions` table is created automatically
   - `messages` table is created automatically
   - Indexes are created for performance

3. **No Manual Setup Required:**
   - ✅ No database server to start
   - ✅ No migrations to run
   - ✅ No configuration needed
   - ✅ Everything happens automatically!

---

## Testing the Database

### 1. Start a Chat Session

```bash
curl -X POST "http://localhost:8000/api/chat/start" \
  -H "Content-Type: application/json" \
  -d '{
    "condition_id": "cond_type_2_diabetes",
    "generate_educational_note": true
  }'
```

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "condition_id": "cond_type_2_diabetes",
  "condition_name": "دیابت نوع ۲",
  "educational_note": {...}
}
```

### 2. Send a Message

```bash
curl -X POST "http://localhost:8000/api/chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "query": "چه غذاهایی برای دیابت خوبه؟"
  }'
```

### 3. Get All Sessions (for Sidebar)

```bash
curl "http://localhost:8000/api/chat/sessions"
```

**Response:**
```json
{
  "success": true,
  "total": 1,
  "sessions": [
    {
      "session_id": "...",
      "condition_name": "دیابت نوع ۲",
      "preview": "چه غذاهایی برای دیابت خوبه؟",
      "message_count": 2,
      "last_updated": "2024-01-15T10:30:00",
      "stats": {...}
    }
  ]
}
```

### 4. Get Chat History

```bash
curl "http://localhost:8000/api/chat/history/550e8400-e29b-41d4-a716-446655440000"
```

---

## Database File Location

The database file is created in the **project root directory**:

```
ehr_nlp_llm_chatbot/
├── chat_history.db  ← SQLite database file (created automatically)
├── api.py
├── app.py
├── requirements.txt
└── ...
```

---

## Inspecting the Database

### Using SQLite Command Line:

```bash
sqlite3 chat_history.db
```

**Useful commands:**
```sql
.tables                    -- List all tables
.schema sessions           -- Show sessions table structure
.schema messages           -- Show messages table structure
SELECT * FROM sessions;    -- View all sessions
SELECT * FROM messages;    -- View all messages
.quit                      -- Exit
```

### Using Python:

```python
import sqlite3

conn = sqlite3.connect('chat_history.db')
cursor = conn.cursor()

# View all sessions
cursor.execute("SELECT * FROM sessions")
print(cursor.fetchall())

# View all messages
cursor.execute("SELECT * FROM messages")
print(cursor.fetchall())

conn.close()
```

---

## Troubleshooting

### Issue: "No module named 'src.database.chat_db'"

**Solution:**
- Make sure you're in the project root directory
- The import path assumes you're running from the root

### Issue: "Database is locked"

**Solution:**
- SQLite doesn't handle concurrent writes well
- Make sure only one process is accessing the database
- In production, consider using PostgreSQL or MySQL

### Issue: "Table already exists"

**Solution:**
- This is normal! The code uses `CREATE TABLE IF NOT EXISTS`
- It won't recreate tables if they already exist
- Your data is safe

### Issue: Database file not created

**Solution:**
- Check file permissions in the project directory
- Make sure you have write access
- The database is created on first API call, not on import

---

## Project Structure

```
ehr_nlp_llm_chatbot/
├── api.py                    # FastAPI server (uses database)
├── app.py                    # Streamlit app (in-memory)
├── chat_history.db           # SQLite database (auto-created)
├── requirements.txt          # Python dependencies
├── src/
│   ├── database/
│   │   ├── chat_db.py        # SQLite database class
│   │   └── vector_db.py      # Vector database (ChromaDB)
│   ├── models/               # ML models
│   ├── search/               # Search engine
│   └── loaders/              # Data loaders
├── scripts/                  # Utility scripts
└── tests/                    # Test files
```

---

## Next Steps

1. **Start the API:**
   ```bash
   uvicorn api:app --reload
   ```

2. **Test the endpoints:**
   - Open `http://localhost:8000/docs` in browser
   - Try the interactive API documentation

3. **Connect your frontend:**
   - Use the API endpoints from your frontend
   - See `api_example.js` for JavaScript examples
   - See `API_DOCUMENTATION.md` for full API docs

4. **View chat history:**
   - Use `GET /api/chat/sessions` for sidebar
   - Use `GET /api/chat/history/{session_id}` for full history

---

## Important Notes

### ✅ What's Automatic:
- Database file creation
- Table creation
- Index creation
- No manual setup needed

### ⚠️ What to Remember:
- Database file is in project root
- Data persists across server restarts
- SQLite is single-file (easy to backup)
- For production with high concurrency, consider PostgreSQL

### 🔒 Data Persistence:
- All chat history is saved to `chat_history.db`
- Data survives server restarts
- To reset: delete `chat_history.db` file
- To backup: copy `chat_history.db` file

---

## Summary

**To start the project with database:**

1. Install dependencies: `pip install -r requirements.txt`
2. Start API: `uvicorn api:app --reload`
3. Database is created automatically!
4. Test at: `http://localhost:8000/docs`

That's it! No database setup required. 🎉

