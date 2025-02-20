from app.infra.celery_fld.celery_config import celery_app
from app.utils.v_converter import convert_to_hls  # Import function


@celery_app.task
def process_video_hls(video_path: str, output_dir: str):
    """
    Celery task to convert uploaded video to HLS format.
    """
    print(f"Processing video: {video_path}")
    hls_path = convert_to_hls(video_path, output_dir)
    
    if hls_path:
        print(f"Conversion successful: {hls_path}")
        return {"status": "success", "hls_path": hls_path}
    else:
        print("Conversion failed")
        return {"status": "failed"}
