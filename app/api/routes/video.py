from fastapi import APIRouter, UploadFile, Form, Depends, Security, HTTPException, File, Query, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.services.movie_service import MovieService
from app.infra.database.db import get_db
from app.infra.database.models import MovieModel, MovieLikeModel, OrderModel
from app.domain.security.auth_user import user_authorization, user_creator_auth, user_admin_auth
from app.infra.tasks.vid_tasks import process_video_hls, generate_thumbnail_task
from app.domain.dtos.movie import MovieDTO, UpdateMovieRequest
from app.infra.kafka.kafka_producer import send_kafka_message
from app.services.payment_service import PaymentService
from app.services.order_service import OrderService
from app.utils.preview_video import filter_m3u8
from app.domain.security.signed_url import generate_signed_url, generate_signed_key_url, verify_signed_enc_url
from app.domain.security.signed_url import verify_signed_url, \
        update_variant_playlists_with_signed_urls, \
        update_m3u8_with_signed_urls, generate_signature
from app.services.image_service import ImageService
import os, shutil, time, io
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel

load_dotenv()

router = APIRouter(
    prefix="/api/movies",
    tags=["API_Movies"]
)

token_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


@router.get("/encryption_key")
async def get_encryption_key(exp: str, sig: str):
    """
    Serve the AES encryption key only to authorized users with a valid signed URL.
    """

    if not verify_signed_enc_url(exp, sig):  # Validate the request
        raise HTTPException(status_code=403, detail="Unauthorized or expired key request")

    key_path = "app/domain/security/encryption.key"
    return FileResponse(key_path, media_type="application/octet-stream")


