$(document).ready(function () {
    const csrfToken = $('meta[name="csrf-token"]').attr('content');

    if (!csrfToken) {
        console.error("CSRF token not found in meta tag");
        return;
    }

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrfToken);

            }
        }
    });

    const notificationButton = $('#notification-button');
    const notificationList = $('#notification-list');
    const notificationCountSpan = $('#notification-count');

    const socket = new WebSocket('ws://' + window.location.host + '/ws/notify/');

    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        if (data.message) {
            const notificationElement = $('<li>')
                .html(data.message)
                .attr('data-id', data.id);

            if (!data.is_read) {
                const markReadButton = $('<button>')
                    .text('Mark as Read')
                    .addClass('mark-read-button');

                notificationElement.append(markReadButton);
            }

            notificationList.append(notificationElement);
            notificationCountSpan.text(notificationList.children().length);
        }
    };

    socket.onclose = function () {
        console.error('WebSocket closed unexpectedly');
    };

    notificationButton.on('click', function () {
        notificationList.toggle();
    });

    notificationList.on('click', '.mark-read-button', function () {
        const notificationElement = $(this).closest('li');
        const notificationId = notificationElement.attr('data-id');

        $.ajax({
            url: window.location.href,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            data: JSON.stringify({mark_read: true, id: notificationId}),
            success: function (data) {
                if (data.status === 'ok') {
                    notificationElement.remove();
                    notificationCountSpan.text(notificationList.children().length);
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.error('There was a problem with the AJAX request:', textStatus, errorThrown);
                console.error('Response text:', jqXHR.responseText);
                console.error('Status:', jqXHR.status);
            }
        });
    });

    $('#mark-read-all-btn').click(function () {
        $.ajax({
            url: window.location.href,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            data: JSON.stringify({mark_read_all: true}),
            success: function (data) {
                if (data.status === 'ok') {
                    notificationList.empty();
                    notificationCountSpan.text(0);
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.error('There was a problem with the AJAX request:', textStatus, errorThrown);
                console.error('Response text:', jqXHR.responseText);
                console.error('Status:', jqXHR.status);
            }
        });
    });
});
