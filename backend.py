from fastapi import FastAPI, UploadFile, File, HTTPException
import ffmpeg
import os
import shutil
import uuid

web_app = FastAPI()

# Directory for temporary files
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@web_app.get("/")
def read_root():
    return {"status": "Video processing server is live!"}

@web_app.post("/process-video")
async def process_video(file: UploadFile = File(...)):
    # 1. Generate unique names to prevent file overwrites
    input_filename = f"{uuid.uuid4()}_{file.filename}"
    output_filename = f"processed_{uuid.uuid4()}.mp4"
    
    input_path = os.path.join(UPLOAD_DIR, input_filename)
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    try:
        # 2. Save the uploaded file to disk
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Process with ffmpeg-python
        # Example: Resizing to 720p
        (
            ffmpeg
            .input(input_path)
            .output(output_path, vf="scale=-1:720")
            .run(overwrite_output=True)
        )

        # 4. (Optional) In a real app, you would upload the file to cloud storage (S3/GCS) here.
        # For now, we return a success message.
        return {"message": "Video processed successfully", "output": output_filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 5. Cleanup: Delete temporary files to keep server storage clean
        if os.path.exists(input_path):
            os.remove(input_path)
        # Note: In a production app, keep the output file if the user needs to download it.
        # If you want to return the file, use FastAPI's FileResponse here.