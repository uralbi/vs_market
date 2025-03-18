
const accessToken = getAccessTokenFromCookie()
let user2Id;
let socket;
let userId;
let userName;
let subject = productName
if (!subject){ subject = "-" }

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
        const chat_user = document.getElementById("chat_username");
        let chat_status = document.createElement("span");
        chat_status.setAttribute("id", `chat_status_${user2Id}`);
        chat_user.appendChild(chat_status)
        chatBox.innerHTML = "";  // Clear previous messages
        
        if (data.subject) {
            chat_title.innerText= `Тема: ${data.subject}`;
        }
        userId = data.user_id
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
    await loadOtherUser(room_id); // get id for user2Id and user2username

    const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
    let hostName = window.location.hostname;
    let back_host = '127.0.0.1:8000';

    if (hostName === '127.0.0.1'){
        back_host = '127.0.0.1:8000'
        } else {
        back_host = 'ai-ber.com'
        }

    recieverId = user2Id;
    
    socket = new WebSocket(`${ws_scheme}://${back_host}/ws/v2/chat/${recieverId}/${subject}?token=${encodeURIComponent(access_token)}`);

    socket.onopen = () => {
        updateUserStatus(userId, true);
        // showMessage("Соединение установлено", "success")
    };

    socket.onerror=(error) => {
        console.error("websocket error:", error)
    }
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.hasOwnProperty("is_online") && data.hasOwnProperty("user_id")) {
            updateUserStatus(data.user_id, data.is_online);
        }
        
        if (data.hasOwnProperty("sender_username") && data.hasOwnProperty("message")) {
            displayMessage(data.sender_username, data.message, "msg_received");
        }
    };

    socket.onclose = () => {
        console.log("WebSocket disconnected");
        updateUserStatus(userId, false);
    };

    loadChatHistory(accessToken, room_id);

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
    const timeSince = timeLapse(timestamp)
    const msgElement = document.createElement("div");
    msgElement.classList.add("chat-message", type);
    const msgText = document.createElement("p");
    msgText.textContent = type === "msg_sent" ? "" : ``; // ${sender}
    const msgSpan = document.createElement("span");
    msgSpan.textContent = `${message}`;
    const timeElement = document.createElement("small");
    timeElement.textContent = `${timeSince}`;
    timeElement.classList.add("timestamp");
    msgText.appendChild(msgSpan);
    msgElement.appendChild(msgText);
    msgElement.appendChild(timeElement);
    chatBox.appendChild(msgElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function updateUserStatus(userId, isOnline) {
    waitForElementToLoad(`chat_status_${userId}`, (userStatusElement) => {
        userStatusElement.textContent = isOnline ? "🟢" : "⚪";
    });
}

function waitForElementToLoad(elementId, callback) {
    const checkExist = setInterval(() => {
        const element = document.getElementById(elementId);
        if (element) {
            clearInterval(checkExist);
            callback(element);
        }
    }, 100);
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
        return data; // Returns the other user's ID
    } catch (error) {
        console.error("Error fetching other user:", error);
        return null;
    }
}

async function loadOtherUser(room_id) {
    try {
        other_data = await getOtherUser(room_id);
        user2Id = other_data.other_user_id
        user2username = other_data.other_username
        userName = other_data.other_username
        document.getElementById("chat_username").innerHTML =  `<i class="bi bi-person-circle"></i> ${user2username} <span id="user_status_${user2Id}></span>` 
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