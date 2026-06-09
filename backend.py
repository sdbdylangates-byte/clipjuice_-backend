from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import ffmpeg
import imageio_ffmpeg
import os
import shutil
import uuid

# --- 1. INITIALIZE APP (Must come before routes!) ---
web_app = FastAPI()

# --- 2. MIDDLEWARE ---
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. CONFIGURATION & HELPERS ---
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()

def cleanup(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

# --- 4. ROUTES (These are now safe because web_app is defined above) ---
@web_app.get("/")
def read_root():
    return {"status": "ClipJuice Backend is operational."}

@web_app.post("/process-video")
async def process_video(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    logo: UploadFile = File(None),
    option: str = Form("720p")
):
    uid = uuid.uuid4()
    input_path = os.path.join(UPLOAD_DIR, f"{uid}_{file.filename}")
    output_path = os.path.join(UPLOAD_DIR, f"processed_{uid}.mp4")

    # Save uploaded video
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Prepare FFmpeg input
        stream = ffmpeg.input(input_path)

        # Apply Logo Overlay if provided
        if logo:
            logo_path = os.path.join(UPLOAD_DIR, f"logo_{uid}.png")
            with open(logo_path, "wb") as buffer:
                shutil.copyfileobj(logo.file, buffer)
            
            logo_input = ffmpeg.input(logo_path)
            # Overlay logo at bottom right with 10px padding
            stream = stream.overlay(logo_input, x='main_w-overlay_w-10', y='main_h-overlay_h-10')
            background_tasks.add_task(cleanup, logo_path)

        # Process with FFmpeg (Default 720p scale)
        stream = stream.output(output_path, vf="scale=-1:720")
        stream.run(cmd=ffmpeg_bin, overwrite_output=True)

        # Cleanup
        cleanup(input_path)
        background_tasks.add_task(cleanup, output_path)

        return FileResponse(output_path, media_type='video/mp4', filename='processed_clip.mp4')

    except Exception as e:
        if os.path.exists(input_path): cleanup(input_path)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")