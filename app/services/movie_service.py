from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.infra.repositories.movie_repository import MovieRepository
from app.infra.database.models import MovieModel


class MovieService:
    def __init__(self, db: Session):
        self.repo = MovieRepository(db)

    def create_movie(self, title: str, description: str, file_path: str, is_public: bool, owner_id: int):
        """Create a new movie entry."""
        movie = MovieModel(
            title=title,
            description=description,
            file_path=file_path,
            is_public=is_public,
            owner_id=owner_id
        )
        return self.repo.create_movie(movie)

    def get_movie(self, movie_id: int):
        """Retrieve a movie by ID."""
        return self.repo.get_movie_by_id(movie_id)

    def get_all_movies(self, is_public: bool = True):
        """Retrieve all public movies."""
        return self.repo.get_all_movies(is_public)

    def update_movie(self, movie_id: int, update_data: dict):
        """Update movie details."""
        return self.repo.update_movie(movie_id, update_data)

    def delete_movie(self, movie_id: int):
        """Delete a movie record."""
        return self.repo.delete_movie(movie_id)

    def search_movies(self, query: str, limit: int = 10, offset: int = 0):
        """
        Perform a full-text search on movies.
        """
        if not query or len(query) < 2:
            return []

        return self.repo.search_movies(query, limit, offset)