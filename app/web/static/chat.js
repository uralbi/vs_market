
const accessToken = getAccessTokenFromCookie()

let user2Id;
let socket;
let userId;
let userName;
let subject = productName

if (!subject){
    subject = "-"
}
async function loadChatHistory(accessToken, room_id) {
    try {
        const response = await fetch(`/chat/messages?room_id=${room_id}`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${accessToken}`,
            }
        });

        if (!response.ok) throw new Error("Failed to load chat history");

        const data = await response.json();
        const chatBox = document.getElementById("chatBox");
        const chat_title = document.getElementById("chat_title");
        chatBox.innerHTML = "";  // Clear previous messages
        
        if (data.subject) {
            chat_title.innerText= data.subject;
        }
        
        data.messages.forEach(msg => {
            displayMessage(msg.sender_username, msg.content, msg.sender_id === userId ? "msg_sent" : "msg_received", msg.timestamp);
        });
    } catch (error) {
        console.error("Error loading chat history:", error);
        alert("Error loading chat history.");
    }
}

// Initialize WebSocket and load messages
async function InitializeChat(room_id, access_token){
    await loadOtherUser(room_id);

    getUserId(accessToken).then(user => {
        if (user.user_id == user2Id) { 
            window.location.href = document.referrer || "/";
            }

        if (!user.user_id) { console.log('No user id'); return};

        userId = user.user_id;
        recieverId = user2Id;
        userName = user.user_name;
        
        socket = new WebSocket(`ws://localhost:8000/ws/v2/chat/${userId}/${recieverId}/${subject}`);

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
        loadChatHistory(accessToken, room_id);
        

    });
};

InitializeChat(room_id, accessToken);


function sendMessage() {

    if (!userName || !messageInput.value) {
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

// Ensure `sendMessage()` is properly attached to button
document.getElementById("sendMessageBtn").addEventListener("click", sendMessage);

// Keep displayMessage function globally accessible
function displayMessage(sender, message, type, timestamp = new Date().toISOString()) {
    const chatBox = document.getElementById("chatBox");
    const formattedTime = formatTimestamp(timestamp);
    const msgElement = document.createElement("div");
    msgElement.classList.add("chat-message", type);
    const msgText = document.createElement("p");
    msgText.textContent = type === "msg_sent" ? "" : `${sender}`;
    const msgSpan = document.createElement("span");
    msgSpan.textContent = `${message}`;
    const timeElement = document.createElement("small");
    timeElement.textContent = formattedTime;
    timeElement.classList.add("timestamp");
    msgText.appendChild(msgSpan);
    msgElement.appendChild(msgText);
    msgElement.appendChild(timeElement);
    chatBox.appendChild(msgElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function formatTimestamp(timestamp = new Date().toISOString()) {
    const dateObj = new Date(timestamp);
    const options = { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false };
    return dateObj.toLocaleString("en-US", options).replace(",", "");
}

async function getOtherUser(roomId) {
    try {
        const token = getAccessTokenFromCookie(); // Retrieve auth token

        const response = await fetch(`/chat/counterpart?room_id=${roomId}`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error("Failed to fetch other user");
        }

        const data = await response.json();
        return data.other_user_id; // ✅ Returns the other user's ID
    } catch (error) {
        console.error("Error fetching other user:", error);
        return null;
    }
}

async function loadOtherUser(room_id) {
    try {
        user2Id = await getOtherUser(room_id);
    } catch (error) {
        console.error("Error fetching other user:", error);
    }
}

function getAccessTokenFromCookie() {
    const cookies = document.cookie.split("; ");
    for (let cookie of cookies) {
        const [name, value] = cookie.split("=");
        if (name === "access_token") return value;
    }
    return null;
}

async function getUserId(accessToken) {
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