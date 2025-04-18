document.addEventListener('DOMContentLoaded', function() {
    const addRuleForm = document.getElementById('add-rule-form');
    const keywordsInput = document.getElementById('keywords');
    const responseInput = document.getElementById('response');
    const rulesTable = document.getElementById('rules-table');
    
    // Function to get CSRF token from meta tag
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }
    
    // Add new rule
    addRuleForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const keywords = keywordsInput.value.trim();
        const response = responseInput.value.trim();
        
        if (!keywords || !response) {
            alert('Please enter both keywords and response');
            return;
        }
        
        try {
            const result = await fetch('/add_rule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    keywords,
                    response
                }),
            });
            
            const data = await result.json();
            
            if (data.status === 'success') {
                // Refresh the page to see the updated rules
                location.reload();
            } else {
                alert(data.message || 'Failed to add rule');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        }
    });
    
    // Delete rule
    const deleteButtons = document.querySelectorAll('.delete-rule');
    deleteButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const ruleId = this.getAttribute('data-rule-id');
            
            if (confirm('Are you sure you want to delete this rule?')) {
                try {
                    const result = await fetch('/delete_rule', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        body: JSON.stringify({
                            rule_id: ruleId
                        }),
                    });
                    
                    const data = await result.json();
                    
                    if (data.status === 'success') {
                        // Remove the row from the table
                        const row = this.closest('tr');
                        row.remove();
                        
                        // If no rules left, show empty message
                        if (rulesTable.querySelectorAll('tbody tr').length === 0) {
                            const emptyRow = document.createElement('tr');
                            emptyRow.innerHTML = '<td colspan="3" class="text-center">No rules defined yet.</td>';
                            rulesTable.querySelector('tbody').appendChild(emptyRow);
                        }
                    } else {
                        alert(data.message || 'Failed to delete rule');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('An error occurred. Please try again.');
                }
            }
        });
    });
});
