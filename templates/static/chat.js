$(document).ready(function () {

    const socket = new WebSocket(`ws://${window.location.host}/ws/message/`);

    socket.onopen = function () {
        console.log("WebSocket connection established.");
    };

    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        if (data.message) {
            displayMessage(data.message);
        }
    };

    socket.onclose = function () {
        console.log("WebSocket connection closed.");
    };

    // Handle form submission
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

        // Log file input data to ensure it's being accessed correctly
        console.log('File Input:', fileInput.files[0]);
        console.log('Voice Input:', voiceInput.files[0]);

        // Check if required fields are present
        if (!chatId || !userId || !recipient || !sender || !context) {
            console.error("Missing required fields:", {
                chatId, userId, recipient, sender, context
            });
            return;
        }

        // Handle files and convert to base64 if present
        const fileBase64 = fileInput.files[0] ? await fileToBase64(fileInput.files[0]) : null;
        const voiceBase64 = voiceInput.files[0] ? await fileToBase64(voiceInput.files[0]) : null;

        const message = {
            username: username,
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

    // Convert file to Base64
    async function fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
        });
    }

    // Display message in the UI
    function displayMessage(message) {
        if (!message || !message.context) {
            console.error("Invalid message data", message);
            return;
        }

        const messageDiv = $(`#message_container`);

        if (messageDiv.length === 0) {
            console.error("Message container not found for chat ID:", message.chatId);
            return;
        }

        const commentElement = $(`
                <div class="chat-message" data-feedback-id="${message.id}">
                    <h5>User: ${message.username}</h5>
                    <span class="feedback-text">${message.context}</span>
                    <br><br>
                </div>
            `);


        messageDiv.append(commentElement);
        messageDiv.scrollTop(messageDiv.prop("scrollHeight"));
    }
});
