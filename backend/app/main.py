from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.v1 import chat, upload
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="Discrete Math RAG API")

# Configure CORS - support localhost dev and Railway production
allowed_origins = ["http://localhost:3000", "http://localhost:5173"]
production_origins = os.getenv("ALLOWED_ORIGINS")
if production_origins:
    allowed_origins.extend(production_origins.split(","))
else:
    # In production on Railway, allow the app's own domain
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])

# Mount static files (for direct asset access)
app.mount("/static", StaticFiles(directory="static"), name="static")

# SPA fallback: serve index.html for all non-API routes
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # If the request is for an API route that wasn't matched, return 404
    if full_path.startswith("api/"):
        return {"detail": "Not Found"}
    # If the file exists in static, serve it
    static_file = f"static/{full_path}"
    if os.path.isfile(static_file):
        return FileResponse(static_file)
    # Otherwise, serve the SPA entry point
    return FileResponse("static/index.html")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
