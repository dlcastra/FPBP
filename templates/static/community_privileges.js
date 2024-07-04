$(document).ready(function () {
    var csrftoken = $('meta[name="csrf-token"]').attr('content');

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    $(document).on('click', '.grant-btn', function (event) {
        event.preventDefault();
        const followerId = $(this).data('follower-id');
        const instance = $(this).data('instance');

        // Store the data in the modal for later use
        $('#privilegesModal').data('follower-id', followerId);
        $('#privilegesModal').data('instance', instance);

        // Show the modal
        $('#privilegesModal').show();
    });

    $(document).on('click', '#submitPrivileges', function (event) {
        event.preventDefault();
        const privilege = $('input[name="privilege"]:checked').val();
        const followerId = $('#privilegesModal').data('follower-id');
        const instance = $('#privilegesModal').data('instance');

        if (privilege) {
            $.ajax({
                type: 'POST',
                url: `/community/name-${instance}/admin-panel/users-management/`,
                data: JSON.stringify({
                    follower_id: followerId,
                    privilege: privilege,
                    instance: instance,
                    action: 'grant_privileges'
                }),
                contentType: 'application/json',
                success: function (response) {
                    if (response.status === "success") {
                        alert("Privileges granted successfully");
                        window.location.reload();
                    } else {
                        alert("Error: " + response.message);
                    }
                },
                error: function (xhr, status, error) {
                    alert("Error granting privileges: " + xhr.responseText);
                }
            });
            $('#privilegesModal').hide();
        } else {
            alert("Please select a privilege");
        }
    });

    // Optional: Hide the modal when clicking outside of it
    $(window).on('click', function (event) {
        if ($(event.target).is('#privilegesModal')) {
            $('#privilegesModal').hide();
        }
    });
});
