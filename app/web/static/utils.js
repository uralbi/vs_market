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
        button.classList.remove("btn-outline-secondary");
        button.classList.add("btn-outline-primary");
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
        let button = document.getElementById(`pin_${productId}`)
        button.classList.remove("btn-outline-primary");
        button.classList.add("btn-outline-secondary");
        console.log('Unpinned')
    } else {
        let error = await response.json();
        alert(error.detail);
    }
}


