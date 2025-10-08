from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from routers.video_processor import router as video_processor_router

app = FastAPI(
    title="Video API",
    description="Backend API for video monorepo with batch video processing",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(video_processor_router)

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

class VideoInfo(BaseModel):
    id: str
    title: str
    description: str
    duration: int
    url: str

# Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    return {"message": "Welcome to Video API"}

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        message="API is running",
        version="0.1.0"
    )

@app.get("/api/videos", response_model=list[VideoInfo])
async def get_videos():
    # Mock data - replace with actual database queries
    return [
        VideoInfo(
            id="1",
            title="Sample Video 1",
            description="This is a sample video",
            duration=120,
            url="https://example.com/video1.mp4"
        ),
        VideoInfo(
            id="2", 
            title="Sample Video 2",
            description="Another sample video",
            duration=180,
            url="https://example.com/video2.mp4"
        )
    ]

@app.get("/api/videos/{video_id}", response_model=VideoInfo)
async def get_video(video_id: str):
    # Mock data - replace with actual database query
    return VideoInfo(
        id=video_id,
        title=f"Video {video_id}",
        description=f"Description for video {video_id}",
        duration=150,
        url=f"https://example.com/video{video_id}.mp4"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
