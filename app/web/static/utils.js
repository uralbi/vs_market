async function addToFavorites(productId) {
    
    try{ await authenticatedRequest('me') }
    catch(error){
        alert("Войдите чтоб сохранить")
        return
    }
    

    let token = getAccessTokenFromCookie();

    let response = await fetch(`/favs/${productId}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
    });

    if (response.ok) {
        let button = document.getElementById(`pin_${productId}`)
        button.classList.remove("btn-outline-success");
        button.classList.add("btn-primary");
    } else {
        let error = await response.json();
        alert(error.detail);
    }
}

async function removeFromFavorites(productId) {

    let token = getAccessTokenFromCookie();

    if (!token) {
        console.warn("User is not authenticated.");
        return;  // Stop execution if no token is found
    }

    let response = await fetch(`/favs/${productId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    });

    if (response.ok) {
        console.log('Unpinned')
    } else {
        let error = await response.json();
        alert(error.detail);
    }
}

document.querySelectorAll(".chat_link_btn").forEach(button => {
    button.addEventListener("click", async function () {
        try{ await authenticatedRequest('me') }
        catch(error){
            alert("Войдите чтоб написать продавцу.")
            return
        }
        const receiverId = this.getAttribute("data-receiver-id");
        const lastPage = sessionStorage.getItem("lastPage") || "/";  // Get last page
        window.location.href = `/messages?receiver_id=${receiverId}&prev_page=${encodeURIComponent(lastPage)}`;
    });
});
