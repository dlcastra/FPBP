$(document).ready(function () {
    var csrftoken = $('meta[name="csrf-token"]').attr('content');

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    $(document).on('submit', '.banForm', function (event) {
        event.preventDefault();
        let action = $(this).data("action");
        let reason = prompt("Ban reason");

        if (reason && reason.length >= 50) {
            const followerId = $(this).find('input').data('follower-id');
            const instance = $(this).find('input').data('instance');
            $.ajax({
                type: 'POST',
                url: `/community/name-${instance}/admin-panel/users-management/`,
                data: JSON.stringify({
                    follower_id: followerId,
                    reason: reason,
                    instance: instance,
                    action: action
                }),
                contentType: 'application/json',
                success: function (response) {
                    if (response.status === "success") {
                        alert("User banned successfully");
                        window.location.reload();
                    } else {
                        alert("Error: " + response.message);
                    }
                },
                error: function (xhr, status, error) {
                    alert("Error banning user: " + xhr.responseText);
                }
            });
        } else {
            alert("Reason must be at least 50 characters long");
        }
    });

    $(document).on('submit', '.blackListForm', function (event) {
        event.preventDefault();
        let action = $(this).data("action");
        const instance = $(this).find('input').data('instance');
        const bannedUserId = $(this).find('input').data('banned-user-id');

        $.ajax({
            type: 'POST',
            url: `/community/name-${instance}/admin-panel/users-management/`,
            data: JSON.stringify({
                action: action,
                bannedUserId: bannedUserId,
            }),
            contentType: 'application/json',
            success: function (response) {
                if (response.status === 'success') {
                    $(`#banned_user_${bannedUserId}`).closest('tr').remove();
                } else {
                    alert(response.message || 'An error occurred');
                }
            },
            error: function () {
                alert('An error occurred');
            }
        });
    });
});