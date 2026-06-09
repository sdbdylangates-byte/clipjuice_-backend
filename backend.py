from fastapi import FastAPI, UploadFile, File
from supabase import create_client
import os

# --- Configuration ---
# 1. Your Supabase URL (already have this)
SUPABASE_URL = "https://vrjyrxdorzttiuvjltou.supabase.co"

# 2. IMPORTANT: Paste your 'anon' public key here
# You can find this in your Supabase Dashboard -> Settings -> API
SUPABASE_KEY = "PASTE_YOUR_ANON_PUBLIC_KEY_HERE"

# --- Initialize ---
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI()

# --- Routes ---

@app.get("/")
def read_root():
    """Simple check to ensure server is running"""
    return {"message": "ListingFlow Backend is online and connected to Supabase!"}

@app.post("/process-video")
async def process_video(file: UploadFile = File(...)):
    """
    Receives the video file, creates a job ticket in the database,
    and returns the Job ID to the user.
    """
    try:
        # 1. Define the initial job state
        job_data = {"status": "pending"}
        
        # 2. Insert into Supabase 'video_jobs' table
        response = supabase.table("video_jobs").insert(job_data).execute()
        
        # 3. Extract the new ID
        job_id = response.data[0]['id']
        
        # 4. Return success message with the tracking ID
        return {
            "message": "Job accepted", 
            "job_id": job_id, 
            "status": "pending"
        }
        
    except Exception as e:
        # If something goes wrong, return the error
        return {"error": f"Database failure: {str(e)}"}

# --- Start the Server ---
if __name__ == "__main__":
    import uvicorn
    # This runs your server when you type 'python backend.py'
    uvicorn.run(app, host="0.0.0.0", port=8000)