"""
AI IT Support Chatbot Engine
============================
Rule-Based AI with Pattern Matching
This module implements the core chatbot intelligence using:
- Keyword matching
- Regular expressions
- NLP preprocessing
- Confidence scoring
"""

import json
import re
import random
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
import os

class ITSupportChatbot:
    """
    Rule-Based Chatbot Engine for IT Support
    
    This class implements pattern matching algorithms to identify user issues
    and provide appropriate troubleshooting responses.
    """
    
    def __init__(self, rules_file: str = "rules.json"):
        """
        Initialize the chatbot with rules from JSON file.
        
        Args:
            rules_file: Path to the JSON file containing chatbot rules
        """
        self.rules_file = rules_file
        self.rules = []
        self.fallback_responses = []
        self.confidence_threshold = 0.6
        self.load_rules()
        
    def load_rules(self) -> None:
        """Load rules and fallback responses from JSON file."""
        try:
            # Get the absolute path to the rules file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            rules_path = os.path.join(script_dir, self.rules_file)
            
            with open(rules_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.rules = data.get('rules', [])
                self.fallback_responses = data.get('fallback_responses', [
                    "I'm not sure I understand. Could you rephrase that?"
                ])
            print(f"✓ Loaded {len(self.rules)} rules and {len(self.fallback_responses)} fallback responses")
        except FileNotFoundError:
            print(f"✗ Rules file not found: {self.rules_file}")
            self.rules = []
            self.fallback_responses = ["I'm having trouble accessing my knowledge base."]
        except json.JSONDecodeError:
            print(f"✗ Invalid JSON in rules file: {self.rules_file}")
            self.rules = []
            self.fallback_responses = ["I'm having trouble accessing my knowledge base."]
    
    def preprocess_input(self, user_input: str) -> str:
        """
        Preprocess user input for better matching.
        
        Steps:
        1. Convert to lowercase
        2. Remove extra whitespace
        3. Remove special characters (keep basic punctuation)
        
        Args:
            user_input: Raw user input string
            
        Returns:
            Preprocessed string
        """
        # Convert to lowercase
        processed = user_input.lower()
        
        # Remove extra whitespace and strip
        processed = ' '.join(processed.split())
        
        # Remove special characters but keep alphanumeric and basic punctuation
        processed = re.sub(r'[^\w\s.,!?-]', '', processed)
        
        return processed.strip()
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using SequenceMatcher.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity ratio between 0 and 1
        """
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def match_pattern(self, user_input: str, pattern: str) -> float:
        """
        Match user input against a pattern using multiple techniques.
        
        Techniques:
        1. Exact match
        2. Substring match
        3. Word boundary match
        4. Similarity scoring
        
        Args:
            user_input: Preprocessed user input
            pattern: Pattern to match against
            
        Returns:
            Match score between 0 and 1
        """
        user_lower = user_input.lower()
        pattern_lower = pattern.lower()
        
        # Exact match (highest confidence)
        if user_lower == pattern_lower:
            return 1.0
        
        # Substring match - pattern contained in input
        if pattern_lower in user_lower:
            # Higher score for longer pattern matches
            return 0.8 + (len(pattern_lower) / len(user_lower)) * 0.1
        
        # Input contained in pattern
        if user_lower in pattern_lower:
            return 0.7
        
        # Word boundary matching - check if all words in pattern are in input
        pattern_words = set(pattern_lower.split())
        user_words = set(user_lower.split())
        
        if pattern_words and pattern_words.issubset(user_words):
            return 0.75
        
        # Partial word matching
        common_words = pattern_words.intersection(user_words)
        if common_words:
            return 0.5 + (len(common_words) / len(pattern_words)) * 0.2
        
        # Similarity matching using SequenceMatcher
        similarity = self.calculate_similarity(user_input, pattern)
        if similarity > 0.6:
            return similarity * 0.7
        
        return 0.0
    
    def keyword_match(self, user_input: str, keywords: List[str]) -> float:
        """
        Match keywords in user input.
        
        Args:
            user_input: Preprocessed user input
            keywords: List of keywords to match
            
        Returns:
            Keyword match score between 0 and 1
        """
        user_lower = user_input.lower()
        user_words = set(user_lower.split())
        
        matched_keywords = 0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Check for exact word match or substring match
            if keyword_lower in user_lower or any(keyword_lower in word for word in user_words):
                matched_keywords += 1
        
        if not keywords:
            return 0.0
            
        return matched_keywords / len(keywords)
    
    def find_best_match(self, user_input: str) -> Tuple[Optional[Dict], float]:
        """
        Find the best matching rule for user input.
        
        Args:
            user_input: Raw user input
            
        Returns:
            Tuple of (best matching rule dict, confidence score)
        """
        processed_input = self.preprocess_input(user_input)
        
        if not processed_input:
            return None, 0.0
        
        best_rule = None
        best_score = 0.0
        
        for rule in self.rules:
            rule_score = 0.0
            
            # Check patterns
            pattern_scores = []
            for pattern in rule.get('patterns', []):
                score = self.match_pattern(processed_input, pattern)
                if score > 0:
                    pattern_scores.append(score)
            
            if pattern_scores:
                # Use the highest pattern match score
                rule_score = max(pattern_scores)
            
            # Also check keywords for additional scoring
            keyword_score = self.keyword_match(processed_input, rule.get('keywords', []))
            
            # Combine scores (pattern match weighted higher)
            combined_score = max(rule_score, keyword_score * 0.8)
            
            # Boost score if both pattern and keywords match
            if rule_score > 0 and keyword_score > 0:
                combined_score = min(1.0, combined_score + 0.1)
            
            if combined_score > best_score:
                best_score = combined_score
                best_rule = rule
        
        return best_rule, best_score
    
    def get_response(self, user_input: str) -> Dict:
        """
        Get response for user input.
        
        Args:
            user_input: User's message
            
        Returns:
            Dictionary containing response data
        """
        # Handle empty input
        if not user_input or not user_input.strip():
            return {
                'response': "I didn't receive any message. How can I help you today?",
                'confidence': 0.0,
                'category': 'Empty Input',
                'rule_id': None,
                'escalation_required': False
            }
        
        # Find best matching rule
        best_rule, confidence = self.find_best_match(user_input)
        
        # If confidence is above threshold, return the rule's response
        if confidence >= self.confidence_threshold and best_rule:
            return {
                'response': best_rule['response'],
                'confidence': round(confidence, 2),
                'category': best_rule.get('category', 'Unknown'),
                'rule_id': best_rule.get('id'),
                'escalation_required': best_rule.get('escalation_required', False)
            }
        
        # Check if user wants to create a ticket
        ticket_keywords = ['ticket', 'support', 'agent', 'human', 'escalate', 'helpdesk']
        if any(keyword in user_input.lower() for keyword in ticket_keywords):
            return {
                'response': "I'll help you create a support ticket. Please provide:\n\n1. Your full name\n2. Your email address\n3. Detailed description of the issue\n\nOr fill out the ticket form below.",
                'confidence': 0.9,
                'category': 'Ticket Creation',
                'rule_id': None,
                'escalation_required': True
            }
        
        # Return fallback response for unknown queries
        fallback = random.choice(self.fallback_responses)
        return {
            'response': fallback,
            'confidence': round(confidence, 2),
            'category': 'Unknown',
            'rule_id': None,
            'escalation_required': False
        }
    
    def get_suggestions(self, user_input: str, max_suggestions: int = 3) -> List[str]:
        """
        Get suggested categories based on partial input.
        
        Args:
            user_input: Partial user input
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of suggested category names
        """
        processed_input = self.preprocess_input(user_input)
        
        if len(processed_input) < 2:
            return []
        
        suggestions = []
        for rule in self.rules:
            # Check if any pattern starts with the input
            for pattern in rule.get('patterns', []):
                if pattern.lower().startswith(processed_input.lower()):
                    category = rule.get('category', '')
                    if category and category not in suggestions:
                        suggestions.append(category)
                        break
            
            if len(suggestions) >= max_suggestions:
                break
        
        return suggestions
    
    def get_all_categories(self) -> List[str]:
        """
        Get all unique categories from rules.
        
        Returns:
            List of category names
        """
        categories = set()
        for rule in self.rules:
            category = rule.get('category', '')
            if category and category not in ['Greeting', 'Goodbye', 'Create Ticket']:
                categories.add(category)
        return sorted(list(categories))
    
    def reload_rules(self) -> bool:
        """
        Reload rules from file (useful for hot-updating).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.load_rules()
            return True
        except Exception as e:
            print(f"Error reloading rules: {e}")
            return False


# Dialogflow Integration Class
class DialogflowIntegration:
    """
    Dialogflow Integration for Advanced NLP
    
    This class provides integration with Google Dialogflow for
    enhanced natural language understanding.
    """
    
    def __init__(self, project_id: str = None, session_id: str = None):
        """
        Initialize Dialogflow integration.
        
        Args:
            project_id: Google Cloud project ID
            session_id: Session ID for the conversation
        """
        self.project_id = project_id
        self.session_id = session_id
        self.enabled = False
        
        # Try to import dialogflow
        try:
            from google.cloud import dialogflow_v2 as dialogflow
            self.dialogflow = dialogflow
            self.enabled = project_id is not None
        except ImportError:
            print("Dialogflow not installed. Run: pip install google-cloud-dialogflow")
            self.dialogflow = None
    
    def detect_intent(self, text: str, language_code: str = 'en') -> Dict:
        """
        Detect intent using Dialogflow.
        
        Args:
            text: User input text
            language_code: Language code (default: 'en')
            
        Returns:
            Dictionary with intent detection results
        """
        if not self.enabled or not self.dialogflow:
            return {
                'intent': None,
                'confidence': 0.0,
                'fulfillment_text': None,
                'parameters': {}
            }
        
        try:
            session_client = self.dialogflow.SessionsClient()
            session = session_client.session_path(self.project_id, self.session_id)
            
            text_input = self.dialogflow.TextInput(text=text, language_code=language_code)
            query_input = self.dialogflow.QueryInput(text=text_input)
            
            response = session_client.detect_intent(
                request={"session": session, "query_input": query_input}
            )
            
            return {
                'intent': response.query_result.intent.display_name,
                'confidence': response.query_result.intent_detection_confidence,
                'fulfillment_text': response.query_result.fulfillment_text,
                'parameters': dict(response.query_result.parameters)
            }
        except Exception as e:
            print(f"Dialogflow error: {e}")
            return {
                'intent': None,
                'confidence': 0.0,
                'fulfillment_text': None,
                'parameters': {}
            }


# Hybrid Chatbot Engine (Rule-Based + Dialogflow)
class HybridChatbotEngine:
    """
    Hybrid Chatbot Engine combining Rule-Based AI with Dialogflow
    
    Uses rule-based matching as primary method with Dialogflow
    as fallback for complex queries.
    """
    
    def __init__(self, rules_file: str = "rules.json", dialogflow_project_id: str = None):
        """
        Initialize hybrid chatbot engine.
        
        Args:
            rules_file: Path to rules JSON file
            dialogflow_project_id: Google Cloud project ID (optional)
        """
        self.rule_engine = ITSupportChatbot(rules_file)
        self.dialogflow = DialogflowIntegration(dialogflow_project_id)
        self.use_dialogflow_threshold = 0.5
    
    def get_response(self, user_input: str) -> Dict:
        """
        Get response using hybrid approach.
        
        Args:
            user_input: User's message
            
        Returns:
            Dictionary containing response data
        """
        # First, try rule-based matching
        rule_result = self.rule_engine.get_response(user_input)
        
        # If confidence is high enough, use rule-based response
        if rule_result['confidence'] >= self.use_dialogflow_threshold:
            return rule_result
        
        # Otherwise, try Dialogflow
        if self.dialogflow.enabled:
            dialogflow_result = self.dialogflow.detect_intent(user_input)
            
            if dialogflow_result['confidence'] > rule_result['confidence']:
                return {
                    'response': dialogflow_result['fulfillment_text'] or rule_result['response'],
                    'confidence': dialogflow_result['confidence'],
                    'category': dialogflow_result['intent'] or rule_result['category'],
                    'rule_id': None,
                    'escalation_required': False,
                    'source': 'dialogflow'
                }
        
        # Return rule-based result if Dialogflow not available or lower confidence
        return rule_result


# Testing function
if __name__ == "__main__":
    # Test the chatbot engine
    print("=" * 60)
    print("IT Support Chatbot Engine - Test Mode")
    print("=" * 60)
    
    chatbot = ITSupportChatbot()
    
    test_inputs = [
        "Hello",
        "My internet is not working",
        "I forgot my password",
        "Printer is offline",
        "My computer is running very slow today",
        "Blue screen error on my laptop",
        "Cannot connect to VPN",
        "This is a random query that doesn't match anything",
        "Thanks, bye!"
    ]
    
    print("\nTesting chatbot responses:\n")
    for user_input in test_inputs:
        result = chatbot.get_response(user_input)
        print(f"User: {user_input}")
        print(f"Bot: {result['response'][:100]}...")
        print(f"Category: {result['category']} | Confidence: {result['confidence']}")
        print("-" * 60)
