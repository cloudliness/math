import os
import json
import uuid
import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.core.rag_engine import get_rag_engine

router = APIRouter()

CHATS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "chats")

class Message(BaseModel):
    role: str
    content: str
    sources: Optional[list[dict]] = None
    flow_data: Optional[dict] = None
    mafs_data: Optional[dict] = None

class ChatSession(BaseModel):
    id: str
    title: str
    updated_at: str
    messages: List[Message]

class ChatRequest(BaseModel):
    session_id: str
    message: str
    active_documents: Optional[List[str]] = None

class ChatResponse(BaseModel):
    response: str
    sources: list[dict]
    flow_data: Optional[dict] = None
    mafs_data: Optional[dict] = None

def get_session_path(session_id: str) -> str:
    os.makedirs(CHATS_DIR, exist_ok=True)
    return os.path.join(CHATS_DIR, f"{session_id}.json")

def load_session(session_id: str) -> Optional[dict]:
    path = get_session_path(session_id)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

def save_session(session_data: dict):
    path = get_session_path(session_data["id"])
    with open(path, "w") as f:
        json.dump(session_data, f, indent=2)

@router.post("/chat/session", response_model=ChatSession)
async def create_session():
    session_id = str(uuid.uuid4())
    session_data = {
        "id": session_id,
        "title": "New Chat",
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "messages": []
    }
    save_session(session_data)
    return session_data

@router.get("/chat/session")
async def list_sessions():
    os.makedirs(CHATS_DIR, exist_ok=True)
    sessions = []
    for filename in os.listdir(CHATS_DIR):
        if filename.endswith(".json"):
            path = os.path.join(CHATS_DIR, filename)
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    sessions.append({
                        "id": data["id"],
                        "title": data["title"],
                        "updated_at": data["updated_at"]
                    })
            except Exception:
                pass
    # Sort by updated_at descending
    sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    return sessions

@router.get("/chat/session/{session_id}")
async def get_session(session_id: str):
    session = load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.delete("/chat/session/{session_id}")
async def delete_session(session_id: str):
    path = get_session_path(session_id)
    if os.path.exists(path):
        os.remove(path)
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Session not found")

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    session = load_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Generate title if first message
        if len(session["messages"]) == 0:
            # Simple title generation: first 30 chars of the message
            session["title"] = request.message[:30] + ("..." if len(request.message) > 30 else "")

        # Append user message
        session["messages"].append({
            "role": "user",
            "content": request.message
        })
        
        # Run RAG
        engine = get_rag_engine()
        result = engine.query(request.message, active_documents=request.active_documents)
        
        # Append assistant message
        session["messages"].append({
            "role": "assistant",
            "content": result["response"],
            "sources": result["sources"],
            "flow_data": result.get("flow_data"),
            "mafs_data": result.get("mafs_data")
        })
        
        # Update timestamp and save
        session["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save_session(session)
        
        return ChatResponse(
            response=result["response"],
            sources=result["sources"],
            flow_data=result.get("flow_data"),
            mafs_data=result.get("mafs_data")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

