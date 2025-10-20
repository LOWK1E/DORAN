# TODO: Update Preprocessed Questions Modal

## Steps to Complete:
- [ ] Add preprocessText function in chat.js to preprocess text (lowercase, remove stopwords and punctuation).
- [ ] Change fetch URLs: '/database/preprocessed_guest_rules.json' to '/database/guest_database/all_guest_rules.json', '/database/user_rules.json' to '/database/user_database/all_user_rules.json'.
- [ ] Modify code for guestRules and userRules to set original: rule.question, preprocessed: preprocessText(rule.question).
- [ ] For faqs categorization, push {original: faq.question, preprocessed: preprocessText(faq.question)} instead of the string.
- [ ] For locations, push {original: displayText, preprocessed: preprocessText(displayText)}.
- [ ] Test the modal to ensure all questions from the specified files are displayed as preprocessed.
- [ ] Verify no console errors and modal functionality.
