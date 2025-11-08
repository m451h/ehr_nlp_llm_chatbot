# Database Architecture Explanation

## Overview

The database system uses **SQLite** to persistently store chat sessions and messages. This replaces the previous in-memory storage, ensuring chat history survives server restarts.

---

## Database Structure

### 1. **Sessions Table** (`sessions`)

Stores information about each chat session:

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | TEXT (PRIMARY KEY) | Unique identifier for each chat session (UUID) |
| `condition_id` | TEXT | Medical condition ID (e.g., "cond_type_2_diabetes") |
| `condition_name` | TEXT | Display name in Persian (e.g., "دیابت نوع ۲") |
| `clinical_data` | TEXT | JSON string containing patient clinical data |
| `educational_note` | TEXT | JSON string containing educational note |
| `stats_total_queries` | INTEGER | Total number of queries in this session |
| `stats_high_confidence` | INTEGER | Number of high-confidence responses |
| `stats_medium_confidence` | INTEGER | Number of medium-confidence responses |
| `stats_low_confidence` | INTEGER | Number of low-confidence responses |
| `created_at` | TEXT | ISO timestamp when session was created |
| `updated_at` | TEXT | ISO timestamp when session was last updated |

**Example Row:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "condition_id": "cond_type_2_diabetes",
  "condition_name": "دیابت نوع ۲",
  "clinical_data": "{\"سن\": \"45 سال\", \"جنسیت\": \"مرد\"}",
  "stats_total_queries": 5,
  "created_at": "2024-01-15T10:30:00"
}
```

### 2. **Messages Table** (`messages`)

Stores individual chat messages:

| Column | Type | Description |
|--------|------|-------------|
| `message_id` | INTEGER (PRIMARY KEY) | Auto-incrementing unique ID |
| `session_id` | TEXT (FOREIGN KEY) | Links to sessions table |
| `role` | TEXT | Either "user" or "bot" |
| `content` | TEXT | The actual message text |
| `confidence_level` | TEXT | For bot messages: "high-confidence", "medium-confidence", or "low-confidence" |
| `created_at` | TEXT | ISO timestamp when message was created |

**Foreign Key:** `session_id` references `sessions(session_id)` with `ON DELETE CASCADE` - if a session is deleted, all its messages are automatically deleted.

**Example Rows:**
```json
[
  {
    "message_id": 1,
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "role": "user",
    "content": "چه غذاهایی برای دیابت خوبه؟",
    "confidence_level": null,
    "created_at": "2024-01-15T10:30:15"
  },
  {
    "message_id": 2,
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "role": "bot",
    "content": "برای دیابت نوع ۲...",
    "confidence_level": "high-confidence",
    "created_at": "2024-01-15T10:30:20"
  }
]
```

### 3. **Indexes**

For faster queries:

- `idx_messages_session_id`: Index on `messages.session_id` - speeds up finding all messages for a session
- `idx_sessions_updated_at`: Index on `sessions.updated_at` - speeds up sorting sessions by last update time

---

## Class Architecture: `ChatDatabase`

### Initialization

```python
chat_db = ChatDatabase(db_path="chat_history.db")
```

**What happens:**
1. Creates/connects to SQLite database file `chat_history.db`
2. Automatically creates tables if they don't exist
3. Creates indexes for performance

### Core Methods

#### 1. **Session Management**

##### `create_session()`
Creates a new chat session in the database.

```python
chat_db.create_session(
    session_id="uuid-here",
    condition_id="cond_type_2_diabetes",
    condition_name="دیابت نوع ۲",
    clinical_data={"سن": "45 سال"},
    educational_note={"note": "..."}
)
```

**What it does:**
- Inserts a new row into `sessions` table
- Converts Python dictionaries to JSON strings for storage
- Sets `created_at` and `updated_at` timestamps

##### `get_session(session_id)`
Retrieves a session by ID.

**What it does:**
- Queries `sessions` table
- Converts JSON strings back to Python dictionaries
- Transforms flat stats columns into a `stats` dictionary
- Returns a Python dictionary

**Returns:**
```python
{
    "session_id": "...",
    "condition_id": "...",
    "condition_name": "...",
    "clinical_data": {...},  # Parsed from JSON
    "educational_note": {...},  # Parsed from JSON
    "stats": {
        "total_queries": 5,
        "high_confidence": 3,
        "medium_confidence": 1,
        "low_confidence": 1
    },
    "created_at": "...",
    "updated_at": "..."
}
```

##### `list_all_sessions()`
Gets all sessions for sidebar display.

**What it does:**
- Uses SQL `LEFT JOIN` to combine sessions with message counts
- Orders by `updated_at` DESC (newest first)
- For each session, gets the first user message as a preview
- Returns a list of session summaries

**Returns:**
```python
[
    {
        "session_id": "...",
        "condition_id": "...",
        "condition_name": "دیابت نوع ۲",
        "preview": "چه غذاهایی برای دیابت خوبه؟",
        "message_count": 4,
        "created_at": "...",
        "last_updated": "...",
        "stats": {...}
    },
    ...
]
```

#### 2. **Message Management**

##### `add_message()`
Adds a message to a session.

```python
chat_db.add_message(
    session_id="...",
    role="user",  # or "bot"
    content="سوال من",
    confidence_level="high-confidence"  # Only for bot messages
)
```

**What it does:**
- Inserts a new row into `messages` table
- Automatically updates the session's `updated_at` timestamp
- Returns the new message ID

##### `get_messages(session_id)`
Retrieves all messages for a session.

**What it does:**
- Queries `messages` table filtered by `session_id`
- Orders by `created_at` ASC (oldest first)
- Returns a list of message dictionaries

**Returns:**
```python
[
    {
        "role": "user",
        "content": "سوال من",
        "created_at": "..."
    },
    {
        "role": "bot",
        "content": "پاسخ من",
        "confidence_level": "high-confidence",
        "created_at": "..."
    }
]
```

#### 3. **Update Methods**

##### `update_session_stats()`
Updates statistics for a session.

```python
chat_db.update_session_stats(
    session_id="...",
    stats={
        "total_queries": 6,
        "high_confidence": 4,
        "medium_confidence": 1,
        "low_confidence": 1
    }
)
```

**What it does:**
- Updates the stats columns in `sessions` table
- Updates `updated_at` timestamp

##### `update_session_clinical_data()`
Updates clinical data for a session.

##### `update_session_educational_note()`
Updates educational note for a session.

##### `update_session_updated_at()`
Updates the `updated_at` timestamp (called automatically when messages are added).

#### 4. **Utility Methods**

##### `get_full_session(session_id)`
Gets a complete session with all messages.

**What it does:**
- Calls `get_session()` to get session data
- Calls `get_messages()` to get all messages
- Combines them into one dictionary

**Returns:**
```python
{
    "session_id": "...",
    "condition_id": "...",
    "condition_name": "...",
    "clinical_data": {...},
    "stats": {...},
    "messages": [
        {"role": "user", "content": "..."},
        {"role": "bot", "content": "..."}
    ]
}
```

##### `delete_session(session_id)`
Deletes a session and all its messages.

**What it does:**
- Deletes from `sessions` table
- Due to `ON DELETE CASCADE`, all related messages are automatically deleted
- Returns `True` if deleted, `False` if not found

---

## Data Flow: How It Works

### 1. **Starting a New Chat**

```
User → API: POST /api/chat/start
  ↓
