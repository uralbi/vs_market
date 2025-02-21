from fastapi import APIRouter, UploadFile, Form, Depends, Response, HTTPException, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.services.movie_service import MovieService
from app.infra.database.db import get_db
from app.infra.database.models import MovieModel, MovieViewModel, MovieCommentModel, MovieLikeModel, MovieSubtitleModel
from app.domain.security.auth_user import user_authorization
from fastapi.security import OAuth2PasswordBearer
from app.infra.tasks.vid_tasks import process_video_hls
from app.domain.dtos.movie import MovieDTO
import os, shutil
from pathlib import Path


router = APIRouter(
    prefix="/api/movies",
    tags=["API_Movies"]
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


# @router.post("/{movie_id}/track")
# def track_movie(movie_id: int, progress: int, db: Session = Depends(get_db)):
#     """ Save user's last watched progress """
#     view = db.query(MovieView).filter_by(movie_id=movie_id, user_id=1).first()
#     if view:
#         view.progress = progress
#     else:
#         view = MovieView(movie_id=movie_id, user_id=1, progress=progress)
#         db.add(view)
#     db.commit()
#     return {"message": "Progress saved"}


UPLOAD_FOLDER = "media/movies/"
ALLOWED_VIDEO_FORMATS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}


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
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    filename = os.path.basename(file.filename).rsplit(".", 1)[0]  # Extract filename without extension
    
    HLS_FOLDER = f"media/movies/{filename}/hls"
    UPLOAD_FOLDER = f"media/movies/{filename}"
    
    if file_extension not in ALLOWED_VIDEO_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
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
    """
    Serve the master `.m3u8` playlist for a given movie.
    """
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    base_filename = Path(movie.file_path).stem  # Extract filename without extension
    hls_directory = Path(movie.file_path).parent / "hls"
    master_playlist_path = hls_directory / f"{base_filename}_master.m3u8"

    if not master_playlist_path.exists():
        raise HTTPException(status_code=404, detail="HLS playlist not found")

    return FileResponse(master_playlist_path, media_type="application/vnd.apple.mpegurl")


@router.get("/{movie_id}/{segment_filename}")
async def serve_hls_segment(movie_id: int, segment_filename: str, db: Session = Depends(get_db)):
    """
    Serve individual .ts segments for HLS playback.
    """
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    hls_directory = Path(movie.file_path).parent / "hls"

    # Dynamically find the correct resolution folder
    possible_paths = [
        hls_directory / segment_filename,                      # Direct in /hls/
        hls_directory / f"{Path(movie.file_path).stem}_4K_{segment_filename}",  # 4K
        hls_directory / f"{Path(movie.file_path).stem}_2K_{segment_filename}",  # 2K
        hls_directory / f"{Path(movie.file_path).stem}_1080p_{segment_filename}",  # 1080p
        hls_directory / f"{Path(movie.file_path).stem}_720p_{segment_filename}",  # 720p
        hls_directory / f"{Path(movie.file_path).stem}_480p_{segment_filename}",  # 480p
    ]

    # Find the correct file
    segment_path = next((path for path in possible_paths if path.exists()), None)

    if not segment_path:
        raise HTTPException(status_code=404, detail="Segment file not found")

    return FileResponse(segment_path, media_type="video/mp2t")  # MPEG-TS format


@router.get("/search", response_model=list[MovieDTO])
async def search_movies(
    query: str = Query(..., min_length=2, title="Search Query"),
    limit: int = Query(10, ge=1, le=100, title="Limit"),
    offset: int = Query(0, ge=0, title="Offset"),
    db: Session = Depends(get_db)
):
    """
    Search for movies using full-text search.
    """
    movie_service = MovieService(db)
    movies = movie_service.search_movies(query, limit, offset)
    return movies