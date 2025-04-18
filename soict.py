"""
SOICT Knowledge Base
-------------------
This file contains all the keyword-based rules for the DORAN chatbot.
Rules are organized with keywords and their corresponding responses.
"""

# Dictionary of SOICT-related rules
# Each rule contains keywords (list) and their corresponding response (string)
RULES = [
    {
        "keywords": ["soict", "office", "hour"],
        "response": "SOICT office hours are from 8:00 AM to 5:00 PM, Monday to Friday."
    },
    {
        "keywords": ["where", "soict", "office"],
        "response": "The SOICT office is located in Building C1, 2nd floor."
    },
    {
        "keywords": ["dean", "soict"],
        "response": "The current Dean of SOICT is Prof. Dr. Nguyen Thanh Thuy."
    },
    {
        "keywords": ["courses", "offered"],
        "response": "SOICT offers various courses including Computer Science, Information Systems, and Software Engineering."
    },
    {
        "keywords": ["admission", "requirements"],
        "response": "Admission requirements include a high school diploma and passing the entrance exam."
    },
    {
        "keywords": ["contact", "information"],
        "response": "You can contact SOICT via email at soict@example.com or phone at +123-456-7890."
    },
    {
        "keywords": ["hello", "hi"],
        "response": "Hello! I'm DORAN, a chatbot designed to help you with SOICT-related queries."
    },
    {
        "keywords": ["thank", "thanks"],
        "response": "You're welcome! Is there anything else I can help you with?"
    },
    {
        "keywords": ["bye", "goodbye"],
        "response": "Goodbye! Feel free to come back if you have more questions."
    },
    {
        "keywords": ["faculty", "staff", "professors"],
        "response": "SOICT has over 50 faculty members, including professors, associate professors, and lecturers."
    },
    {
        "keywords": ["research", "areas", "focus"],
        "response": "SOICT's research areas include AI, Machine Learning, Data Science, IoT, Cybersecurity, and Software Engineering."
    },
    {
        "keywords": ["laboratories", "labs", "facilities"],
        "response": "SOICT has several modern laboratories for AI, IoT, Networks, and Software Engineering research and education."
    },
    {
        "keywords": ["academic", "calendar", "schedule"],
        "response": "The academic calendar typically includes two main semesters and one summer term. Please check the university website for specific dates."
    },
    {
        "keywords": ["tuition", "fees"],
        "response": "Tuition fees depend on the program and student status. Please check the university's finance department for current rates."
    },
    {
        "keywords": ["scholarships", "financial", "aid"],
        "response": "SOICT offers various scholarships based on academic achievement and financial need. Applications are typically due at the beginning of each semester."
    }
]

# Helper function to get all rules
def get_all_rules():
    """Return all rules in the knowledge base with added IDs"""
    return [{"id": idx, "keywords": rule["keywords"], "response": rule["response"]} 
            for idx, rule in enumerate(RULES)]

# Helper function to get a rule by its ID
def get_rule_by_id(rule_id):
    """Return a specific rule by its ID"""
    rule_id = int(rule_id)
    if 0 <= rule_id < len(RULES):
        return {
            "id": rule_id,
            "keywords": RULES[rule_id]["keywords"],
            "response": RULES[rule_id]["response"]
        }
    return None

# Helper function to add a new rule
def add_rule(keywords, response):
    """Add a new rule to the knowledge base"""
    RULES.append({"keywords": keywords, "response": response})
    return len(RULES) - 1  # Return the ID of the new rule

# Helper function to delete a rule by its ID
def delete_rule(rule_id):
    """Delete a rule from the knowledge base by its ID"""
    rule_id = int(rule_id)
    if 0 <= rule_id < len(RULES):
        RULES.pop(rule_id)
        return True
    return False