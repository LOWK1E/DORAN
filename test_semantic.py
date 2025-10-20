from chatbot import Chatbot

chatbot = Chatbot()
print('Testing semantic similarity for guest rules:')
test_queries = ['Where is SOICT office?', 'Tell me about SOICT office location', 'SOICT office hours']
for query in test_queries:
    response = chatbot.get_response(query, user_role='guest')
    print(f'Query: {query} -> Response: {response[:100]}...')
