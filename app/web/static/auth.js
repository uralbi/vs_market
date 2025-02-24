const API_URL = "/api/auth";


async function login(email, password) {
    try {
        const response = await fetch(`${API_URL}/token`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include", // Ensures cookies are sent with the request
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) throw new Error("Invalid credentials");

        const data = await response.json();
        setAccessTokenCookie(data.access_token);
        return data;
    } catch (error) {
        console.error("Login error:", error);
        throw error;
    }
}

function setAccessTokenCookie(accessToken) {
    document.cookie = `access_token=${accessToken}; path=/; secure; samesite=strict`;
}

function getAccessTokenFromCookie() {
    const cookies = document.cookie.split("; ");
    for (let cookie of cookies) {
        const [name, value] = cookie.split("=");
        if (name === "access_token") return value;
    }
    return null;
}

function getRefreshTokenFromCookie() {
    const cookies = document.cookie.split("; ");
    for (let cookie of cookies) {
        const [name, value] = cookie.split("=");
        if (name === "refresh_token") return value;
    }
    return null;
}

async function refreshAccessToken() {
    try {
        let refresh_token = getRefreshTokenFromCookie();
        if (!refresh_token) {
            console.log("No refresh token.")
            return null;
        }

        let requestBody = JSON.stringify({ refresh_token: refresh_token });

        const response = await fetch(`${API_URL}/refresh`, {
            method: "POST",
            headers: { "Content-Type" : "application/json" },
            body: requestBody,
        });

        if (!response.ok) {
            const errorText = await response.text()
            clearAuthCookies();
            return null;
        };
        
        const data = await response.json();
        setAccessTokenCookie(data.access_token);
        return data.access_token;
    } catch (error) {
        console.error("Token refresh error:", error);
        return null;
    }
}

async function authenticatedRequest(endpoint, options = {}) {
    let accessToken = getAccessTokenFromCookie();

    if (!accessToken || isTokenExpired(accessToken)) {
        accessToken = await refreshAccessToken();
        if (!accessToken) {
            console.error("Authentication required: No valid access token.");
            clearAuthCookies();
            throw new Error("Authentication required");
        }
    }

    // Set authorization header with valid token
    options.headers = {
        ...options.headers,
        "Authorization": `Bearer ${accessToken}`
    };

    let response = await fetch(`${API_URL}/${endpoint}`, options);

    // If unauthorized, attempt to refresh token once
    if (response.status === 401) {
        console.warn("Access token expired, attempting refresh...");

        accessToken = await refreshAccessToken();
        if (!accessToken) {
            console.error("Failed to refresh access token. Authentication required.");
            throw new Error("Authentication required");
        }

        options.headers["Authorization"] = `Bearer ${accessToken}`;
        response = await fetch(`${API_URL}/${endpoint}`, options);
    }

    if (!response.ok) {
        console.error(`Request failed with status ${response.status}: ${await response.text()}`);
        throw new Error(`Request failed: ${response.status}`);
    }

    return response.json();
}

function isTokenExpired(token) {
    try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        const expirationTime = payload.exp * 1000;  // Convert to milliseconds
        return Date.now() >= expirationTime;
    } catch (error) {
        console.error("Invalid token:", error);
        return true;  // Assume expired if there's an error
    }
}

function clearAuthCookies() {
    document.cookie = "access_token=; Max-Age=0; path=/";
    document.cookie = "refresh_token=; Max-Age=0; path=/";
    console.warn("Authentication tokens cleared.");
}

const logoutBtn = document.getElementById("logoutBtn");
if (logoutBtn) {
    logoutBtn.addEventListener("click", async function() {
        logout();
    });
}

async function logout() {
    document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; secure; samesite=strict";
    await fetch(`${API_URL}/logout`, { method: "POST", credentials: "include" }); // Logout API to clear refresh token
    window.location.href = "/";
}


