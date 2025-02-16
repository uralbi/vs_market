
        // Connect to the SSE endpoint
    const eventSource = new EventSource("/api/products/sse_products");

    eventSource.onmessage = function(event) {
        let product = JSON.parse(event.data);

        // Add new product to the list dynamically
        let productList = document.getElementById("productContainer");
        let productCard = document.createElement("div");
        productCard.classList.add("product-card");
        productCard.classList.add("card");
        productCard.innerHTML = `
            <img src="/${product.image_urls[0]}" alt="Product Image" class="card-img-top">
            <div class="card-body">
                <h5 class="card-title">${product.name}</h3>
                <p class="card-text">${product.description}</p>
                <p class="">Price: $${product.price.toFixed(2)}</p>
                <p>Category: ${product.category}</p>
            </div>
        `;
        
        productList.prepend(productCard);  // Insert new product at the top
    };

    eventSource.onerror = function(error) {
        console.error("SSE Error:", error);
    };

