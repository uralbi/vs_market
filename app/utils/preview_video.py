import subprocess, os, tempfile
from fastapi import FastAPI, HTTPException
from app.services.movie_service import MovieService
from app.infra.database.models import MovieModel
from pathlib import Path


def filter_m3u8(movie, target_seconds):
    """
    Reads the existing 480p.m3u8, removes unneeded TS files, and creates a Preview_480p.m3u8.
    """
    print('filtering... ')
    movie_file_path = movie.file_path  # Example: media/movies/Python/Python.mp4
    ts_folder = Path(os.path.dirname(movie_file_path)) / "hls"
    
    org_m3u8_path = find_480p_m3u8(movie_folder=str(ts_folder))
    preview_m3u8_path = ts_folder / "480p_preview.m3u8"
    
    if preview_m3u8_path:
        return preview_m3u8_path
    
    if not org_m3u8_path:
        raise HTTPException(status_code=404, detail="Original HLS playlist not found")
    
    org_m3u8_path = Path(org_m3u8_path)

    lines = org_m3u8_path.read_text().splitlines()
    new_lines = [
        "#EXTM3U", "#EXT-X-VERSION:3", "#EXT-X-TARGETDURATION:19",
        "#EXT-X-MEDIA-SEQUENCE:0", "#EXT-X-PLAYLIST-TYPE:VOD",
        ]

    current_time = 0  
    ids = 0
    last_line = ''
    for i in range(len(lines)):
        if ids >= len(target_seconds):
            break
        line = lines[i]
        if line.startswith("#EXTINF:"):
            duration = float(line.split(":")[1].split(",")[0])  
            current_time += duration
            print('c_time', round(current_time,2), target_seconds[ids])
            if target_seconds[ids] < current_time: 
                new_lines.append(line)  
                new_lines.append(lines[i + 1])
                ids += 1
                i+=1
            else:
                i+=1
    new_lines.append("#EXT-X-ENDLIST")
    
    preview_m3u8_path.write_text("\n".join(new_lines))
    return preview_m3u8_path



def find_480p_m3u8(movie_folder: str) -> str:
    """
    Finds the .m3u8 playlist file ending with '480p.m3u8' in the given folder.
    Returns the full file path if found, otherwise raises an exception.
    """
    for file in os.listdir(movie_folder):
        if file.endswith("480p.m3u8"):
            return os.path.join(movie_folder, file)
    return None
