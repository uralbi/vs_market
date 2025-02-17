async function load_chats(userId) {
    try {
        const response = await fetch(`/chat/rooms/${userId}`);
        if (!response.ok) {
            throw new Error("Failed to fetch chat rooms");
        }

        const chatRooms = await response.json();
        const chatRoomsList = document.getElementById("chatRoomsList");

        // Clear previous chat list to prevent duplication
        chatRoomsList.innerHTML = "";

        if (chatRooms.length === 0) {
            chatRoomsList.innerHTML = "<li class='list-group-item'>No chat rooms found</li>";
            return;
        }

        chatRooms.forEach(room => {
            const listItem = document.createElement("li");
            listItem.classList.add("list-group-item");

            listItem.innerHTML = `
                <a href="/messages?receiver_id=${room.other_user_id}" class="text-decoration-none">
                    Chat with User ${room.other_user_id}
                </a>
            `;

            chatRoomsList.appendChild(listItem);
        });
    } catch (error) {
        console.error("Error loading chat rooms:", error);
        alert("Error loading chat rooms. Please try again.");
    }
}
