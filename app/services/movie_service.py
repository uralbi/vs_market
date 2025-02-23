from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.infra.repositories.movie_repository import MovieRepository
from app.infra.database.models import MovieModel, MovieViewModel
import os, shutil

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

    def get_movie_by_id(self, movie_id: int, user=None):
        """Retrieve a movie by ID."""
        movie = self.repo.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        if not user and movie.is_public:
            return movie
        if user and movie.owner_id == user.id:
                return movie
        return HTTPException(status_code=404, detail="Movie not found")
    
    def get_movies(self, limit: int, offset: int):
        """Fetch paginated movies."""
        return self.repo.get_movies(limit, offset)

    def update_movie(self, movie_id: int, update_data: dict):
        """Update movie details."""
        return self.repo.update_movie(movie_id, update_data)

    def delete_movie(self, movie_id: int, user_id: int):
        """Delete a movie record."""
        
        movie = self.repo.get_movie_by_id(movie_id)
        if not movie or movie.owner_id != user_id:
            return False
    
        if movie.thumbnail_path:
            thumb_path = movie.thumbnail_path.replace("media", "media/movies/thumbs")
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
                
        if movie.file_path:
            movie_folder = os.path.dirname(movie.file_path)
            if os.path.exists(movie_folder):
                hls_folder = os.path.join(movie_folder, "hls")
                if os.path.exists(hls_folder) and os.path.isdir(hls_folder):
                    shutil.rmtree(hls_folder)
                    
                for file in os.listdir(movie_folder):
                    file_path = os.path.join(movie_folder, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                os.rmdir(movie_folder)
        
        return self.repo.delete_movie(movie_id)

    def search_movies(self, query: str, limit: int = 20, offset: int = 0):
        """
        Perform a full-text search on movies.
        """
        if not query or len(query) < 2:
            return []

        return self.repo.search_movies(query, limit, offset)
    
    def track_movie_progress(self, movie_id: int, user_id: int, progress: int):
        """Track and update user's progress in a movie."""
        return self.repo.save_movie_progress(movie_id, user_id, progress)
    
    def get_movie_progress(self, movie_id: int, user_id: int):
        """Retrieve user's progress in a movie."""
        return self.repo.get_movie_progress(movie_id, user_id)
    
    def update_movie_thumbnail(self, movie_id: int, thumbnail_path: str):
        """ Update the movie's thumbnail path in the database """
        return self.repo.update_movie_thumbnail(movie_id, thumbnail_path)
    
    def get_user_movies(self, user_id: int):
        """ Get user's movies """
        return self.repo.get_user_movies(user_id)
    
    def update_movie(self, movie_id: int, user_id: int, title: str, description: str, is_public: bool):
        movie = self.repo.get_movie_by_id(movie_id)
        if not movie:
            return None  # Movie not found
        if movie.owner_id != user_id:
            return "forbidden"  # User is not the owner
        return self.repo.update_movie(movie_id, title, description, is_public)