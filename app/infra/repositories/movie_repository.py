from sqlalchemy.orm import Session, aliased
from fastapi import HTTPException
from sqlalchemy import or_, func, case
from app.infra.database.models import MovieModel
from sqlalchemy.sql import text
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

    def search_movies(self, query: str, limit: int = 10, offset: int = 0):
        """
        Search movies using full-text search (`@@`) and substring search (`ILIKE`).
        """
        search_query = func.plainto_tsquery("english", query)  # Convert search query into tsquery
        search_query_rus = func.plainto_tsquery("russian", query)  # Russian search
        
        movies = (
            self.db.query(MovieModel)
            .filter(
                (MovieModel.search_vector.op("@@")(search_query) | MovieModel.search_vector.op("@@")(search_query_rus)) |  # Full-text search
                (MovieModel.title.ilike(f"%{query}%")) |  # Substring match in title
                (MovieModel.description.ilike(f"%{query}%"))  # Substring match in description
            )
            .order_by(text("ts_rank_cd(search_vector, plainto_tsquery('english', :query)) DESC"))
            .params(query=query)  # Parameter binding for security
            .limit(limit)
            .offset(offset)
            .all()
        )
        return movies
        