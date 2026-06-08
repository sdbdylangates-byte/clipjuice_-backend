from fastapi import FastAPI, UploadFile, File, HTTPException
import ffmpeg
import imageio_ffmpeg
import os
import shutil
import uuid

# 1. Get the path to the internal ffmpeg binary
ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()

web_app = FastAPI()

# Directory for temporary files
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@web_app.get("/")
def read_root():
    return {"status": "Video processing server is live and ready!"}

@web_app.post("/process-video")
async def process_video(file: UploadFile = File(...)):
    input_filename = f"{uuid.uuid4()}_{file.filename}"
    output_filename = f"processed_{uuid.uuid4()}.mp4"
    
    input_path = os.path.join(UPLOAD_DIR, input_filename)
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    try:
        # Save the uploaded file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process with ffmpeg-python using the internal binary
        # We pass cmd=ffmpeg_bin to ensure it uses the file we installed via pip
        (
            ffmpeg
            .input(input_path)
            .output(output_path, vf="scale=-1:720")
            .run(cmd=ffmpeg_bin, overwrite_output=True)
        )

        return {"message": "Video processed successfully", "file": output_filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    finally:
        # Cleanup
        if os.path.exists(input_path):
            os.remove(input_path)