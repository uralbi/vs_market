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
