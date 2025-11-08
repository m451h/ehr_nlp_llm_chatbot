"""
SQLite Database for Chat History Storage
Stores chat sessions and messages persistently
"""

import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path


class ChatDatabase:
    """SQLite database for storing chat sessions and messages"""
    
    def __init__(self, db_path: str = "chat_history.db"):
        """
        Initialize the chat database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def _init_database(self):
        """Initialize database tables if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                condition_id TEXT NOT NULL,
                condition_name TEXT NOT NULL,
                clinical_data TEXT,  -- JSON string
                educational_note TEXT,  -- JSON string
                stats_total_queries INTEGER DEFAULT 0,
                stats_high_confidence INTEGER DEFAULT 0,
                stats_medium_confidence INTEGER DEFAULT 0,
                stats_low_confidence INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,  -- 'user' or 'bot'
                content TEXT NOT NULL,
                confidence_level TEXT,  -- For bot messages
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session_id 
            ON messages(session_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_updated_at 
            ON sessions(updated_at)
        """)
        
        conn.commit()
        conn.close()
    
    def create_session(
        self,
        session_id: str,
        condition_id: str,
        condition_name: str,
        clinical_data: Optional[Dict] = None,
        educational_note: Optional[Dict] = None
    ) -> bool:
        """
        Create a new chat session
        
        Args:
            session_id: Unique session identifier
            condition_id: Medical condition ID
            condition_name: Display name of condition
            clinical_data: Clinical data dictionary
            educational_note: Educational note dictionary
            
        Returns:
            True if successful
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        try:
            cursor.execute("""
                INSERT INTO sessions (
                    session_id, condition_id, condition_name,
                    clinical_data, educational_note,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                condition_id,
                condition_name,
                json.dumps(clinical_data) if clinical_data else None,
                json.dumps(educational_note) if educational_note else None,
                now,
                now
            ))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Session already exists
            return False
        finally:
            conn.close()
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get a session by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session dictionary or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sessions WHERE session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Convert row to dictionary
        session = dict(row)
        
        # Parse JSON fields
        if session['clinical_data']:
            session['clinical_data'] = json.loads(session['clinical_data'])
        else:
            session['clinical_data'] = {}
        
        if session['educational_note']:
            session['educational_note'] = json.loads(session['educational_note'])
        else:
            session['educational_note'] = None
        
        # Build stats dictionary
        session['stats'] = {
            'total_queries': session['stats_total_queries'],
            'high_confidence': session['stats_high_confidence'],
            'medium_confidence': session['stats_medium_confidence'],
            'low_confidence': session['stats_low_confidence']
        }
        
        # Remove individual stat fields
        for key in ['stats_total_queries', 'stats_high_confidence', 
                   'stats_medium_confidence', 'stats_low_confidence']:
            session.pop(key, None)
        
        return session
    
    def update_session_stats(self, session_id: str, stats: Dict):
        """
        Update session statistics
        
        Args:
            session_id: Session identifier
            stats: Statistics dictionary
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE sessions SET
                stats_total_queries = ?,
                stats_high_confidence = ?,
                stats_medium_confidence = ?,
                stats_low_confidence = ?,
                updated_at = ?
            WHERE session_id = ?
        """, (
            stats.get('total_queries', 0),
            stats.get('high_confidence', 0),
            stats.get('medium_confidence', 0),
            stats.get('low_confidence', 0),
            datetime.now().isoformat(),
            session_id
        ))
        
        conn.commit()
        conn.close()
    
    def update_session_educational_note(self, session_id: str, educational_note: Dict):
        """
        Update educational note for a session
        
        Args:
            session_id: Session identifier
            educational_note: Educational note dictionary
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE sessions SET
                educational_note = ?,
                updated_at = ?
            WHERE session_id = ?
        """, (
            json.dumps(educational_note),
            datetime.now().isoformat(),
            session_id
        ))
        
        conn.commit()
        conn.close()
    
    def update_session_updated_at(self, session_id: str):
        """Update the updated_at timestamp for a session"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE sessions SET updated_at = ? WHERE session_id = ?
        """, (datetime.now().isoformat(), session_id))
        
        conn.commit()
        conn.close()
    
    def update_session_clinical_data(self, session_id: str, clinical_data: Dict):
        """
        Update clinical data for a session
        
        Args:
            session_id: Session identifier
            clinical_data: Clinical data dictionary
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE sessions SET
                clinical_data = ?,
                updated_at = ?
            WHERE session_id = ?
        """, (
            json.dumps(clinical_data),
            datetime.now().isoformat(),
            session_id
        ))
        
        conn.commit()
        conn.close()
    
    def list_all_sessions(self) -> List[Dict]:
        """
        Get list of all sessions (for sidebar/history)
        
        Returns:
            List of session summaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                s.session_id,
                s.condition_id,
                s.condition_name,
                s.stats_total_queries,
                s.stats_high_confidence,
                s.stats_medium_confidence,
                s.stats_low_confidence,
                s.created_at,
                s.updated_at,
                COUNT(m.message_id) as message_count
            FROM sessions s
            LEFT JOIN messages m ON s.session_id = m.session_id
            GROUP BY s.session_id
            ORDER BY s.updated_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        sessions = []
        for row in rows:
            # Get first user message as preview
            preview = self._get_session_preview(row['session_id'])
            
            session = {
                'session_id': row['session_id'],
                'condition_id': row['condition_id'],
                'condition_name': row['condition_name'],
                'preview': preview or 'چت جدید',
                'message_count': row['message_count'],
                'created_at': row['created_at'],
                'last_updated': row['updated_at'],
                'stats': {
                    'total_queries': row['stats_total_queries'],
                    'high_confidence': row['stats_high_confidence'],
                    'medium_confidence': row['stats_medium_confidence'],
                    'low_confidence': row['stats_low_confidence']
                }
            }
            sessions.append(session)
        
        return sessions
    
    def _get_session_preview(self, session_id: str, max_length: int = 50) -> Optional[str]:
        """Get first user message as preview"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT content FROM messages
            WHERE session_id = ? AND role = 'user'
            ORDER BY created_at ASC
            LIMIT 1
        """, (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            content = row['content']
            return content[:max_length] if len(content) > max_length else content
        return None
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        confidence_level: Optional[str] = None
    ) -> int:
        """
        Add a message to a session
        
        Args:
            session_id: Session identifier
            role: 'user' or 'bot'
            content: Message content
            confidence_level: Confidence level for bot messages
            
        Returns:
            Message ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO messages (session_id, role, content, confidence_level, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, role, content, confidence_level, now))
        
        message_id = cursor.lastrowid
        
        # Update session updated_at timestamp
        self.update_session_updated_at(session_id)
        
        conn.commit()
        conn.close()
        
        return message_id
    
    def get_messages(self, session_id: str) -> List[Dict]:
        """
        Get all messages for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of message dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT role, content, confidence_level, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC
        """, (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        messages = []
        for row in rows:
            message = {
                'role': row['role'],
                'content': row['content'],
                'created_at': row['created_at']
            }
            if row['confidence_level']:
                message['confidence_level'] = row['confidence_level']
            messages.append(message)
        
        return messages
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its messages
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def get_full_session(self, session_id: str) -> Optional[Dict]:
        """
        Get full session with all messages
        
        Args:
            session_id: Session identifier
            
        Returns:
            Complete session dictionary with messages, or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Add messages
        session['messages'] = self.get_messages(session_id)
        
        return session

