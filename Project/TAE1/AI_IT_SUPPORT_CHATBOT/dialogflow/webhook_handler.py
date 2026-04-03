"""
Dialogflow Webhook Handler
==========================
Handles Dialogflow fulfillment requests and integrates with the rule-based chatbot.

This module provides:
- Webhook endpoint for Dialogflow fulfillment
- Intent handling and response formatting
- Integration with the main chatbot engine
"""

import json
from flask import Blueprint, request, jsonify
from chatbot_engine import ITSupportChatbot

# Initialize chatbot
chatbot = ITSupportChatbot('rules.json')

# Create Blueprint
dialogflow_bp = Blueprint('dialogflow', __name__)


def format_dialogflow_response(text, session_info=None, payload=None):
    """
    Format response for Dialogflow.
    
    Args:
        text: Response text
        session_info: Optional session information
        payload: Optional custom payload
        
    Returns:
        Dialogflow-compatible response dict
    """
    response = {
        'fulfillmentText': text,
        'fulfillmentMessages': [
            {
                'text': {
                    'text': [text]
                }
            }
        ]
    }
    
    if payload:
        response['payload'] = {
            'google': payload,
            'slack': payload,
            'facebook': payload
        }
    
    return response


@dialogflow_bp.route('/webhook', methods=['POST'])
def webhook():
    """
    Main Dialogflow webhook endpoint.
    
    Receives webhook requests from Dialogflow and returns
    appropriate fulfillment responses.
    
    Returns:
        JSON response for Dialogflow
    """
    try:
        # Parse request
        req = request.get_json(silent=True, force=True)
        
        # Extract key information
        query_result = req.get('queryResult', {})
        session = req.get('session', '')
        
        intent = query_result.get('intent', {}).get('displayName', '')
        parameters = query_result.get('parameters', {})
        query_text = query_result.get('queryText', '')
        
        print(f"Dialogflow Request - Intent: {intent}, Query: {query_text}")
        
        # Handle specific intents
        if intent == 'Default Welcome Intent':
            return handle_welcome_intent()
        
        elif intent == 'Create Support Ticket':
            return handle_create_ticket_intent(parameters)
        
        elif intent == 'Default Fallback Intent':
            return handle_fallback_intent(query_text)
        
        else:
            # For all other intents, use the rule-based chatbot
            return handle_rule_based_intent(query_text)
            
    except Exception as e:
        print(f"Error in webhook: {e}")
        return jsonify(format_dialogflow_response(
            "I'm sorry, I encountered an error processing your request. Please try again."
        ))


def handle_welcome_intent():
    """Handle welcome/greeting intent."""
    welcome_messages = [
        "Hello! I'm your IT Support Assistant. I can help you with internet issues, password resets, printer problems, and more. What can I assist you with today?",
        "Hi there! Welcome to IT Support. I'm here to help resolve your technical issues. Please describe your problem.",
        "Greetings! I'm your IT Support Bot. I can troubleshoot common IT problems. What issue are you experiencing?"
    ]
    
    import random
    message = random.choice(welcome_messages)
    
    return jsonify(format_dialogflow_response(message))


def handle_create_ticket_intent(parameters):
    """
    Handle ticket creation intent.
    
    Args:
        parameters: Dialogflow parameters
    """
    name = parameters.get('name', '')
    email = parameters.get('email', '')
    
    if name and email:
        message = f"Thank you {name}! I'll create a support ticket for you. Our IT team will contact you at {email} within 24 hours. Your ticket reference will be sent to your email."
    else:
        message = "I'll help you create a support ticket. Please provide your name and email address so our IT team can contact you."
    
    return jsonify(format_dialogflow_response(message))


def handle_fallback_intent(query_text):
    """
    Handle fallback intent when no other intent matches.
    
    Args:
        query_text: Original user query
    """
    # Try rule-based matching
    result = chatbot.get_response(query_text)
    
    return jsonify(format_dialogflow_response(
        result['response'],
        payload={
            'confidence': result.get('confidence'),
            'category': result.get('category'),
            'escalation_required': result.get('escalation_required', False)
        }
    ))


def handle_rule_based_intent(query_text):
    """
    Handle intent using rule-based chatbot.
    
    Args:
        query_text: User query text
    """
    result = chatbot.get_response(query_text)
    
    return jsonify(format_dialogflow_response(
        result['response'],
        payload={
            'confidence': result.get('confidence'),
            'category': result.get('category'),
            'escalation_required': result.get('escalation_required', False)
        }
    ))


# ==================== ENTITY CONFIGURATION ====================

ENTITIES_CONFIG = {
    "issue_type": {
        "entities": [
            {"value": "internet", "synonyms": ["wifi", "network", "connection", "online"]},
            {"value": "password", "synonyms": ["login", "account", "credentials", "forgot password"]},
            {"value": "printer", "synonyms": ["print", "printing", "paper jam"]},
            {"value": "software", "synonyms": ["application", "program", "install", "app"]},
            {"value": "hardware", "synonyms": ["computer", "laptop", "desktop", "device"]},
            {"value": "email", "synonyms": ["outlook", "mail", "mailbox"]},
            {"value": "vpn", "synonyms": ["remote access", "tunnel", "secure connection"]},
            {"value": "virus", "synonyms": ["malware", "security", "threat", "infection"]}
        ]
    },
    "priority_level": {
        "entities": [
            {"value": "low", "synonyms": ["minor", "not urgent", "can wait"]},
            {"value": "medium", "synonyms": ["normal", "standard", "moderate"]},
            {"value": "high", "synonyms": ["urgent", "important", "critical for work"]},
            {"value": "critical", "synonyms": ["emergency", "down", "not working at all", "blocking"]}
        ]
    }
}


def get_entity_config():
    """Get Dialogflow entity configuration."""
    return ENTITIES_CONFIG


# ==================== TESTING ====================

if __name__ == "__main__":
    print("=" * 60)
    print("Dialogflow Webhook Handler - Test Mode")
    print("=" * 60)
    
    # Test webhook handling
    test_requests = [
        {
            "queryResult": {
                "intent": {"displayName": "Default Welcome Intent"},
                "queryText": "Hello"
            },
            "session": "test-session-001"
        },
        {
            "queryResult": {
                "intent": {"displayName": "Internet Not Working"},
                "queryText": "My internet is not working"
            },
            "session": "test-session-002"
        },
        {
            "queryResult": {
                "intent": {"displayName": "Default Fallback Intent"},
                "queryText": "Something random"
            },
            "session": "test-session-003"
        }
    ]
    
    with open('intents.json', 'r') as f:
        intents = json.load(f)
    
    print(f"\nLoaded {len(intents['intents'])} intents from configuration")
    print("\nIntent List:")
    for intent in intents['intents']:
        print(f"  - {intent['displayName']}")
    
    print("\n✓ Dialogflow webhook handler ready")
