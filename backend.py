import os
import uuid
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from moviepy.editor import VideoFileClip

web_app = FastAPI()

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

@web_app.post("/process-video")
async def process_video(file: UploadFile = File(...)):
    # Create unique names for files to avoid conflicts
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{unique_id}_{file.filename}")
    output_path = os.path.join(PROCESSED_DIR, f"trimmed_{unique_id}_{file.filename}")
    
    # Save uploaded file
    with open(input_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # Trim the video (First 5 seconds)
    try:
        with VideoFileClip(input_path) as clip:
            new_clip = clip.subclip(0, 5)
            new_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    except Exception as e:
        return {"error": str(e)}
        
    return FileResponse(output_path, media_type='video/mp4', filename="trimmed_video.mp4")