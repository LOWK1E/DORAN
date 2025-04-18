import logging
import string
import re
from uuid import uuid4

# Simple tokenizer function
def simple_tokenize(text):
    """Split text into tokens by whitespace and punctuation"""
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Split by whitespace
    return text.split()

class Chatbot:
    def __init__(self):
        # Initialize rules list with uuid for identification
        self.rules = []
        self.fallback_responses = [
            "I'm sorry, I don't understand that query. Could you please rephrase?",
            "I don't have information on that topic yet. Please try asking something else.",
            "I couldn't find a match for your query. Please try using different keywords."
        ]
        self.fallback_index = 0
        logging.debug("Chatbot initialized")
    
    def add_rule(self, keywords, response):
        """Add a new rule to the chatbot's knowledge base"""
        rule_id = str(uuid4())
        self.rules.append({
            'id': rule_id,
            'keywords': keywords,
            'response': response
        })
        logging.debug(f"Added rule: {keywords} -> {response}")
        return rule_id
    
    def delete_rule(self, rule_id):
        """Delete a rule by its ID"""
        for i, rule in enumerate(self.rules):
            if rule['id'] == rule_id:
                del self.rules[i]
                logging.debug(f"Deleted rule: {rule_id}")
                return True
        logging.debug(f"Rule not found for deletion: {rule_id}")
        return False
    
    def get_rules(self):
        """Get all current rules"""
        return self.rules
    
    def get_response(self, user_input):
        """Generate a response based on user input and defined rules"""
        if not user_input.strip():
            return "Please type a message to chat with DORAN."
        
        # Preprocess user input
        user_input = user_input.lower()
        tokens = simple_tokenize(user_input)
        
        # Check each rule for keyword matches
        best_match = None
        most_matches = 0
        
        for rule in self.rules:
            matches = sum(1 for keyword in rule['keywords'] if keyword in tokens)
            match_ratio = matches / len(rule['keywords'])
            
            # Consider it a match if all keywords are present
            if match_ratio == 1.0:
                return rule['response']
            
            # Keep track of the best partial match (most keywords matched)
            if matches > most_matches and matches >= 1:
                most_matches = matches
                best_match = rule
        
        # Return best partial match if it exists and has at least 2 keywords or more than 50% match
        if best_match and (most_matches >= 2 or most_matches / len(best_match['keywords']) > 0.5):
            return best_match['response']
        
        # Return fallback response if no match found
        fallback = self.fallback_responses[self.fallback_index]
        self.fallback_index = (self.fallback_index + 1) % len(self.fallback_responses)
        return fallback
