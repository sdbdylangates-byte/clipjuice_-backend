from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import ffmpeg
import imageio_ffmpeg
import os
import shutil
import uuid

# 1. Initialize App
web_app = FastAPI()

# 2. Add CORS Middleware (Essential for connecting to a Frontend website)
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your actual frontend URL (e.g., "https://clipjuice.com")
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Setup Temp Directory
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Helper to remove files after they are sent to the user
def cleanup(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()

@web_app.post("/process-video")
async def process_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Unique IDs for this specific request
    uid = uuid.uuid4()
    input_path = os.path.join(UPLOAD_DIR, f"{uid}_{file.filename}")
    output_path = os.path.join(UPLOAD_DIR, f"processed_{uid}.mp4")

    try:
        # Save upload
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process with FFmpeg
        (
            ffmpeg
            .input(input_path)
            .output(output_path, vf="scale=-1:720")
            .run(cmd=ffmpeg_bin, overwrite_output=True)
        )

        # Cleanup input file immediately
        cleanup(input_path)

        # Schedule cleanup of the output file AFTER the user downloads it
        background_tasks.add_task(cleanup, output_path)

        # Return the file to the user
        return FileResponse(output_path, media_type='video/mp4', filename='processed_video.mp4')

    except Exception as e:
        # Clean up if something failed
        cleanup(input_path)
        cleanup(output_path)
        raise HTTPException(status_code=500, detail=str(e))

@web_app.get("/")
def read_root():
    return {"status": "ClipJuice Backend is operational."}