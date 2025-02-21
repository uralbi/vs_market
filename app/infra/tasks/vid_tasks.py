from app.infra.celery_fld.celery_config import celery_app
from app.utils.v_converter import convert_to_hls  # Import function
from pathlib import Path
import os 

import logging
import logging.config
from app.core.config import settings
logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def process_video_hls(self, video_path: str, output_dir: str):
    """
    Celery task to convert an uploaded video to HLS format asynchronously.
    """
    try:
        logger.info(f"Processing video: {video_path}")

        # Ensure output directory exists
        # filename = os.path.splitext(os.path.basename(video_path))[0]
        # output_dir = f"{output_dir}/{filename}"
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        hls_path = convert_to_hls(video_path, output_dir)

        if hls_path:
            logger.info(f"Conversion successful: {hls_path}")
            return {"status": "success", "hls_path": hls_path}
        else:
            logger.error("Conversion failed")
            return {"status": "failed"}
    
    except Exception as e:
        logger.exception(f"Error processing video: {e}")
        return {"status": "error", "message": str(e)}
