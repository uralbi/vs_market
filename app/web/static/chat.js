// Get `user2_id` from URL
const urlParams = new URLSearchParams(window.location.search);
const user2Id = urlParams.get("receiver_id");  // This is the other user in the chat

// Get User's Own ID from Token
const token = document.cookie.split('; ').find(row => row.startsWith('access_token='));
const accessToken = token ? token.split('=')[1] : '';

if (!accessToken) {
    alert("Authentication required. Please log in.");
    window.location.href = "/login";
}

// Fetch authenticated user's ID
async function getUserId() {
    try {
        const response = await fetch(`/api/auth/me`, {
            headers: {
                "Authorization": `Bearer ${accessToken}`
            }
        });
        const user = await response.json();
        
        return {"user_id": user.user_id, "user_name": user.username}
    } catch (error) {
        console.error("Error fetching user:", error);
        alert("Error retrieving user info.");
        window.location.href = "/login";
    }
}

// Fetch chat history from API
async function loadChatHistory(userId, user2Id) {
    try {
        const response = await fetch(`/chat/messages?user2_id=${user2Id}`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${accessToken}`,
                "Content-Type": "application/json"
            }
        });

        if (!response.ok) throw new Error("Failed to load chat history");

        const data = await response.json();
        const chatBox = document.getElementById("chatBox");

        chatBox.innerHTML = "";  // Clear previous messages

        data.messages.forEach(msg => {
            displayMessage(msg.sender_id, msg.content, msg.sender_id === userId ? "msg_sent" : "msg_received");
        });
    } catch (error) {
        console.error("Error loading chat history:", error);
        alert("Error loading chat history.");
    }
}

// WebSocket variable to be accessible globally
let socket;
let userId;
let userName;

// Initialize WebSocket and load messages
getUserId().then(user => {
    
    if (!user.user_id) {
        console.log('No user id')    
        return
    };
    userId = user.user_id;
    userName = user.user_name;

    socket = new WebSocket(`ws://localhost:8000/ws/v2/chat/${userId}`);

    socket.onopen = () => {
        console.log("Connected to WebSocket");
        document.getElementById("chatBox").innerHTML += '<div class="text-center text-muted">Connected to chat</div>';
    };

    socket.onerror=(error) => {
        console.error("websocket error:", error)
    }
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        displayMessage(data.sender_username, data.message, "msg_received");
    };

    socket.onclose = () => {
        console.log("WebSocket disconnected");
        document.getElementById("chatBox").innerHTML += '<div class="text-center text-danger">Disconnected</div>';
    };

    // Load chat history when the page loads
    if (user2Id) {
        loadChatHistory(userId, user2Id);
    }
});

// Move sendMessage function OUTSIDE `getUserId().then(...)`
function sendMessage() {

    if (!userName) {
        alert("Please enter a message");
        return;
    }

    const messageData = {
        receiver_id: parseInt(user2Id),
        message: messageInput.value
    };

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(messageData));
        displayMessage(userName, messageInput.value, "msg_sent");
        messageInput.value = "";
    } else {
        alert("WebSocket is not connected!");
    }
}

// ✅ Ensure `sendMessage()` is properly attached to button
document.getElementById("sendMessageBtn").addEventListener("click", sendMessage);

// ✅ Keep displayMessage function globally accessible
function displayMessage(sender, message, type) {
    const chatBox = document.getElementById("chatBox");
    const msgElement = document.createElement("div");
    msgElement.classList.add("chat-message", type);
    msgElement.innerHTML = `<strong>${sender}:</strong> ${message}`;
    chatBox.appendChild(msgElement);
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to latest message
}
