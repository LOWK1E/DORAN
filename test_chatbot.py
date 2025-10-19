from chatbot import Chatbot

chatbot = Chatbot()
print('Sample user rules:')
for rule in chatbot.rules[:3]:
    print(f'  {rule["question"]} -> {rule["response"][:50]}...')
print('Sample guest rules:')
for rule in chatbot.guest_rules[:3]:
    print(f'  {rule["question"]} -> {rule["response"][:50]}...')
print('Sample location rules:')
for rule in chatbot.location_rules[:3]:
    print(f'  Keywords: {rule["keywords"]} -> {rule["response"][:50]}...')

print('User rules with SOICT office:')
for rule in chatbot.rules:
    if 'soict' in rule['question'].lower() and 'office' in rule['question'].lower():
        print(f'  {rule["question"]}')
print('Guest rules with SOICT office:')
for rule in chatbot.guest_rules:
    if 'soict' in rule['question'].lower() and 'office' in rule['question'].lower():
        print(f'  {rule["question"]}')
