from fastapi import APIRouter, UploadFile, Form, Depends, Response, HTTPException, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.services.movie_service import MovieService
from app.infra.database.db import get_db
from app.infra.database.models import MovieModel, MovieViewModel, MovieCommentModel, MovieLikeModel, MovieSubtitleModel
from app.domain.security.auth_user import user_authorization
from fastapi.security import OAuth2PasswordBearer
from app.infra.tasks.vid_tasks import process_video_hls
import os, shutil
from pathlib import Path

router = APIRouter(
    prefix="/movies",
    tags=["Movies"]
)

token_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


@router.get("/search")
def search_movies(query: str, db: Session = Depends(get_db)):
    """
    Search for movies using full-text search on title and description.
    """
    movie_service = MovieService(db)
    return movie_service.search_movies(query)


@router.get("/")
def get_movies(db: Session = Depends(get_db)):
    """ Fetches all movies """
    movies = db.query(MovieModel).filter(MovieModel.is_public == True).all()
    return movies


@router.post("/{movie_id}/track")
def track_movie(movie_id: int, progress: int, db: Session = Depends(get_db)):
    """ Save user's last watched progress """
    view = db.query(MovieView).filter_by(movie_id=movie_id, user_id=1).first()
    if view:
        view.progress = progress
    else:
        view = MovieView(movie_id=movie_id, user_id=1, progress=progress)
        db.add(view)
    db.commit()
    return {"message": "Progress saved"}

HLS_FOLDER = "hls/"
UPLOAD_FOLDER = "media/movies/"

@router.post("/upload")
async def upload_movie(
    token: str = Depends(token_scheme),
    title: str = Form(...),
    description: str = Form(...),
    is_public: bool = Form(True),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
    ):

    user = user_authorization(token, db)
    
    Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)  # Ensure upload directory exists
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    process_video_hls.delay(file_path, HLS_FOLDER) # Trigger HLS conversion via Celery
    
    mov_service = MovieService(db) # Create movie entry in the database
    
    movie = mov_service.create_movie(title, description, file_path, is_public, owner_id=user.id)  # Replace with actual user

    return {"message": "Upload successful, processing started!", "movie_id": movie.id, "file_path": file_path}


@router.post("/{movie_id}/like")
def like_movie(movie_id: int, token, db: Session = Depends(get_db)):
    user = user_authorization(token, db)
    
    existing_like = db.query(MovieLikeModel).filter_by(user_id=user.id, movie_id=movie_id).first()
    if existing_like:
        return {"message": "Already liked"}
    
    like = MovieLikeModel(user_id=user.id, movie_id=movie_id)
    db.add(like)
    db.commit()
    return {"message": "Liked successfully"}


@router.get("/{movie_id}/hls")
async def stream_hls(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    file_path = movie.file_path.replace(".mp4", ".m3u8")  # Assume converted

    return FileResponse(file_path, media_type="application/vnd.apple.mpegurl")
