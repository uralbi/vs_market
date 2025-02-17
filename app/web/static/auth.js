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


async function refreshAccessToken() {
    try {
        const response = await fetch(`${API_URL}/refresh`, {
            method: "POST",
            credentials: "include" // Sends HTTP-only refresh token from cookies
        });

        if (!response.ok) throw new Error("Failed to refresh token");

        const data = await response.json();
        setAccessTokenCookie(data.access_token);
        return data.access_token;
    } catch (error) {
        console.error("Token refresh error:", error);
        logout();
    }
}

async function authenticatedRequest(endpoint, options = {}) {
    let accessToken = getAccessTokenFromCookie();

    if (!accessToken || isTokenExpired(accessToken)) {
        accessToken = await refreshAccessToken();
        if (!accessToken) throw new Error("Authentication required");
    }

    options.headers = {
        ...options.headers,
        "Authorization": `Bearer ${accessToken}`
    };

    let response = await fetch(`${API_URL}/${endpoint}`, options);

    if (response.status === 401) {
        // Try refreshing the token if access is denied
        accessToken = await refreshAccessToken();
        if (!accessToken) throw new Error("Authentication required");

        options.headers["Authorization"] = `Bearer ${accessToken}`;
        response = await fetch(`${API_URL}${endpoint}`, options);
    }

    if (!response.ok) {
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
