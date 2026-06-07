from fastapi import FastAPI

# Renaming the instance to 'web_app'
web_app = FastAPI()

@web_app.get("/")
def read_root():
    return {"status": "ClipJuice Backend is UP"}