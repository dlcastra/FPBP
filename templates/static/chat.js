$(document).ready(function () {
    const chatId = $('#chat_id').val();
    const socket = new WebSocket(`ws://${window.location.host}/ws/chat/${chatId}/`);

    socket.onopen = function () {
        console.log("WebSocket connection established.");
    };

    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);

        if (data.type === 'chat_message') {
            displayMessage(data.message);
        } else if (data.type === 'delete_message') {
            removeMessage(data.message_id);
        }
    };

    socket.onclose = function () {
        console.log("WebSocket connection closed.");
    };

    socket.onerror = function (error) {
        console.error("WebSocket error observed:", error);
    };

    $('.messageForm').on('submit', async function (event) {
        event.preventDefault();

        const form = $(this);
        const chatId = form.data('chat-id');
        const userId = $(`#user_id_${chatId}`).val();
        const recipient = $(`#recipient_id_${chatId}`).val();
        const sender = $(`#sender_id_${chatId}`).val();
        const context = $(`#context_${chatId}`).val().trim();
        const fileInput = $(`#file_${chatId}`)[0];
        const voiceInput = $(`#voice_${chatId}`)[0];

        if (!chatId || !userId || !recipient || !sender || !context) {
            console.error("Missing required fields:", {chatId, userId, recipient, sender, context});
            return;
        }

        const fileBase64 = fileInput.files[0] ? await fileToBase64(fileInput.files[0]) : null;
        const voiceBase64 = voiceInput.files[0] ? await fileToBase64(voiceInput.files[0]) : null;

        const message = {
            type: 'chat_message',
            username: $('#username').val(),
            user_id: userId,
            recipient: recipient,
            sender: sender,
            context: context,
            chatId: chatId,
            file: fileBase64,
            voice: voiceBase64,
        };

        console.log("Sending message:", message);



        socket.send(JSON.stringify(message));
        form[0].reset();
    });

    async function fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
        });
    }

    function displayMessage(message) {
        if (!message || !message.context) {
            console.error("Invalid message data", message);
            return;
        }

        console.log("Displaying message:", message);

        const messageDiv = $(`#message_container_${message.chatId}`);
        const messageClass = (message.userId === message.sender) ? 'sent' : 'received';
        const commentElement = $(`
        <div class="message ${messageClass}" data-message-id="${message.message_id}">
            <h5>${message.username}</h5>
            <p>${message.context}</p>
            ${message.file ? `<img src="${message.file}" alt="Image"/>` : ''}
            ${message.voice ? `<audio controls src="${message.voice}"></audio>` : ''}
            ${message.userId === message.sender ? '<button class="delete-message-btn" data-message-id="' + message.message_id + '">Delete</button>' : ''}
        </div>
    `);

        messageDiv.append(commentElement);
        messageDiv.scrollTop(messageDiv.prop("scrollHeight"));
    }


    function deleteMessage(messageId) {
        const userId = $(`#user_id_${chatId}`).val();
        const message = {
            type: 'delete_message',
            message_id: messageId,
            user_id: userId,
        };
        socket.send(JSON.stringify(message));
    }

    function removeMessage(messageId) {
        $(`.message[data-message-id="${messageId}"]`).remove();
    }

    $(document).on('click', '.delete-message-btn', function () {
        const messageId = $(this).data('message-id');
        deleteMessage(messageId);
    });
});
