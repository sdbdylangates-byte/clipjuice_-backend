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
    return {"status": "ListingFlow Cinematic Engine is active (Optimized for RAM)."}

@web_app.post("/process-video")
async def process_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    logo: UploadFile = File(None),
    option: str = Form("cinematic")
):
    uid = uuid.uuid4()
    input_path = os.path.join(UPLOAD_DIR, f"{uid}_{file.filename}")
    output_path = os.path.join(UPLOAD_DIR, f"processed_{uid}.mp4")

    # Save uploaded file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Input stream
        input_stream = ffmpeg.input(input_path)
        
        # 1. Video Pipeline (Optimized for Memory)
        # We scale to 1280x720 FIRST. This drastically reduces RAM usage for the following filters.
        video_stream = input_stream.video.filter('scale', w=1280, h=720)
        
        # Now apply heavy filters on the scaled stream
        video_stream = video_stream.filter('deshake')
        video_stream = video_stream.filter('zoompan', zoom='min(zoom+0.0015,1.25)', d=125, s='720x1280', fps=30)

        # 2. Audio Pipeline: Noise Reduction (afftdn)
        audio_stream = input_stream.audio.filter('afftdn', nr=10, nf=-25)

        # 3. Branding (Logo Overlay)
        if logo:
            logo_path = os.path.join(UPLOAD_DIR, f"logo_{uid}.png")
            with open(logo_path, "wb") as buffer:
                shutil.copyfileobj(logo.file, buffer)
            
            logo_input = ffmpeg.input(logo_path)
            video_stream = video_stream.overlay(logo_input, x='main_w-overlay_w-10', y='main_h-overlay_h-10')
            background_tasks.add_task(cleanup, logo_path)

        # 4. Combine and Output
        out = ffmpeg.output(
            video_stream, 
            audio_stream, 
            output_path, 
            vcodec='libx264', 
            acodec='aac',
            crf=23, 
            preset='veryfast' # 'veryfast' further reduces CPU/Memory spike
        )
        
        out.run(cmd=ffmpeg_bin, overwrite_output=True)

        # Cleanup
        cleanup(input_path)
        background_tasks.add_task(cleanup, output_path)

        return FileResponse(output_path, media_type='video/mp4', filename='listing_cinematic.mp4')

    except Exception as e:
        if os.path.exists(input_path): cleanup(input_path)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")