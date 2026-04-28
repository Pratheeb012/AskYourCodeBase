import uuid as uuid_lib
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.core import storage
from app.services.rag import generate_rag_response, generate_architecture_summary
from app.api.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    repository_id: str
    rewrite_query: bool = True


class FeedbackRequest(BaseModel):
    feedback: str  # "positive" | "negative"


@router.post("/query")
def query_codebase(body: QueryRequest, current_user: dict = Depends(get_current_user)):
    repo = storage.get_repo(body.repository_id)
    if not repo or repo.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    if repo["status"] != "ready":
        raise HTTPException(status_code=409, detail=f"Repository not ready (status: {repo['status']})")
    if not repo.get("faiss_index_path"):
        raise HTTPException(status_code=500, detail="FAISS index not found")

    result = generate_rag_response(
        query=body.query,
        index_dir=repo["faiss_index_path"],
        top_k=8,
        rewrite=body.rewrite_query,
    )

    # Save to in-memory history
    entry = storage.add_query_history({
        "repository_id": body.repository_id,
        "query": body.query,
        "rewritten_query": result["rewritten_query"],
        "response": result["answer"],
        "retrieved_chunks": result["references"],
        "tokens_used": result["tokens_used"],
        "response_time_ms": result["response_time_ms"],
        "feedback": None,
    })

    return {
        "query_id": entry["id"],
        "original_query": body.query,
        "rewritten_query": result["rewritten_query"],
        "answer": result["answer"],
        "references": result["references"],
        "tokens_used": result["tokens_used"],
        "response_time_ms": result["response_time_ms"],
    }


@router.get("/history/{repo_id}")
def get_history(repo_id: str, current_user: dict = Depends(get_current_user), limit: int = 50):
    repo = storage.get_repo(repo_id)
    if not repo or repo.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Repository not found")
    return storage.get_query_history(repo_id, limit=limit)


@router.post("/feedback/{query_id}")
def submit_feedback(query_id: str, body: FeedbackRequest, current_user: dict = Depends(get_current_user)):
    if body.feedback not in ("positive", "negative"):
        raise HTTPException(status_code=400, detail="Feedback must be 'positive' or 'negative'")
    ok = storage.update_query_feedback(query_id, body.feedback)
    if not ok:
        raise HTTPException(status_code=404, detail="Query not found")
    return {"status": "ok"}


@router.get("/architecture/{repo_id}")
def get_architecture(repo_id: str, current_user: dict = Depends(get_current_user)):
    repo = storage.get_repo(repo_id)
    if not repo or repo.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    if repo["status"] != "ready":
        raise HTTPException(status_code=404, detail="Repository not ready")
    summary = generate_architecture_summary(repo["faiss_index_path"])
    return {"summary": summary}
