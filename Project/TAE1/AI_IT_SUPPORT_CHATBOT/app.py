"""
AI IT Support Chatbot - Flask Application
=========================================
Main entry point for the IT Support Chatbot web application.

This application provides:
- RESTful API endpoints for chatbot interaction
- Support ticket management
- Chat history logging
- Dialogflow integration
- Web interface for chat
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from datetime import datetime
import uuid
import os
import json
import logging
from logging.handlers import RotatingFileHandler

# Import custom modules
from chatbot_engine import ITSupportChatbot, HybridChatbotEngine
from database import DatabaseManager

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)  # Enable CORS for all routes

# Configuration
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size

# Initialize components
chatbot = ITSupportChatbot('rules.json')
db = DatabaseManager()

# Setup logging
def setup_logging():
    """Configure application logging."""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'chatbot.log')
    
    handler = RotatingFileHandler(
        log_file, 
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    
    # Also log to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

setup_logging()

# ==================== WEB ROUTES ====================

@app.route('/')
def index():
    """
    Render the main chat interface.
    
    Returns:
        HTML template for chat interface
    """
    # Generate session ID if not exists
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    return render_template('index.html')

@app.route('/admin')
def admin_dashboard():
    """
    Render admin dashboard (placeholder).
    
    Returns:
        Simple admin page with statistics
    """
    stats = db.get_ticket_statistics()
    return jsonify({
        'message': 'Admin Dashboard',
        'statistics': stats
    })

# ==================== API ROUTES - CHAT ====================

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint - process user message and return bot response.
    
    Request Body:
        {
            "message": "User's message",
            "session_id": "optional-session-id"
        }
    
    Returns:
        {
            "response": "Bot's response",
            "confidence": 0.95,
            "category": "Issue Category",
            "escalation_required": false,
            "session_id": "session-id"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id') or session.get('session_id') or str(uuid.uuid4())
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        # Log the incoming message
        app.logger.info(f"Chat request - Session: {session_id}, Message: {user_message[:50]}...")
        
        # Get response from chatbot
        result = chatbot.get_response(user_message)
        
        # Log chat to database
        db.log_chat_message(
            session_id=session_id,
            user_message=user_message,
            bot_response=result['response'],
            confidence=result.get('confidence'),
            category=result.get('category'),
            escalation_triggered=result.get('escalation_required', False)
        )
        
        # Prepare response
        response_data = {
            'success': True,
            'response': result['response'],
            'confidence': result.get('confidence', 0),
            'category': result.get('category', 'Unknown'),
            'escalation_required': result.get('escalation_required', False),
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }
        
        app.logger.info(f"Chat response - Category: {result.get('category')}, Confidence: {result.get('confidence')}")
        
        return jsonify(response_data)
        
    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/chat/suggestions', methods=['GET'])
def get_suggestions():
    """
    Get chat suggestions based on partial input.
    
    Query Parameters:
        q: Partial input text
    
    Returns:
        List of suggested categories
    """
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify({'suggestions': []})
    
    suggestions = chatbot.get_suggestions(query)
    
    return jsonify({
        'suggestions': suggestions,
        'query': query
    })

@app.route('/api/chat/categories', methods=['GET'])
def get_categories():
    """
    Get all available issue categories.
    
    Returns:
        List of category names
    """
    categories = chatbot.get_all_categories()
    
    return jsonify({
        'categories': categories,
        'count': len(categories)
    })

# ==================== API ROUTES - TICKETS ====================

@app.route('/api/tickets', methods=['POST'])
def create_ticket():
    """
    Create a new support ticket.
    
    Request Body:
        {
            "name": "User's name",
            "email": "User's email",
            "issue_description": "Detailed description",
            "category": "Issue category",
            "priority": "Low/Medium/High/Critical",
            "session_id": "optional-chat-session-id"
        }
    
    Returns:
        Ticket creation result with ticket number
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['name', 'email', 'issue_description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field.replace("_", " ").title()} is required'
                }), 400
        
        # Create ticket
        result = db.create_ticket(
            name=data.get('name').strip(),
            email=data.get('email').strip().lower(),
            issue_description=data.get('issue_description').strip(),
            category=data.get('category', 'General'),
            priority=data.get('priority', 'Medium'),
            chat_session_id=data.get('session_id')
        )
        
        if result['success']:
            app.logger.info(f"Ticket created: {result['ticket_number']} for {data.get('email')}")
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error creating ticket: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create ticket',
            'message': str(e)
        }), 500

@app.route('/api/tickets/<ticket_number>', methods=['GET'])
def get_ticket(ticket_number):
    """
    Get ticket details by ticket number.
    
    Args:
        ticket_number: Unique ticket identifier
    
    Returns:
        Ticket details
    """
    ticket = db.get_ticket(ticket_number)
    
    if ticket:
        return jsonify({
            'success': True,
            'ticket': ticket
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Ticket {ticket_number} not found'
        }), 404

@app.route('/api/tickets/user/<email>', methods=['GET'])
def get_user_tickets(email):
    """
    Get all tickets for a specific user.
    
    Args:
        email: User's email address
    
    Query Parameters:
        limit: Maximum number of tickets (default: 10)
    
    Returns:
        List of user's tickets
    """
    limit = request.args.get('limit', 10, type=int)
    tickets = db.get_tickets_by_email(email, limit)
    
    return jsonify({
        'success': True,
        'email': email,
        'count': len(tickets),
        'tickets': tickets
    })

