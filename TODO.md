# TODO: Implement Add, Edit, Delete Rules in Admin Panel

## Completed Tasks
- [x] Add edit_rule method to chatbot.py to modify JSON files for user/guest rules
- [x] Add delete_rule method to chatbot.py to remove rules from JSON files
- [x] Add /add_rule route to app.py that calls chatbot.add_rule
- [x] Add /edit_rule route to app.py that calls chatbot.edit_rule
- [x] Add /delete_rule route to app.py that calls chatbot.delete_rule

## Followup Steps
- [ ] Test the routes by running the app and using the admin panel to add, edit, and delete rules
- [ ] Verify that rules are correctly saved to all_user_rules.json and all_guest_rules.json
- [ ] Ensure embeddings are recomputed after edits/deletes for semantic matching
