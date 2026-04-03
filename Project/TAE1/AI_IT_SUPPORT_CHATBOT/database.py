"""
Database Module for IT Support Chatbot
======================================
Handles SQLite database operations for support tickets and chat history.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os


class DatabaseManager:
    """
    Database Manager for IT Support Ticket System
    
    Manages SQLite database connections and provides methods for:
    - Creating and managing support tickets
    - Storing and retrieving chat history
    - Generating reports and statistics
    """
    
    def __init__(self, db_path: str = "database/tickets.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        # Get absolute path relative to script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(script_dir, db_path)
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get database connection with row factory.
        
        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self) -> None:
        """
        Initialize database tables if they don't exist.
        Creates tables for tickets and chat history.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create support tickets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                issue_description TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                assigned_to TEXT,
                resolution_notes TEXT,
                chat_session_id TEXT
            )
        ''')
        
        # Create chat history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                confidence REAL,
                category TEXT,
                escalation_triggered BOOLEAN DEFAULT 0
            )
        ''')
        
        # Create chat sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                user_name TEXT,
                user_email TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                issue_resolved BOOLEAN DEFAULT 0,
                ticket_created BOOLEAN DEFAULT 0,
                ticket_id INTEGER,
                FOREIGN KEY (ticket_id) REFERENCES support_tickets(id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tickets_status ON support_tickets(status)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tickets_email ON support_tickets(email)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat_history(timestamp)
        ''')
        
        conn.commit()
        conn.close()
        print(f"✓ Database initialized at: {self.db_path}")
    
    # ==================== TICKET METHODS ====================
    
    def create_ticket(
        self, 
        name: str, 
        email: str, 
        issue_description: str,
        category: str = "General",
        priority: str = "Medium",
        chat_session_id: str = None
    ) -> Dict:
        """
        Create a new support ticket.
        
        Args:
            name: User's full name
            email: User's email address
            issue_description: Detailed description of the issue
            category: Issue category (default: General)
            priority: Ticket priority - Low/Medium/High/Critical (default: Medium)
            chat_session_id: Associated chat session ID (optional)
            
        Returns:
            Dictionary with ticket details
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Generate unique ticket number
        ticket_number = self._generate_ticket_number()
        
        try:
            cursor.execute('''
                INSERT INTO support_tickets 
                (ticket_number, name, email, issue_description, category, priority, chat_session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ticket_number, name, email, issue_description, category, priority, chat_session_id))
            
            ticket_id = cursor.lastrowid
            
            # Update chat session if provided
            if chat_session_id:
                cursor.execute('''
                    UPDATE chat_sessions 
                    SET ticket_created = 1, ticket_id = ?
                    WHERE session_id = ?
                ''', (ticket_id, chat_session_id))
            
            conn.commit()
            
            return {
                'success': True,
                'ticket_id': ticket_id,
                'ticket_number': ticket_number,
                'message': f'Support ticket {ticket_number} created successfully!'
            }
            
        except sqlite3.IntegrityError:
            return {
                'success': False,
                'error': 'Failed to generate unique ticket number. Please try again.'
            }
        finally:
            conn.close()
    
    def get_ticket(self, ticket_number: str) -> Optional[Dict]:
        """
        Get ticket details by ticket number.
        
        Args:
            ticket_number: Unique ticket number
            
        Returns:
            Ticket dictionary or None if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM support_tickets WHERE ticket_number = ?
        ''', (ticket_number,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_tickets_by_email(self, email: str, limit: int = 10) -> List[Dict]:
        """
        Get all tickets for a specific email.
        
        Args:
            email: User's email address
            limit: Maximum number of tickets to return
            
        Returns:
            List of ticket dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM support_tickets 
            WHERE email = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (email, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_ticket_status(
        self, 
        ticket_number: str, 
        status: str, 
        resolution_notes: str = None
    ) -> Dict:
        """
        Update ticket status.
        
        Args:
            ticket_number: Unique ticket number
            status: New status (Open/In Progress/Resolved/Closed)
            resolution_notes: Notes about resolution (optional)
            
        Returns:
            Dictionary with update result
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        update_fields = ['status = ?', 'updated_at = CURRENT_TIMESTAMP']
        params = [status]
        
        if status.lower() in ['resolved', 'closed']:
            update_fields.append('resolved_at = CURRENT_TIMESTAMP')
        
        if resolution_notes:
            update_fields.append('resolution_notes = ?')
            params.append(resolution_notes)
        
        params.append(ticket_number)
        
        cursor.execute(f'''
            UPDATE support_tickets 
            SET {', '.join(update_fields)}
            WHERE ticket_number = ?
        ''', params)
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return {
                'success': True,
                'message': f'Ticket {ticket_number} updated to {status}'
            }
        else:
            conn.close()
            return {
                'success': False,
                'error': f'Ticket {ticket_number} not found'
            }
    
    def get_all_tickets(
        self, 
        status: str = None, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get all tickets with optional filtering.
        
        Args:
            status: Filter by status (optional)
            limit: Maximum number of tickets
            offset: Pagination offset
            
        Returns:
            List of ticket dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute('''
                SELECT * FROM support_tickets 
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (status, limit, offset))
        else:
            cursor.execute('''
                SELECT * FROM support_tickets 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_ticket_statistics(self) -> Dict:
        """
        Get ticket statistics for dashboard.
        
        Returns:
            Dictionary with statistics
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total tickets
        cursor.execute('SELECT COUNT(*) as total FROM support_tickets')
        total = cursor.fetchone()['total']
        
        # By status
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM support_tickets 
            GROUP BY status
        ''')
        by_status = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # By priority
        cursor.execute('''
            SELECT priority, COUNT(*) as count 
            FROM support_tickets 
            GROUP BY priority
        ''')
        by_priority = {row['priority']: row['count'] for row in cursor.fetchall()}
        
        # Today's tickets
        cursor.execute('''
            SELECT COUNT(*) as count 
            FROM support_tickets 
            WHERE DATE(created_at) = DATE('now')
        ''')
        today = cursor.fetchone()['count']
        
        # Average resolution time (for resolved tickets)
        cursor.execute('''
            SELECT AVG(
                (julianday(resolved_at) - julianday(created_at)) * 24
            ) as avg_hours
            FROM support_tickets 
            WHERE resolved_at IS NOT NULL
        ''')
        result = cursor.fetchone()
        avg_resolution_hours = result['avg_hours'] if result['avg_hours'] else 0
        
        conn.close()
        
        return {
            'total_tickets': total,
            'by_status': by_status,
            'by_priority': by_priority,
            'today_tickets': today,
            'avg_resolution_hours': round(avg_resolution_hours, 2) if avg_resolution_hours else 0
        }
    
    # ==================== CHAT HISTORY METHODS ====================
    
    def start_chat_session(
        self, 
        session_id: str, 
        user_name: str = None, 
        user_email: str = None
    ) -> bool:
        """
        Start a new chat session.
        
        Args:
            session_id: Unique session identifier
            user_name: User's name (optional)
            user_email: User's email (optional)
            
        Returns:
            True if successful
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO chat_sessions (session_id, user_name, user_email)
                VALUES (?, ?, ?)
            ''', (session_id, user_name, user_email))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Session already exists
            return False
        finally:
            conn.close()
    
    def end_chat_session(
        self, 
        session_id: str, 
        issue_resolved: bool = False
    ) -> bool:
        """
        End a chat session.
        
        Args:
            session_id: Session identifier
            issue_resolved: Whether the issue was resolved
            
        Returns:
            True if successful
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE chat_sessions 
            SET ended_at = CURRENT_TIMESTAMP, issue_resolved = ?
            WHERE session_id = ?
        ''', (issue_resolved, session_id))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    def log_chat_message(
        self,
        session_id: str,
        user_message: str,
        bot_response: str,
        confidence: float = None,
        category: str = None,
        escalation_triggered: bool = False
    ) -> bool:
        """
        Log a chat message exchange.
        
        Args:
            session_id: Session identifier
            user_message: User's message
            bot_response: Bot's response
            confidence: Match confidence score
            category: Issue category
            escalation_triggered: Whether escalation was triggered
            
        Returns:
            True if successful
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_history 
            (session_id, user_message, bot_response, confidence, category, escalation_triggered)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, user_message, bot_response, confidence, category, escalation_triggered))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_chat_history(self, session_id: str) -> List[Dict]:
        """
        Get chat history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of chat message dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM chat_history 
            WHERE session_id = ?
            ORDER BY timestamp ASC
        ''', (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_recent_chats(self, limit: int = 50) -> List[Dict]:
        """
        Get recent chat sessions.
        
        Args:
            limit: Maximum number of sessions
            
        Returns:
            List of chat session dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM chat_sessions 
            ORDER BY started_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def export_chat_to_file(self, session_id: str, file_path: str) -> bool:
        """
        Export chat history to a text file.
        
        Args:
            session_id: Session identifier
            file_path: Path to output file
            
        Returns:
            True if successful
        """
        chat_history = self.get_chat_history(session_id)
        
        if not chat_history:
            return False
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Chat Session: {session_id}\n")
                f.write("=" * 60 + "\n\n")
                
                for msg in chat_history:
                    f.write(f"[{msg['timestamp']}]\n")
                    f.write(f"User: {msg['user_message']}\n")
                    f.write(f"Bot: {msg['bot_response']}\n")
                    f.write("-" * 40 + "\n")
            
            return True
        except Exception as e:
            print(f"Error exporting chat: {e}")
            return False
    
    # ==================== UTILITY METHODS ====================
    
    def _generate_ticket_number(self) -> str:
        """
        Generate a unique ticket number.
        Format: IT-YYYYMMDD-XXXX
        
        Returns:
            Unique ticket number string
        """
        date_str = datetime.now().strftime('%Y%m%d')
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get count of tickets today for sequence number
        cursor.execute('''
            SELECT COUNT(*) as count 
            FROM support_tickets 
            WHERE DATE(created_at) = DATE('now')
        ''')
        
        count = cursor.fetchone()['count'] + 1
        conn.close()
        
        return f"IT-{date_str}-{count:04d}"
    
    def search_tickets(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search tickets by keyword.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching tickets
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        search_pattern = f"%{query}%"
        
        cursor.execute('''
            SELECT * FROM support_tickets 
            WHERE ticket_number LIKE ? 
               OR name LIKE ? 
               OR email LIKE ? 
               OR issue_description LIKE ?
               OR category LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def close(self) -> None:
        """Close any open connections (for cleanup)."""
        pass  # Connections are per-method


# Testing function
if __name__ == "__main__":
    print("=" * 60)
    print("Database Manager - Test Mode")
    print("=" * 60)
    
    db = DatabaseManager()
    
    # Test creating a ticket
    result = db.create_ticket(
        name="John Doe",
        email="john.doe@company.com",
        issue_description="Cannot connect to VPN from home",
        category="VPN Connection",
        priority="High"
    )
    print(f"\nCreate ticket result: {result}")
    
    # Test retrieving ticket
    if result['success']:
        ticket = db.get_ticket(result['ticket_number'])
        print(f"\nRetrieved ticket: {ticket}")
    
    # Test statistics
    stats = db.get_ticket_statistics()
    print(f"\nTicket Statistics: {json.dumps(stats, indent=2)}")
    
    # Test chat logging
    db.start_chat_session("test-session-001", "John Doe", "john@company.com")
    db.log_chat_message(
        session_id="test-session-001",
        user_message="My internet is not working",
        bot_response="Please restart your router...",
        confidence=0.95,
        category="Internet Connectivity"
    )
    
    chat_history = db.get_chat_history("test-session-001")
    print(f"\nChat history: {chat_history}")
    
    print("\n✓ Database tests completed successfully!")
