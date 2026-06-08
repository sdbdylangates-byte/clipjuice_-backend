from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Form # Add Form

# ... (rest of your imports)

@web_app.post("/process-video")
async def process_video(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    option: str = Form("720p") # This captures the dropdown choice
):
    # Map the user selection to specific FFmpeg arguments
    # 720p is the default, 1080p is high quality, mute removes audio
    if option == "1080p":
        scale_val = "scale=-1:1080"
        audio_val = None
    elif option == "mute":
        scale_val = "scale=-1:720"
        audio_val = "an" # FFmpeg command to remove audio
    else:
        scale_val = "scale=-1:720"
        audio_val = None

    # ... (Your logic inside the try block)
    # Update your FFmpeg run to include the variables:
    cmd = ffmpeg.input(input_path).output(output_path, vf=scale_val)
    if audio_val:
        cmd = cmd.output(output_path, an=None) # Correct syntax depends on library
    
    # Simple example for your current workflow:
    # Just pass the scale variable into your current ffmpeg logic
    (
        ffmpeg
        .input(input_path)
        .output(output_path, vf=scale_val) 
        .run(cmd=ffmpeg_bin, overwrite_output=True)
    )
    # ...