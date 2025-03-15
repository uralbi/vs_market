
const exchangeRate = 87.8;
function displayPrice(price, isDollar) {    
    function formatLargeNumbers(value, isUSD = false) {
        if (value >= 1_000_000_000) return (value / 1_000_000_000).toFixed(1) + (isUSD ? " млрд" : " млрд");
        if (value >= 1_000_000) return (value / 1_000_000).toFixed(2) + (isUSD ? " млн" : " млн");
        if (value >= 100_000) return (value / 1_000).toFixed(1) + (isUSD ? " тыс" : " тыс");
        if (value >= 10_000) return (value / 1_000).toFixed(1) + (isUSD ? " тыс" : " тыс");
        return value.toFixed(1);
    }

    if (isDollar) {
        let som = price * exchangeRate;
        return `$ ${formatLargeNumbers(price, true)} <br> <small> ${formatLargeNumbers(som, false)} c.</small>`;
    } else {
        let usd = price / exchangeRate;
        return `${formatLargeNumbers(price, false)} c.<br><small> $ ${formatLargeNumbers(usd, true)} </small>`;
    }
}

function displayPrice_org(price, isDollar) {
    const formatNumber = num => num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");

    if (isDollar) {
        let som = price * exchangeRate;
        return `$ ${formatNumber(price)} <br> <small> ${formatNumber(som.toFixed(0))} c.</small>`;
    } else {
        let usd = price / exchangeRate;
        return `${formatNumber(price)} c.<br><small> $ ${formatNumber(usd.toFixed(0))} </small>`;
    }
}

function displayPrice_org_list(price, isDollar) {
    const formatNumber = num => num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");

    if (isDollar) {
        let som = price * exchangeRate;
        return `$ ${formatNumber(price)} <small>( ${formatNumber(som.toFixed(0))} c. )</small>`;
    } else {
        let usd = price / exchangeRate;
        return `${formatNumber(price)} c. <small>( $${formatNumber(usd.toFixed(0))} )</small>`;
    }
}

function setCookie(name, value, days) {
    let expires = "";
    if (days) {
        let date = new Date();
        date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + value + "; path=/" + expires;
}

function getCookie(name) {
    let nameEQ = name + "=";
    let ca = document.cookie.split(";");
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i].trim();
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length);
    }
    return null;
}

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

function timeLapse(timestamp = new Date().toISOString()) {
    const dateObj = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now - dateObj) / 1000);

    if (diffInSeconds < 300) return "менее 5 мин назад"; // <5 min
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} мин назад`; // Minutes
    if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `${hours} ${getHourWord(hours)} назад`; // Hours
    }
    if (diffInSeconds < 2592000) {
        const days = Math.floor(diffInSeconds / 86400);
        return `${days} ${getDayWord(days)} назад`; // Days
    }

    return formatYearMonth(timestamp); // Fallback to Year-Month if >30 days
}

// Helper function to correctly format "час", "часа", "часов"
function getHourWord(hours) {
    if (hours === 1 || hours % 10 === 1 && hours !== 11) return "час";
    if ([2, 3, 4].includes(hours % 10) && ![12, 13, 14].includes(hours)) return "часа";
    return "часов";
}

// Helper function to correctly format "день", "дня", "дней"
function getDayWord(days) {
    if (days === 1 || days % 10 === 1 && days !== 11) return "день";
    if ([2, 3, 4].includes(days % 10) && ![12, 13, 14].includes(days)) return "дня";
    return "дней";
}
