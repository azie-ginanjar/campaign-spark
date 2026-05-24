from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os

from backend.api.routes import generate, monetization, auth

app = FastAPI(title="CampaignSpark API", version="1.0.0")

# Security Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1"]
)

# Mount API routes
app.include_router(generate.router, prefix="/api/v1", tags=["Generate"])
app.include_router(monetization.router, prefix="/api/v1", tags=["Monetization"])
app.include_router(auth.router, prefix="/api/v1", tags=["Auth"])

# Get absolute path to frontend directory
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

# Mount static files to serve JS/CSS
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Catch-all route to serve the SPA index.html
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse(os.path.join(frontend_dir, "index.html"))
