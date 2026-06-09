from fastapi import UploadFile, File, Form # Ensure Form is imported

@web_app.post("/process-video")
async def process_video(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    logo: UploadFile = File(None), # Accepts an optional logo
    option: str = Form("720p")
):
    # ... (Keep your uid/paths logic)
    
    # 1. Setup Inputs
    video_input = ffmpeg.input(input_path)
    
    # 2. Check for Logo
    if logo:
        logo_path = os.path.join(UPLOAD_DIR, f"logo_{uid}.png")
        with open(logo_path, "wb") as buffer:
            shutil.copyfileobj(logo.file, buffer)
        
        logo_input = ffmpeg.input(logo_path)
        # Apply overlay: bottom-right corner with 10px padding
        stream = video_input.overlay(logo_input, x='main_w-overlay_w-10', y='main_h-overlay_h-10')
        background_tasks.add_task(cleanup, logo_path) # Cleanup logo too
    else:
        stream = video_input

    # 3. Apply Resizing and Process
    stream = stream.output(output_path, vf="scale=-1:720")
    stream.run(cmd=ffmpeg_bin, overwrite_output=True)

    # ... (Keep your cleanup/return logic)