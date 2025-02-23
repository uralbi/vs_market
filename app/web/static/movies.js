const Mov_API_URL = "/api/movies";
let limit = 20;  // Number of movies per page
let offset = 0; // Offset for pagination

async function fetchMovies() {
    try {
        const response = await fetch(`${Mov_API_URL}?limit=${limit}&offset=${offset}`);
        if (!response.ok) throw new Error("Failed to fetch movies.");

        const movies = await response.json();
        displayMovies(movies, "moviesContainer");
    } catch (error) {
        console.error("Error loading movies:", error);
    }
}

function displayMovies(movies, div_id) {
    const container = document.getElementById(div_id);
    container.innerHTML = ""; // Clear previous content

    if (movies.length === 0) {
        container.innerHTML = "<p class='text-center'>No movies found.</p>";
        return;
    }

    movies.forEach(movie => {
        const movieCard = document.createElement("div");
        
        movieCard.innerHTML = `
            <div class="card shadow-sm">
                <img src="${movie.thumbnail_path || '/media/no_image.webp'}" class="card-img-top" alt="Movie Thumbnail">
                <div class="card-body">
                    <h5 class="card-title">${movie.title}</h5>
                    <p class="card-text">${movie.description.substring(0, 100)}...</p>
                    <a href="/movies/stream/?id=${movie.id}" class="btn btn-outline-primary btn-sm">Смотреть</a>
                </div>
            </div>
        `;
        container.appendChild(movieCard);
    });
}

// Pagination controls
document.getElementById("prevBtn").addEventListener("click", () => {
    if (offset >= limit) {
        offset -= limit;
        fetchMovies();
    }
});

document.getElementById("nextBtn").addEventListener("click", () => {
    offset += limit;
    fetchMovies();
});


fetchMovies();
