$(document).ready(function () {
    const socket = new WebSocket(`ws://${window.location.host}/ws/comments/`);

    socket.onopen = function () {
        console.log("WebSocket connection established.");
    };

    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        if (data.comment) {
            displayComment(data.comment);
        }
    };

    socket.onclose = function () {
        console.log("WebSocket connection closed.");
    };

    $('.commentForm').on('submit', async function (event) {
        event.preventDefault();

        const form = $(this);
        const contentId = form.attr('id').split('_')[1];
        console.log(contentId)
        const userId = $(`#user_id_${contentId}`).val();
        const username = $(`#username_id_${contentId}`).val();
        const objectId = $(`#object_id_${contentId}`).val();
        const content = $(`#content_${contentId}`).val().trim();
        const contentTypeId = $(`#content_type_id_${contentId}`).val();

        const fileInput = $(`#file_${contentId}`)[0];
        const imageInput = $(`#image_${contentId}`)[0];


        const message = {
            username: username,
            user_id: userId,
            content: content,
            content_type_id: contentTypeId,
            object_id: objectId,
            object_ct_id:contentId,
            file: fileInput.files[0] ? await fileToBase64(fileInput.files[0]) : null,
            image: imageInput.files[0] ? await fileToBase64(imageInput.files[0]) : null,
        };

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

   function displayComment(comment) {
    if (!comment || !comment.object_id || !comment.content) {
        console.error("Invalid comment data", comment);
        return;
    }

    const commentsDiv = $(`#comments_${comment.object_ct_id}`);

    if (commentsDiv.length === 0) {
        console.error("Comments container not found for object ID:", comment.object_id);
        return;
    }

    const commentElement = $(`
        <div class="feedback" data-feedback-id="${comment.id}">
            <h5>User: ${comment.username}</h5>
            <span class="feedback-text">${comment.content}</span>
            <br><br>
        </div>
    `);
    console.log(commentElement)
    commentsDiv.append(commentElement);
    commentsDiv.scrollTop(commentsDiv.prop("scrollHeight"));
}

});
