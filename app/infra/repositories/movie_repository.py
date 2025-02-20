from sqlalchemy.orm import Session, aliased
from fastapi import HTTPException
from sqlalchemy import or_, func, case
from app.infra.database.models import MovieModel, MovieLikeModel, MovieCommentModel, MovieSubtitleModel, MovieViewModel
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session


class MovieRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_movie(self, movie: MovieModel):
        """Insert a new movie record into the database."""
        self.db.add(movie)
        self.db.commit()
        self.db.refresh(movie)
        return movie

    def get_movie_by_id(self, movie_id: int):
        """Fetch a movie by its ID."""
        return self.db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    def get_all_movies(self, is_public: bool = True):
        """Fetch all public movies (or all movies for admin)."""
        query = self.db.query(MovieModel)
        if is_public:
            query = query.filter(MovieModel.is_public == True)
        return query.all()

    def update_movie(self, movie_id: int, update_data: dict):
        """Update a movie's details."""
        movie = self.get_movie_by_id(movie_id)
        if not movie:
            return None
        for key, value in update_data.items():
            setattr(movie, key, value)
        self.db.commit()
        self.db.refresh(movie)
        return movie

    def delete_movie(self, movie_id: int):
        """Delete a movie record."""
        movie = self.get_movie_by_id(movie_id)
        if movie:
            self.db.delete(movie)
            self.db.commit()
            return True
        return False

    def search_movies(self, query: str):
        """Search movies by title or description using full-text search."""
        return (
            self.db.query(MovieModel)
            .filter(MovieModel.search_vector.op('@@')(func.to_tsquery("english", query)))
            .all()
        )
        