@app.route('/api/tickets/<ticket_number>/status', methods=['PUT'])
def update_ticket_status(ticket_number):
    """
    Update ticket status.
    
    Args:
        ticket_number: Unique ticket identifier
    
    Request Body:
        {
            "status": "Open/In Progress/Resolved/Closed",
            "resolution_notes": "Optional notes"
        }
    
    Returns:
        Update result
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('status'):
            return jsonify({
                'success': False,
                'error': 'Status is required'
            }), 400
        
        result = db.update_ticket_status(
            ticket_number=ticket_number,
            status=data.get('status'),
            resolution_notes=data.get('resolution_notes')
        )
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error updating ticket: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update ticket'
        }), 500

@app.route('/api/tickets', methods=['GET'])
def list_tickets():
    """
    List all tickets with optional filtering.
    
    Query Parameters:
        status: Filter by status
        limit: Maximum results (default: 50)
        offset: Pagination offset (default: 0)
    
    Returns:
        List of tickets
    """
    status = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    tickets = db.get_all_tickets(status=status, limit=limit, offset=offset)
    
    return jsonify({
        'success': True,
        'count': len(tickets),
        'tickets': tickets
    })

@app.route('/api/tickets/search', methods=['GET'])
def search_tickets():
    """
    Search tickets by keyword.
    
    Query Parameters:
        q: Search query
        limit: Maximum results (default: 20)
    
    Returns:
        List of matching tickets
    """
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query is required'
        }), 400
    
    tickets = db.search_tickets(query, limit)
    
    return jsonify({
        'success': True,
        'query': query,
        'count': len(tickets),
        'tickets': tickets
    })

# ==================== API ROUTES - STATISTICS ====================

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    Get system statistics.
    
    Returns:
        Ticket and chat statistics
    """
    try:
        ticket_stats = db.get_ticket_statistics()
        
        return jsonify({
            'success': True,
            'statistics': {
                'tickets': ticket_stats,
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        app.logger.error(f"Error getting statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get statistics'
        }), 500

# ==================== API ROUTES - CHAT SESSIONS ====================

@app.route('/api/sessions', methods=['POST'])
def start_session():
    """
    Start a new chat session.
    
    Request Body:
        {
            "user_name": "Optional user name",
            "user_email": "Optional user email"
        }
    
    Returns:
        Session ID
    """
    try:
        data = request.get_json() or {}
        session_id = str(uuid.uuid4())
        
        db.start_chat_session(
            session_id=session_id,
            user_name=data.get('user_name'),
            user_email=data.get('user_email')
        )
        
        # Store in Flask session
        session['session_id'] = session_id
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Session started successfully'
        })
        
    except Exception as e:
        app.logger.error(f"Error starting session: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to start session'
        }), 500

@app.route('/api/sessions/<session_id>/end', methods=['POST'])
def end_session(session_id):
    """
    End a chat session.
    
    Args:
        session_id: Session identifier
    
    Request Body:
        {
            "issue_resolved": true/false
        }
    
    Returns:
        End session result
    """
    try:
        data = request.get_json() or {}
        
        result = db.end_chat_session(
            session_id=session_id,
            issue_resolved=data.get('issue_resolved', False)
        )
        
        return jsonify({
            'success': result,
            'message': 'Session ended' if result else 'Session not found'
        })
        
    except Exception as e:
        app.logger.error(f"Error ending session: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to end session'
        }), 500

@app.route('/api/sessions/<session_id>/history', methods=['GET'])
def get_session_history(session_id):
    """
    Get chat history for a session.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Chat history
    """
    try:
        history = db.get_chat_history(session_id)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'count': len(history),
            'history': history
        })
        
    except Exception as e:
        app.logger.error(f"Error getting session history: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get session history'
        }), 500

# ==================== DIALOGFLOW INTEGRATION ====================

@app.route('/api/dialogflow/webhook', methods=['POST'])
def dialogflow_webhook():
    """
    Dialogflow webhook endpoint for fulfillment.
    
    Returns:
        Dialogflow-compatible response
    """
    try:
        req = request.get_json()
        
        # Extract intent and parameters from Dialogflow request
        intent = req.get('queryResult', {}).get('intent', {}).get('displayName', '')
        parameters = req.get('queryResult', {}).get('parameters', {})
        query_text = req.get('queryResult', {}).get('queryText', '')
        
        app.logger.info(f"Dialogflow webhook - Intent: {intent}, Query: {query_text}")
        
        # Get response from our chatbot
        result = chatbot.get_response(query_text)
        
        # Format response for Dialogflow
        response = {
            'fulfillmentText': result['response'],
            'fulfillmentMessages': [
                {
                    'text': {
                        'text': [result['response']]
                    }
                }
            ],
            'payload': {
                'confidence': result.get('confidence'),
                'category': result.get('category'),
                'escalation_required': result.get('escalation_required', False)
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        app.logger.error(f"Error in Dialogflow webhook: {str(e)}")
        return jsonify({
            'fulfillmentText': 'Sorry, I encountered an error processing your request.'
        })

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    app.logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'success': False,
        'error': 'Method not allowed'
    }), 405

# ==================== MAIN ====================

if __name__ == '__main__':
    print("=" * 60)
    print("AI IT Support Chatbot Server")
    print("=" * 60)
    print("\nStarting server...")
    print("Access the chat interface at: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Run the Flask application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
