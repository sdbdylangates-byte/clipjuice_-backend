from fastapi import FastAPI, UploadFile, File
import os

web_app = FastAPI()

# Create an 'uploads' folder on the server
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@web_app.get("/")
def read_root():
    return {"status": "ClipJuice Backend is UP"}

# This allows users to send a file to your server
@web_app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save the file to the server's storage
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    return {"filename": file.filename, "message": "Video received successfully!"}