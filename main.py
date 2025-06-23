# main.py
from fastapi import FastAPI
from api import router as course_router

app = FastAPI(title="AI Course Generator")

# Include API router (with optional prefix and tags)
app.include_router(course_router, prefix="/course", tags=["Course Generation"])

# Health check or root endpoint
@app.get("/", tags=["Health"])
def read_root():
    return {"message": "AI Course Generator backend is running"}

