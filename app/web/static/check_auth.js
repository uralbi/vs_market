
    async function checkAuthStatus() {
        let token = document.cookie.split('; ').find(row => row.startsWith('access_token='));
        if (!token) {
            document.getElementById("authStatus").innerText = "You are not logged in.";
            window.location.href = "/login";
            return;
        }
        token = token.split('=')[1];
        let response = await fetch("/api/auth/me", {
            method: "GET",
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (response.ok) {
            let user = await response.json();
            document.getElementById("authStatus").innerText = `You are logged in as ${user.email}`;
        } else {
            document.getElementById("authStatus").innerText = "You are not logged in.";
        }
    }

    document.addEventListener("DOMContentLoaded", checkAuthStatus);
