from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import ffmpeg
import imageio_ffmpeg
import os
import shutil
import uuid

# 1. INITIALIZE APP (This must be first)
web_app = FastAPI()

# 2. MIDDLEWARE (Configures CORS so your frontend can talk to this backend)
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. CONFIGURATION & HELPERS
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()

def cleanup(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

# 4. ROUTES
@web_app.get("/")
def read_root():
    return {"status": "ClipJuice Backend is operational."}

@web_app.post("/process-video")
async def process_video(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    option: str = Form("720p")
):
    uid = uuid.uuid4()
    input_path = os.path.join(UPLOAD_DIR, f"{uid}_{file.filename}")
    output_path = os.path.join(UPLOAD_DIR, f"processed_{uid}.mp4")

    # Determine settings based on user selection
    scale_val = "scale=-1:720"
    if option == "1080p":
        scale_val = "scale=-1:1080"
    
    try:
        # Save the uploaded file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process with FFmpeg
        # If "mute" is selected, we add an audio filter
        stream = ffmpeg.input(input_path)
        if option == "mute":
            stream = stream.output(output_path, vf=scale_val, an=None)
        else:
            stream = stream.output(output_path, vf=scale_val)
        
        stream.run(cmd=ffmpeg_bin, overwrite_output=True)

        # Cleanup input immediately
        cleanup(input_path)

        # Schedule output cleanup for after response
        background_tasks.add_task(cleanup, output_path)

        return FileResponse(output_path, media_type='video/mp4', filename='processed_clip.mp4')

    except Exception as e:
        cleanup(input_path)
        cleanup(output_path)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")