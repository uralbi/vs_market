import os, json, subprocess, logging
from pathlib import Path
import logging.config
from app.core.config import settings

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)


def get_video_resolution(input_video_path: str):
    """
    Extract video resolution using ffprobe.
    Returns (width, height) of the video.
    """
    command = [
        "ffprobe", 
        "-v", "error", 
        "-select_streams", "v:0", 
        "-show_entries", "stream=width,height", 
        "-of", "json", 
        input_video_path
    ]

    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        video_info = json.loads(result.stdout)
        if "streams" in video_info and video_info["streams"]:
            width = video_info["streams"][0]["width"]
            height = video_info["streams"][0]["height"]
            if width and height:
                print(f"Video resolution detected: {width} x {height}")
                return width, height
    except Exception as e:
        print(f"Error detecting resolution: {e}")
        return None, None  # Default to skipping 2K & 4K if detection fails


def convert_to_hls(input_video_path: str, output_dir: str):
    """
    Convert a video to HLS format with multiple quality options (4K, 2K, 1080p, 720p, 480p).
    
    Args:
        input_video_path (str): Path to the uploaded video file.
        output_dir (str): Directory where HLS files will be saved.

    Returns:
        str: Path to the master `.m3u8` playlist.
    """

    Path(output_dir).mkdir(parents=True, exist_ok=True)  # Ensure output directory exists
    filename = Path(input_video_path).stem  # Extract filename without extension
    width, height = get_video_resolution(input_video_path)

    # Define quality levels dynamically based on video resolution 1280 / 720
    variants = []

    if width and height:
        if width >= 3840 and height >= 2160:
            variants.append({"name": "4K", "resolution": "3840x2160", "bitrate": "12000k"})
        if width >= 2560 and height >= 1440:
            variants.append({"name": "2K", "resolution": "2560x1440", "bitrate": "8000k"})
        if width >= 1920 and height >= 1080:
            variants.append({"name": "1080p", "resolution": "1920x1080", "bitrate": "5000k"})
        if width >= 1280 and height >= 720:
            variants.append({"name": "720p", "resolution": "1280x720", "bitrate": "2800k"})
        if width >= 1100 and 600 > height >= 480:
            variants.append({"name": "Original", "resolution": f"{width}x{height}", "bitrate": "5000k"})
        if width >= 854 and height >= 480:
            variants.append({"name": "480p", "resolution": "854x480", "bitrate": "1200k"})

    variant_playlists = []

    for variant in variants:
        variant_output_m3u8 = os.path.join(output_dir, f"{filename}_{variant['name']}.m3u8")
        variant_ts_files = os.path.join(output_dir, f"{filename}_{variant['name']}_%03d.ts")

        command = [
            "ffmpeg",
            "-hwaccel", "auto",
            "-i", input_video_path,  
            "-vf", f"scale={variant['resolution']}",  # Resize video
            "-c:v", "libx264",
            "-preset", "fast",
            "-b:v", variant["bitrate"],
            "-bufsize", "5000k",
            "-threads", "4",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ac", "2",
            "-f", "hls",
            "-hls_time", "10",
            "-hls_playlist_type", "vod",
            "-hls_segment_filename", variant_ts_files,
            variant_output_m3u8
        ]

        # Run FFmpeg command
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Created HLS variant: {variant['name']} ({variant['resolution']})")
            variant_playlists.append((variant_output_m3u8, variant["bitrate"], variant["resolution"]))
        except subprocess.CalledProcessError as e:
            print(f"Error converting video {variant['name']}: {e}")

    # Generate master playlist (index.m3u8)
    master_playlist_path = os.path.join(output_dir, f"{filename}_master.m3u8")
    with open(master_playlist_path, "w") as master_playlist:
        master_playlist.write("#EXTM3U\n")
        master_playlist.write("#EXT-X-VERSION:3\n")
        for playlist, bitrate, resolution in variant_playlists:
            master_playlist.write(f"#EXT-X-STREAM-INF:BANDWIDTH={bitrate.replace('k', '000')},RESOLUTION={resolution}\n")
            master_playlist.write(f"{os.path.basename(playlist)}\n")

    return master_playlist_path


def generate_thumbnail(video_path: str, filename: str, time: int = 20) -> str:
    """
    Generate a thumbnail from the video using FFmpeg at the given time (default: 5 seconds).
    """
    THUMBNAIL_FOLDER = "media/movies/thumbs"
    thumbnail_filename = f"{filename}.jpg"
    thumbnail_path = os.path.join(THUMBNAIL_FOLDER, thumbnail_filename)

    command = [
        "ffmpeg", "-i", video_path, "-ss", str(time), "-vframes", "1",
        "-vf", "scale=320:-1", thumbnail_path, "-y"
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return thumbnail_path
    except subprocess.CalledProcessError:
        return None


def get_video_duration(video_path: str) -> float:
    """
    Get the duration of the video in seconds using FFmpeg.
    """
    try:
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-select_streams", "v:0", 
            "-show_entries", "format=duration", 
            "-of", "json", 
            video_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    
    except Exception as e:
        logger.error(f"Error getting video duration: {e}")
        return -1
    