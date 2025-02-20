import os
import subprocess
from pathlib import Path

def convert_to_hls(input_video_path: str, output_dir: str):
    """
    Convert an MP4 video to HLS format (.m3u8 + .ts segments).
    
    Args:
        input_video_path (str): Path to the uploaded video file.
        output_dir (str): Directory where HLS files will be saved.

    Returns:
        str: Path to the .m3u8 manifest file.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)  # Create output directory if it doesn't exist
    
    filename = os.path.basename(input_video_path).rsplit(".", 1)[0]  # Extract filename without extension
    output_m3u8_path = os.path.join(output_dir, f"{filename}.m3u8")

    command = [
        "ffmpeg",
        "-i", input_video_path,        # Input file
        "-c:v", "h264",                # Encode video as H.264
        "-b:v", "2500k",               # Bitrate
        "-c:a", "aac",                 # Encode audio as AAC
        "-ac", "2",                     # Stereo audio
        "-strict", "experimental",      # Use experimental aac codec if needed
        "-f", "hls",                    # Output format
        "-hls_time", "10",              # Segment duration (10 seconds)
        "-hls_playlist_type", "vod",    # Set as Video on Demand (VOD)
        "-hls_segment_filename", os.path.join(output_dir, f"{filename}_%03d.ts"),  # TS segment pattern
        output_m3u8_path
    ]

    # Run FFmpeg command
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_m3u8_path
    except subprocess.CalledProcessError as e:
        print(f"Error converting video: {e}")
        return None
