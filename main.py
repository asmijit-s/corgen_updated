# main.py
from fastapi import FastAPI
from api import router as course_router

app = FastAPI(title="AI Course Generator")

# Include API router
app.include_router(course_router)

# Optional health check endpoint
@app.get("/")
def read_root():
    return {"message": "AI Course Generator backend is running"}