function displayPrice(price, isDollar) {
    const exchangeRate = 87.8;
    
    function formatLargeNumbers(value, isUSD = false) {
        if (value >= 1_000_000_000) return (value / 1_000_000_000).toFixed(1) + (isUSD ? " млрд" : " млрд");
        if (value >= 1_000_000) return (value / 1_000_000).toFixed(2) + (isUSD ? " млн" : " млн");
        if (value >= 100_000) return (value / 1_000).toFixed(1) + (isUSD ? " тыс" : " тыс");
        if (value >= 10_000) return (value / 1_000).toFixed(1) + (isUSD ? " тыс" : " тыс");
        return value.toFixed(1);
    }

    if (isDollar) {
        let som = price * exchangeRate;
        return `$${formatLargeNumbers(price, true)} <br> <small> ${formatLargeNumbers(som, false)} c.</small>`;
    } else {
        let usd = price / exchangeRate;
        return `${formatLargeNumbers(price, false)} c.<br><small> $${formatLargeNumbers(usd, true)} </small>`;
    }
}

function displayPrice_org(price, isDollar) {
    const exchangeRate = 87.8;
    if (isDollar) {
        let som = price * exchangeRate;
        return `$${price} <br> <small> ${som.toFixed(2)} c.</small>`;
    } else {
        let usd = price / exchangeRate;
        return `${price} c.<br><small> $${usd.toFixed(2)} </small>`;
    }
}


function getTimeDifference(updatedAt) {
    const updatedAtDate = new Date(updatedAt);
    const now = new Date();
    const differenceInSeconds = Math.round((now - updatedAtDate) / 1000);
    const differenceInMinutes = Math.round(differenceInSeconds / 60);
    const differenceInHours = Math.round(differenceInMinutes / 60);
    const differenceInDays = Math.round(differenceInHours / 24);
    const differenceInWeeks = Math.round(differenceInDays / 7);
    const differenceInMonths = Math.round(differenceInDays / 30);
    const differenceInYears = Math.round(differenceInDays / 365);

    if (differenceInSeconds < 60) {
        return `${differenceInSeconds} сек`;
    } else if (differenceInMinutes < 60) {
        return `${differenceInMinutes} мин`;
    } else if (differenceInHours < 24) {
        return `${differenceInHours} час.`;
    } else if (differenceInDays < 7) {
        return `${differenceInDays} дн.`;
    } else if (differenceInWeeks < 4) {
        return `${differenceInWeeks} нед.`;
    } else if (differenceInMonths < 12) {
        return `${differenceInMonths} мес.`;
    } else {
        return `${differenceInYears} год.`;
    }
  };

  function setCookie(name, value, days) {
    let expires = "";
    if (days) {
        let date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + value + "; path=/" + expires;
}

function getCookie(name) {
    let cookies = document.cookie.split("; ");
    for (let cookie of cookies) {
        let [cookieName, cookieValue] = cookie.split("=");
        if (cookieName === name) return cookieValue;
    }
    return null;
}

function toggleTheme() {
    const body = document.body;
    body.classList.toggle("dark-mode");
    
    const themeIcon = document.getElementById("themeIcon");
    // ✅ Save the current mode in cookies
    if (body.classList.contains("dark-mode")) {
        setCookie("theme", "dark", 30);  // Save for 30 days
        themeIcon.classList.replace("bi-lightbulb-fill", "bi-lightbulb"); // Switch to moon icon
    } else {
        setCookie("theme", "light", 30);
        themeIcon.classList.replace("bi-lightbulb", "bi-lightbulb-fill"); // Switch back to lightbulb
    }


}

// ✅ Load theme on page load
document.addEventListener("DOMContentLoaded", () => {
    if (getCookie("theme") === "dark") {
        document.body.classList.add("dark-mode");
    }
});

document.addEventListener("DOMContentLoaded", function() {
AOS.init();
});


function createProductCard(product, delay) {
    let productCard = document.createElement("div");
    productCard.classList.add("product-card", "card");
    productCard.setAttribute("data-aos", "fade-in");
    productCard.setAttribute("data-aos-delay", delay);
    let imageUrls = product.image_urls && product.image_urls.length > 0 ? product.image_urls : ["/static/no-image.png"];
    let productName = `${product.name} <span class="card-text"> - ${product.description} </span>`;
    productCard.innerHTML = `
        <div class="card-img-top">
            ${createImageCarousel(product.id, imageUrls)}
        </div>
        <div class="card-body">
            <a href="/product/${product.id}"><h5 class="card-title">${productName}</h5></a>

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
