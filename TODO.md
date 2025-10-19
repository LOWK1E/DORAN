# TODO: Add Notification Badges to Admin Dashboard

## Tasks
- [x] Modify `/admin` route in `app.py` to fetch and pass pending counts for accounts and feedback
- [x] Update `htdocs/admin_dashboard.html` to display badges on "Manage Accounts" and "Manage Feedback" cards
- [x] Add CSS styles for the notification badges in `static/css/admin.css`
- [x] Test the implementation to ensure badges appear correctly when there are pending items

# TODO: Add User Type Selection to Admin Forms

## Tasks
- [x] Add user type dropdown to admin_visuals.html form
- [x] Add user type dropdown to admin_locations.html form
- [x] Update admin_visuals.js to include user_type in form submission
- [x] Update admin_locations.js to include user_type in form submission
- [x] Update backend routes to handle user_type parameter for visuals and locations
- [x] Update database models to include user_type field for visuals and locations
- [x] Test the user type filtering in chatbot responses