API creates session_id (UUID)
  ↓
API calls: chat_db.create_session()
  ↓
Database: INSERT INTO sessions
  ↓
Returns session_id to user
```

### 2. **Sending a Message**

```
User → API: POST /api/chat/query
  ↓
API calls: chat_db.get_session() → Get session info
  ↓
API calls: chat_db.add_message() → Save user message
  ↓
API processes query → Gets bot response
  ↓
API calls: chat_db.add_message() → Save bot response
  ↓
API calls: chat_db.update_session_stats() → Update stats
  ↓
Returns response to user
```

### 3. **Loading Chat History**

```
User → API: GET /api/chat/history/{session_id}
  ↓
API calls: chat_db.get_full_session()
  ↓
Database: SELECT from sessions + SELECT from messages
  ↓
Returns complete session with messages
```

### 4. **Listing All Sessions (Sidebar)**

```
User → API: GET /api/chat/sessions
  ↓
API calls: chat_db.list_all_sessions()
  ↓
Database: SELECT with JOIN and COUNT
  ↓
For each session: Get preview message
  ↓
Returns list of session summaries
```

---

## Key Design Decisions

### 1. **Why JSON for Complex Data?**

`clinical_data` and `educational_note` are stored as JSON strings because:
- They're nested dictionaries with varying structure
- SQLite doesn't have native JSON support (in older versions)
- Easy to serialize/deserialize with Python's `json` module

### 2. **Why Separate Tables?**

Sessions and messages are in separate tables because:
- **Normalization**: Avoids data duplication
- **Scalability**: Can have many messages per session
- **Performance**: Can query messages independently
- **Flexibility**: Easy to add message metadata later

### 3. **Why Indexes?**

Indexes on `session_id` and `updated_at` because:
- **Fast lookups**: Finding messages by session_id is common
- **Fast sorting**: Listing sessions by last update is common
- **Performance**: Without indexes, queries scan entire tables

### 4. **Why CASCADE Delete?**

`ON DELETE CASCADE` on messages because:
- **Data integrity**: Prevents orphaned messages
- **Automatic cleanup**: Deleting a session removes all messages
- **Simplicity**: No need to manually delete messages first

---

## Connection Management

### Pattern Used

```python
def some_method(self):
    conn = self._get_connection()  # Open connection
    cursor = conn.cursor()
    
    try:
        cursor.execute("...")  # Do work
        conn.commit()  # Save changes
    finally:
        conn.close()  # Always close connection
