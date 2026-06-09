from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import ffmpeg
import imageio_ffmpeg
import os
import shutil
import uuid

# --- Initialize App ---
web_app = FastAPI()

# --- Middleware ---
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration ---
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()

def cleanup(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

# --- Routes ---
@web_app.get("/")
def read_root():
    return {"status": "ListingFlow Engine is active."}

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

    # Save uploaded file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Start FFmpeg pipeline
        stream = ffmpeg.input(input_path)

        # 1. Stabilization (Deshake) - Cleans up shaky handheld footage
        stream = stream.filter('deshake')

        # 2. Cinematic Zoom (Ken Burns Effect) - Adds motion and vertical crop (9:16)
        stream = stream.filter('zoompan', zoom='min(zoom+0.0015,1.25)', d=125, s='720x1280', fps=30)

        # 3. Branding (Logo Overlay)
        if logo:
            logo_path = os.path.join(UPLOAD_DIR, f"logo_{uid}.png")
            with open(logo_path, "wb") as buffer:
                shutil.copyfileobj(logo.file, buffer)
            
            logo_input = ffmpeg.input(logo_path)
            # Overlay at bottom-right corner with 10px padding
            stream = stream.overlay(logo_input, x='main_w-overlay_w-10', y='main_h-overlay_h-10')
            background_tasks.add_task(cleanup, logo_path)

        # 4. Final Output
        stream = stream.output(output_path, vcodec='libx264', crf=23, preset='veryfast')
        stream.run(cmd=ffmpeg_bin, overwrite_output=True)

        # Cleanup
        cleanup(input_path)
        background_tasks.add_task(cleanup, output_path)

        return FileResponse(output_path, media_type='video/mp4', filename='listing_pro.mp4')

    except Exception as e:
        if os.path.exists(input_path): cleanup(input_path)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")