@router.get("/generate_qr")
def generate_qr(movie_id: int, token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """ Generate a QR Code for payment (Simulated) """

    user = user_authorization(token, db)
    # qr = qrcode.make(f"pay://payment_link?movie={movie_id}")  # Simulated payment link
    # qr_path = f"temp_qr_{movie_id}.png"
    # qr.save(qr_path)
    
    order = db.query(OrderModel).filter(
        OrderModel.user_id == user.id, 
        OrderModel.movie_id == movie_id, 
    ).first()
    if not order:
        order = OrderModel(user_id=user.id, movie_id=movie_id, status="PENDING")
        db.add(order)
        db.commit()
    
    order.status="COMPLETED"
    db.commit()
    
    return {"qr_path": "media/movie_50.png", "price": 100}
    # return FileResponse(qr_path)


@router.post("/purchase/{movie_id}")
def purchase_video(movie_id: int, token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """Creates an order and simulates a payment processing"""
    user = user_authorization(token, db)
    movie_service = MovieService(db)
    movie = movie_service.get_movie_by_id(movie_id)
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Create order
    order = OrderModel(user_id=user.id, movie_id=movie.id, status="PENDING")
    db.add(order)
    db.commit()
    
    # Simulate payment processing (later integrate with Stripe, PayPal)
    pay_service = PaymentService(order, db)
    pay_service.payment_success()
    return {"message": "Purchase completed" if order.status == "completed" else "Payment failed"}


@router.put("/{id}")
async def update_movie(id: int, 
                       request: UpdateMovieRequest = Depends(),
                       token: str = Depends(token_scheme), 
                       db: Session = Depends(get_db)):
    """
    Update a movie's title, description, visibility, or thumbnail.
    """
    user = user_authorization(token, db)
    user_creator_auth(user)
    
    movie_service = MovieService(db)
    movie = movie_service.get_movie_by_id(id, user)
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    if movie.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    thumbnail = request.thumbnail_path
    
    if thumbnail:
        upload_dir = "media/movies/thumbs"
        os.makedirs(upload_dir, exist_ok=True)
        file_ext = os.path.splitext(thumbnail.filename)[1].lower()
        thumbnail_filename = f"movie_{id}{file_ext}"
        thumbnail_path = os.path.join(upload_dir, thumbnail_filename)
        with open(thumbnail_path, "wb") as buffer:
            shutil.copyfileobj(thumbnail.file, buffer)        
        img_service = ImageService()
        try:
            thumbnail_path = await img_service.process_and_store_thumbnails(thumbnail_path, upload_dir)
        except Exception as e:
            print("error in processing image:", e)
        movie_service.update_movie_thumbnail(id, thumbnail_path)

    update_data = {}
    if request.title is not None and request.title != movie.title:
        update_data["title"] = request.title
    if request.description is not None and request.description != movie.description:
        update_data["description"] = request.description
    if request.price is not None and request.price != movie.price:
        update_data["price"] = request.price
    if request.is_public is not None and request.is_public != movie.is_public:
        update_data["is_public"] = request.is_public
    
    if update_data:
        updated_movie = movie_service.update_movie(id, user.id, update_data)
    else:
        updated_movie = movie  # No changes to title/description/is_public

    return {"message": "Movie updated successfully", "movie": updated_movie}


@router.get("/my_orders")
def get_my_ordered_movies(token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """
    Fetch all movies uploaded by the authenticated user.
    """
    user = user_authorization(token, db)  # Extract user from token
    
    order_service = OrderService(db)
    my_orders = order_service.get_user_orders(user.id)
    # order: user_id, movie_id, status, created_at
    movie_service = MovieService(db)    
    orders_with_movies = []
    for order in my_orders:
        try:
            movie = movie_service.get_movie_by_id(order.movie_id)  # Get movie object
            if movie:
                orders_with_movies.append({
                    "user_id": order.user_id,
                    "movie": movie,                                 # Replace movie_id with movie object
                    "status": order.status,
                    "created_at": order.created_at
                })
        except HTTPException as e:
            if e.status_code == 404:                                # Handle movie not found or not accessible
                continue

    return orders_with_movies


@router.get("/my")
def get_my_movies(token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """
    Fetch all movies uploaded by the authenticated user.
    """
    user = user_authorization(token, db)  # Extract user from token
    movie_service = MovieService(db)
    movies = movie_service.get_user_movies(user.id)

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found for this user")

    return movies


@router.delete("/{id}")
def delete_movie(id: int, token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """
    Delete a movie by ID.
    """
    user = user_authorization(token, db)
    user_creator_auth(user)
    movie_service = MovieService(db)
    deleted = movie_service.delete_movie(id, user.id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Movie not found")

    return {"message": "Movie deleted successfully"}


@router.get("/search")
def search_movies(query: str, db: Session = Depends(get_db)):
    """
    Search for movies using full-text search on title and description.
    """
    
    # send_kafka_message(
    #     topic="movie_search",
    #     key="search",
    #     message={"query": query, "timestamp": str(datetime.datetime.now())},
    # )

    movie_service = MovieService(db)
    return movie_service.search_movies(query)


@router.get("/{id}")
def get_movie(id: int, token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """
    Fetch the movies.
    """
    try:
        user = user_authorization(token, db)
    except Exception as e:
        user = None
    movie_service = MovieService(db)
    movie = movie_service.get_movie_by_id(id, user)
    return movie


@router.get("/")
def get_movies(
    limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),  db: Session = Depends(get_db)
        ):
    """
    Fetch public movies with pagination.
    """
    movie_service = MovieService(db)
    movies = movie_service.get_movies(limit, offset)
    return movies


class AccessTokenRequest(BaseModel):
    access_token: str
    
@router.post("/{movie_id}/progress")
def get_movie_progress(movie_id: int, payload: AccessTokenRequest, db: Session = Depends(get_db)):
    """
    Retrieve the last watched progress of the user for a given movie.
    """
    token = payload.access_token
    user = user_authorization(token, db)
    movie_service = MovieService(db)

    view = movie_service.get_movie_progress(movie_id, user.id)

    return {"progress": view.progress if view else 0}


class ProgressRequest(BaseModel):
    access_token: str
    progress: int
    
@router.post("/{movie_id}/track")
def track_movie(movie_id: int, payload: ProgressRequest, db: Session = Depends(get_db)):
    """
    Save user's last watched progress using the service layer.
    """
    token = payload.access_token
    progress = payload.progress
    user = user_authorization(token, db)
    movie_service = MovieService(db)
    movie_service.track_movie_progress(movie_id, user.id, progress)
    
    return {"message": "Progress saved"}


UPLOAD_FOLDER = "media/movies/"
ALLOWED_VIDEO_FORMATS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}


@router.post("/upload")
async def upload_movie(
    token: str = Depends(token_scheme),
    title: str = Form(...),
    price: int = Form(...),
    description: str = Form(...),
    is_public: bool = Form(True),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
    ):

    user = user_authorization(token, db)
    user_creator_auth(user)
    
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

    mov_service = MovieService(db) # Create movie entry in the database
    movie = mov_service.create_movie(title, description, price, file_path, is_public, owner_id=user.id)
    
    process_video_hls.delay(file_path, HLS_FOLDER, movie.id) # Trigger HLS conversion via Celery
    
    generate_thumbnail_task.delay(movie.id, str(file_path), f"movie_{movie.id}")

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


@router.get("/preview/{movie_id}/hls")
async def get_preview_m3u8(movie_id: str, db: Session = Depends(get_db)):
    """
    Generates and serves Preview_480p.m3u8 by filtering the existing 480p.m3u8.
    """
    
    movie_service = MovieService(db)
    movie = movie_service.get_movie_by_id(movie_id)
    preview_m3u8 = filter_m3u8(movie)
    # update_m3u8_with_signed_urls(preview_m3u8, movie_id)
    if not preview_m3u8.exists():
        raise HTTPException(status_code=403, detail="Not Found")

    signed_key_url = generate_signed_key_url(movie_id)

    with open(preview_m3u8, "r") as file:
        lines = file.readlines()

    updated_lines = []
    for line in lines:
        line = line.strip()

        if "EXT-X-KEY" in line:
            updated_lines.append(f'#EXT-X-KEY:METHOD=AES-128,URI="{signed_key_url}"\n')

        elif line.endswith(".ts"):
            signed_segment_url = generate_signed_url(movie_id, line)
            updated_lines.append(signed_segment_url + "\n")
        else:
            updated_lines.append(line + "\n")

    updated_playlist = "".join(updated_lines)

    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0"
    }

    return Response(content=updated_playlist, media_type="application/vnd.apple.mpegurl", headers=headers)


@router.get("/preview/{movie_id}/{segment_filename}")
async def serve_hls_segment(movie_id: int, segment_filename: str,
                            exp: str, sig: str, db: Session = Depends(get_db)):
    """
    Serve individual .ts segments for HLS playback.
    """
    
    if not verify_signed_url(movie_id, segment_filename, exp, sig):
        raise HTTPException(status_code=403, detail="Unauthorized or expired link")
    
    movie_service = MovieService(db)
    movie = movie_service.get_movie_by_id(movie_id)

    hls_directory = Path(movie.file_path).parent / "hls"

    # Dynamically find the correct resolution folder
    possible_paths = [
        hls_directory / segment_filename,                                       # Direct in /hls/
        hls_directory / f"{Path(movie.file_path).stem}_4K_{segment_filename}",  # 4K
        hls_directory / f"{Path(movie.file_path).stem}_2K_{segment_filename}",  # 2K
        hls_directory / f"{Path(movie.file_path).stem}_1080p_{segment_filename}",  # 1080p
        hls_directory / f"{Path(movie.file_path).stem}_720p_{segment_filename}",  # 720p
        hls_directory / f"{Path(movie.file_path).stem}_480p_{segment_filename}",  # 480p
    ]

    segment_path = next((path for path in possible_paths if path.exists()), None)

    if not segment_path:
        raise HTTPException(status_code=404, detail="Segment file not found")
    
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
        "Content-Disposition": "inline",            # Prevents browsers from forcing downloads
        "X-Content-Type-Options": "nosniff",        # Blocks MIME-type sniffing
        "Referrer-Policy": "no-referrer",           # Prevents URL tracking
        "Permissions-Policy": "interest-cohort=()", # Blocks tracking
    }
    
    return FileResponse(segment_path, media_type="application/vnd.apple.mpegurl", headers=headers)


@router.get("/{movie_id}/hls")
async def stream_hls(movie_id: int, token: str = Security(token_scheme), db: Session = Depends(get_db)):
    """
    Serve the master `.m3u8` playlist with signed URLs for variant `.m3u8` files and encryption keys.
    """
    movie_service = MovieService(db)
    movie = movie_service.get_movie_by_id(movie_id)
    
    if movie.price > 0:
        user = user_authorization(token, db)
        order_service = OrderService(db)
        if not order_service.check_order_status(user.id, movie_id):
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)    
    if not movie:
        return JSONResponse({"detail": "Movie not found"}, status_code=404)

    base_filename = Path(movie.file_path).stem
    # hls_directory = Path(movie.file_path).parent / "hls"
    
    master_playlist_path = f"{base_filename}_master.m3u8" # disk path

    base_url = f"http://127.0.0.1:8000/api/movies/master/{movie_id}"
    signed_master_url = f"{base_url}/{master_playlist_path}?exp={int(time.time()) + 600}&sig={generate_signature(movie_id, master_playlist_path)}"
    return JSONResponse({"hls_url": signed_master_url})


@router.get("/master/{movie_id}/{master_playlist_path}")
async def get_master_file(movie_id: int, master_playlist_path: str, exp: str, sig: str,):
    
    if not verify_signed_url(movie_id, master_playlist_path, exp, sig):
        raise HTTPException(status_code=401, detail="Unauthorized or expired link")
    
    base_idx = master_playlist_path.find("_master")
    base_dirname = master_playlist_path[:base_idx]    
    hls_directory = Path(f"media/movies/{base_dirname}/hls")    
    master_playlist_path = hls_directory / f"{base_dirname}_master.m3u8" # disk path
    
    if not master_playlist_path.exists():
        return JSONResponse({"detail": "HLS playlist not found"}, status_code=404)
    
    signed_playlist = io.StringIO()
    with open(master_playlist_path, "r") as file:
        for line in file:
            line = line.strip()

            if "EXT-X-KEY" in line:
                signed_key_url = generate_signed_key_url(movie_id)
                signed_playlist.write(f'#EXT-X-KEY:METHOD=AES-128,URI="{signed_key_url}"\n')

            elif line.endswith(".m3u8"):  # ✅ Sign variant playlists (.m3u8)
                signed_variant_url = f"/api/movies/segment/{movie_id}/{line}?exp={int(time.time()) + 600}&sig={generate_signature(movie_id, line)}&fld={hls_directory}"
                signed_playlist.write(signed_variant_url + "\n")

            else:
                signed_playlist.write(line + "\n")
    
    return Response(content=signed_playlist.getvalue(), media_type="application/vnd.apple.mpegurl")
 
    
@router.get("/segment/{movie_id}/{segment_filename}")
async def serve_hls_segment(movie_id: int, segment_filename: str, 
                            exp: str, sig: str, fld: str):
    """
    Serve individual `.m3u8` and `.ts` segments for HLS playback.
    """
    
    segment_path = Path(f"{fld}/{segment_filename}")
    if not segment_path.exists():
        raise HTTPException(status_code=404, detail="Segment file not found")
    updated_playlist = io.StringIO()

    if segment_filename.endswith(".m3u8"):
        
        with open(segment_path, "r") as file:
            for line in file:
                line = line.strip()

                if "EXT-X-KEY" in line:
                    # ✅ Replace encryption key with signed key URL
                    signed_key_url = generate_signed_key_url(movie_id)
                    updated_playlist.write(f'#EXT-X-KEY:METHOD=AES-128,URI="{signed_key_url}"\n')

                elif line.endswith(".ts"):  # ✅ Sign `.ts` segment files
                    signed_ts_url = (
                        f"http://127.0.0.1:8000/api/movies/segment/{movie_id}/{line}"
                        f"?exp={int(time.time()) + 600}&sig={generate_signature(movie_id, line)}&fld={fld}"
                    )
                    updated_playlist.write(signed_ts_url + "\n")

                else:
                    updated_playlist.write(line + "\n")

        return Response(content=updated_playlist.getvalue(), media_type="application/vnd.apple.mpegurl")

    segment_path = Path(f"{fld}/{segment_filename}")
    
    if not verify_signed_url(movie_id, segment_filename, exp, sig):
        raise HTTPException(status_code=401, detail="Unauthorized or expired link")

    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
        "Content-Disposition": "inline",           
        "X-Content-Type-Options": "nosniff",        
        "Referrer-Policy": "no-referrer",           
        "Permissions-Policy": "interest-cohort=()", 
    }
    return FileResponse(segment_path, media_type="application/vnd.apple.mpegurl", headers=headers)


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

