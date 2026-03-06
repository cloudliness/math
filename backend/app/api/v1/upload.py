import os
import shutil
import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel
from typing import Dict
from app.core.rag_engine import get_rag_engine
from app.core.websocket import manager

router = APIRouter()

# Store active uploads status
upload_statuses: Dict[str, dict] = {}

@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data"))

@router.post("/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, file.filename)
    
    try:
        # Save the uploaded file immediately
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # Initialize status
        upload_statuses[file.filename] = {
            "status": "processing",
            "filename": file.filename,
            "chunks_indexed": 0,
            "error": None
        }
        
        # Schedule the slow ingestion in the background
        background_tasks.add_task(process_ingestion, file.filename, file_path)
        
        return {
            "status": "processing",
            "filename": file.filename,
            "message": f"Upload received. Processing '{file.filename}' in background."
        }
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

async def process_ingestion(filename: str, file_path: str):
    try:
        await manager.broadcast(f"Starting ingestion for {filename}...")
        await manager.broadcast(f"Parsing PDF with LlamaParse...")
        
        # Run synchronous LlamaParse in executor
        loop = asyncio.get_event_loop()
        engine = get_rag_engine()
        num_chunks = await loop.run_in_executor(None, engine.ingest_file, file_path)
        
        upload_statuses[filename] = {
            "status": "success",
            "filename": filename,
            "chunks_indexed": num_chunks,
            "error": None
        }
        await manager.broadcast(f"Successfully indexed {num_chunks} chunks into Vector DB.")
        await manager.broadcast(f"COMPLETE|{filename}|{num_chunks}") # Special token for frontend
        
    except Exception as e:
        upload_statuses[filename] = {
            "status": "error",
            "filename": filename,
            "chunks_indexed": 0,
            "error": str(e)
        }
        await manager.broadcast(f"Error during ingestion: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)

@router.get("/upload/status/{filename}")
async def get_upload_status(filename: str):
    if filename not in upload_statuses:
        return {"status": "unknown"}
    return upload_statuses[filename]

@router.get("/documents")
async def list_documents():
    os.makedirs(DATA_DIR, exist_ok=True)
    files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(".pdf")]
    return {"documents": files, "count": len(files)}

@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    # Security: prevent directory traversal
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(DATA_DIR, safe_filename)
    
    # 1. Delete from RAG engine
    try:
        engine = get_rag_engine()
        engine.delete_document(safe_filename)
    except Exception as e:
        print(f"Error removing document from VectorDB: {e}")
        # Proceed to delete from disk anyway
    
    # 2. Delete from disk
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Update statuses if it exists there
    if safe_filename in upload_statuses:
        del upload_statuses[safe_filename]
        
    return {"status": "success", "message": f"Deleted {safe_filename}"}

