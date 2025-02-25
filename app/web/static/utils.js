async function addToFavorites(productId) {
    try { 
        await authenticatedRequest('me'); 
    } catch (error) {
        showMessage("Войдите, чтобы сохранить", "danger");
        return;
    }

    let token = getAccessTokenFromCookie();
    let response = await fetch(`/favs/${productId}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
    });

    let button = document.getElementById(`pin_${productId}`);

    if (response.ok) {
        let resp = await response.json();
        if (resp.message.includes("добавлено")) {
            button.classList.remove("btn-outline-secondary");
            button.classList.add("btn-outline-primary");
            showMessage(resp.message, "primary");
        } else {
            button.classList.remove("btn-outline-primary");
            button.classList.add("btn-outline-secondary");
            showMessage(resp.message, "success");
        }
    } else {
        let error = await response.json();
        showMessage(error.detail, "success");
    }
}

function showMessage(message, type = "primary") {
    let msg_field = document.getElementById("status_messages");

    if (!msg_field) {
        console.warn("Element with ID 'status_messages' not found.");
        return;
    }

    // Clear existing timeout if a new message appears
    if (msg_field.dataset.timeoutId) {
        clearTimeout(msg_field.dataset.timeoutId);
    }

    // Set message content and styles
    msg_field.innerHTML = message;
    msg_field.className = `text-center alert alert-${type} fade show`; // Set Bootstrap alert class
    msg_field.style.opacity = "1";

    // Set a new timeout for disappearing message
    let timeoutId = setTimeout(() => {
        msg_field.style.transition = "opacity 1s";
        msg_field.style.opacity = "0";
        setTimeout(() => {
            msg_field.innerHTML = "";
        }, 1000); // Remove text after fade-out
    }, 4000); // 6 seconds

    // Store timeout ID to reset if a new message appears
    msg_field.dataset.timeoutId = timeoutId;
}
