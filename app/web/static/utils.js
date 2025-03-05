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

function formatTimestamp(timestamp = new Date().toISOString()) {
    const dateObj = new Date(timestamp);
    const options = { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false };
    return dateObj.toLocaleString("en-US", options).replace(",", "");
}

function formatYearMonth(timestamp = new Date().toISOString()) {
    const dateObj = new Date(timestamp);
    return `${dateObj.getFullYear()}.${String(dateObj.getMonth() + 1).padStart(2, '0')}`;
}

function formatYear(timestamp = new Date().toISOString()) {
    const dateObj = new Date(timestamp);
    return `${dateObj.getFullYear()}`;
}

function showConfirmationModal(message, onConfirm) {
    // showConfirmationModal("Ваш текст", () => { });
    const modal = new bootstrap.Modal(document.getElementById("confirmationModal"));
    document.getElementById("confirmationModalBody").innerText = message;
    document.getElementById("confirmActionBtn").onclick = function () {
        modal.hide();
        onConfirm(); // Execute callback function
    };

    modal.show();
}


function displayMovies(movies, div_id) {
    const container = document.getElementById(div_id);
    container.innerHTML = ""; // Clear previous content

    if (movies.length === 0) {
        container.innerHTML = "<p class='text-center'>No movies found.</p>";
        return;
    }

    movies.forEach(movie => {
        let maxLength = 20;
        let truncatedName = movie.title.length > maxLength 
        ? truncatedName.substring(0, maxLength) + " ..." 
        : movie.title;
        
        let maxLength_desc = 50
        let truncatedDescription = movie.description.length > maxLength_desc
        ? movie.description.substring(0, maxLength_desc) + " ..." 
        : movie.description;

        const movieCard = document.createElement("div");
        movieCard.classList.add("movie-card");

        movieCard.innerHTML = `
            <div class="card shadow-sm">
                <img src="${movie.thumbnail_path || '/media/no_image.webp'}" class="card-img-top" alt="Movie Thumbnail">
                <div class="card-body">
                    <h5 class="card-title">${movie.title}   </h5>
                    <p class="card-text">${truncatedDescription}   </p>
                    <p class="movie_duration">${(movie.duration / 60).toFixed(0)} мин </p>
                    <p class="movie_price">${movie.price === 0 ? 'Бесплатно' : movie.price + ' <span>cом</span>'}</p>
                    <a href="/movies/preview/?id=${movie.id}" class="btn btn-outline-success btn-sm m-0"><i class="bi bi-play-btn me-1"></i>preview</a>
                    <a href="/movies/stream/?id=${movie.id}" class="play_btn"><i class="bi bi-play-circle-fill"></i></a>
                    
                </div>
            </div>
        `;
        container.appendChild(movieCard);
    });

}

function createProductCard(product, delay) {
    let productCard = document.createElement("div");
    productCard.classList.add("product-card", "card");
    productCard.setAttribute("data-aos", "fade-in");
    productCard.setAttribute("data-aos-delay", delay);
    let imageUrls = product.image_urls && product.image_urls.length > 0 ? product.image_urls : ["/static/no-image.png"];
    //let productName = `${product.name} <span class="card-text"> - ${product.description} </span>`;
    let productName = product.name;
    let maxLength = 20;
    let truncatedName = product.name.length > maxLength 
    ? productName.substring(0, maxLength) + " ..." 
    : productName;

    productCard.innerHTML = `
        <div class="card-img-top">
            ${createImageCarousel(product.id, imageUrls)}
        </div>
        <div class="card-body">
            <a href="/product/${product.id}"><h5 class="card-title">${truncatedName}</h5></a>

            <button class="chat_btn btn btn-outline-secondary btn-sm" 
                data-aos-delay="10"
                onclick="openChat(${product.owner_id}, ${product.id})">
                <i class="bi bi-chat-left-text"></i>
            </button>

            <button class="btn btn-sm btn-outline-secondary pin_btn"
                id="pin_${product.id}" 
                onclick="addToFavorites(${product.id})">
                <i class="bi bi-paperclip"></i>
            </button>

            <p class="card-price">
                ${displayPrice(product.price, product.is_dollar)}
            </p>
        </div>
    `;

    return productCard;
}

async function openChat(receiverId, product_id) {
 
    try {
        const user = await authenticatedRequest('me'); 
        if (!user) {
            // msg_field.innerHTML = "Вы не зарегистрированы!"
            showMessage("Вы не зарегистрированы!", "warning");
            return;
        }

        if (user.user_id === receiverId) {
            // msg_field.innerHTML = "Это ваше объявление!"
            showMessage("Это ваше объявление!", "success");
            return;
        }
        window.location.href = `/messages/users?user_id=${user.user_id}&receiver_id=${receiverId}&product_id=${product_id}`;

    } catch (error) {
        console.error("Authentication error:", error);
        showMessage("Вы не зарегистрированы!", "warning");
    }
}