```

**Why this pattern?**
- **Resource management**: Always closes connections
- **Transaction safety**: Commits only on success
- **Error handling**: Connection closed even if error occurs

---

## Integration with API

### In `api.py`:

```python
# Initialize database once
chat_db = ChatDatabase()

# Use in endpoints
@app.post("/api/chat/start")
def start_chat(request):
    session_id = str(uuid.uuid4())
    chat_db.create_session(...)  # Save to database
    return {"session_id": session_id}

@app.post("/api/chat/query")
def query_chat(request):
    session = chat_db.get_session(request.session_id)  # Load from database
    chat_db.add_message(...)  # Save message
    return response
```

---

## Benefits of This Design

1. **Persistence**: Chat history survives server restarts
2. **Scalability**: Can handle many sessions and messages
3. **Performance**: Indexes make queries fast
4. **Data Integrity**: Foreign keys ensure consistency
5. **Simplicity**: SQLite requires no separate server
6. **Portability**: Database is a single file

---

## Example Queries

### Get all sessions with message counts:
```sql
SELECT 
    s.session_id,
    s.condition_name,
    COUNT(m.message_id) as message_count
FROM sessions s
LEFT JOIN messages m ON s.session_id = m.session_id
GROUP BY s.session_id
ORDER BY s.updated_at DESC;
```

### Get all messages for a session:
```sql
SELECT role, content, created_at
FROM messages
WHERE session_id = ?
ORDER BY created_at ASC;
```

### Update session statistics:
```sql
UPDATE sessions
SET 
    stats_total_queries = ?,
    stats_high_confidence = ?,
    updated_at = ?
WHERE session_id = ?;
```

---

## File Location

The database file `chat_history.db` is created in the project root directory when the API first starts.

You can inspect it using SQLite tools:
```bash
sqlite3 chat_history.db
.tables
SELECT * FROM sessions;
SELECT * FROM messages;
```

