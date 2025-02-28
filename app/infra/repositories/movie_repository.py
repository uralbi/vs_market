from sqlalchemy.orm import Session, aliased
from fastapi import HTTPException
from sqlalchemy import or_, func, cast, Interval
from app.infra.database.models import MovieModel, MovieViewModel
from sqlalchemy.sql import text
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

    def get_movies(self, limit: int, offset: int):
        """Retrieve public movies with pagination."""
        return (
            self.db.query(MovieModel)
            .filter(MovieModel.is_public == True)
            .filter(MovieModel.duration > 0)
            .order_by(MovieModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

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
            .filter(MovieModel.is_public == True)
            .filter(MovieModel.duration > 0)
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
    
    def get_movie_progress(self, movie_id: int, user_id: int):
        """Retrieve user's last watched progress for a movie."""
        return self.db.query(MovieViewModel).filter_by(movie_id=movie_id, user_id=user_id).first()

    def save_movie_progress(self, movie_id: int, user_id: int, progress: int):
        """Save or update user's last watched progress."""
        view = self.get_movie_progress(movie_id, user_id)
        if view:
            view.progress = progress
        else:
            view = MovieViewModel(movie_id=movie_id, user_id=user_id, progress=progress)
            self.db.add(view)
        self.db.commit()
        return view

    def update_movie_thumbnail(self, movie_id: int, thumbnail_path: str):
        """
        Update the movie's thumbnail path in the database.
        """
        movie = self.db.query(MovieModel).filter(MovieModel.id == movie_id).first()
        if movie:
            movie.thumbnail_path = thumbnail_path
            self.db.commit()
            self.db.refresh(movie)
            
    def get_user_movies(self, user_id: int):
        """ Get user's movies """
        return self.db.query(MovieModel).filter(MovieModel.owner_id == user_id).all()

    def update_movie(self, movie_id: int, update_data: dict):
        """
        Dynamically update a movie's details using a dictionary.
        """
        movie = self.get_movie_by_id(movie_id)
        if not movie:
            return None

        for key, value in update_data.items():
            if value is not None:
                setattr(movie, key, value)

        self.db.commit()
        self.db.refresh(movie)
        return movie
