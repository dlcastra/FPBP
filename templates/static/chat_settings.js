$(document).ready(function() {
    // Attach a click event handler to the button
    $('#block_user_btn').on('click', function() {
        // Get the action from the button's data attribute
        var action = $(this).data('action');

        // Determine the new action for the button
        var newAction = (action === 'block_user') ? 'unblock_user' : 'block_user';
        $(this).data('action', newAction); // Update the button's action

        // Prepare the data to send with the POST request
        var postData = {
            action: newAction
        };

        // Send an AJAX POST request to the server
        $.ajax({
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(postData),
            headers: {
                'X-CSRFToken': getCookie('csrftoken') // Include CSRF token for security
            },
            success: function(response) {
                if (response.status === 'success') {
                    // Update button text based on action
                    if (newAction === 'block_user') {
                        $('#block_user_btn').text('Unblock user');
                    } else {
                        $('#block_user_btn').text('Block user');
                    }
                } else {
                    console.error('Error:', response.message);
                }
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
            }
        });
    });

    // Function to get the CSRF token from cookies
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
