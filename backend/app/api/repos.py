import os
import shutil
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form, Depends
from typing import Optional, List
from app.core.config import settings
from app.core import storage
from app.services.ingestion import clone_github_repo, extract_zip, ingest_repository
from app.services.embedding import build_faiss_index
from app.services.analysis import run_static_analysis, build_dependency_graph
from app.api.auth import get_current_user
import re

router = APIRouter(prefix="/repos", tags=["repositories"])


def _get_repo_name_from_url(url: str) -> str:
    match = re.search(r"github\.com/[^/]+/([^/]+?)(?:\.git)?$", url)
    if match:
        return match.group(1)
    return url.rstrip("/").split("/")[-1]


def _process_repo(repo_id: str, repo_path: str, index_dir: str):
    """Background task: ingest → embed → save metadata."""
    try:
        storage.update_repo(repo_id, status="processing")

        chunks, stats = ingest_repository(repo_path)
        if not chunks:
            storage.update_repo(repo_id, status="error", error_message="No code files found in repository")
            return

        build_faiss_index(chunks, index_dir)

        storage.update_repo(
            repo_id,
            status="ready",
            file_count=stats["file_count"],
            chunk_count=stats["chunk_count"],
            language_stats=stats["language_stats"],
            faiss_index_path=index_dir,
        )

    except Exception as e:
        storage.update_repo(repo_id, status="error", error_message=str(e)[:500])


@router.post("/github", status_code=201)
async def ingest_github(
    github_url: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
):
    """Ingest a public GitHub repository."""
    if "github.com" not in github_url:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")

    repo = storage.create_repo(
        name=_get_repo_name_from_url(github_url),
        source_type="github",
        user_id=current_user["id"],
        github_url=github_url,
    )
    repo_id = repo["id"]
    repo_path = os.path.join(settings.UPLOAD_DIR, repo_id, "repo")
    index_dir = os.path.join(settings.FAISS_INDEX_PATH, repo_id)

    storage.update_repo(repo_id, local_path=repo_path)

    # Clone the repo
    try:
        clone_github_repo(github_url, repo_path, token=settings.GITHUB_TOKEN)
    except Exception as e:
        storage.update_repo(repo_id, status="error", error_message=f"Clone failed: {str(e)[:300]}")
        raise HTTPException(status_code=422, detail=f"Failed to clone repo: {e}")

    background_tasks.add_task(_process_repo, repo_id, repo_path, index_dir)
    return storage.get_repo(repo_id)


@router.post("/upload", status_code=201)
async def ingest_zip(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
):
    """Ingest a ZIP file upload."""
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported")

    repo = storage.create_repo(
        name=file.filename.replace(".zip", ""),
        source_type="zip",
        user_id=current_user["id"],
    )
    repo_id = repo["id"]
    upload_dir = os.path.join(settings.UPLOAD_DIR, repo_id)
    zip_path = os.path.join(upload_dir, "upload.zip")
    os.makedirs(upload_dir, exist_ok=True)

    contents = await file.read()
    if len(contents) > settings.MAX_REPO_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large (max {settings.MAX_REPO_SIZE_MB}MB)")

    with open(zip_path, "wb") as f:
        f.write(contents)

    repo_path = extract_zip(zip_path, os.path.join(upload_dir, "repo"))
    index_dir = os.path.join(settings.FAISS_INDEX_PATH, repo_id)

    storage.update_repo(repo_id, local_path=repo_path)
    background_tasks.add_task(_process_repo, repo_id, repo_path, index_dir)
    return storage.get_repo(repo_id)


@router.get("/")
def list_repos(current_user: dict = Depends(get_current_user)):
    return storage.list_repos(user_id=current_user["id"])


@router.get("/{repo_id}")
def get_repo(repo_id: str, current_user: dict = Depends(get_current_user)):
    repo = storage.get_repo(repo_id)
    if not repo or repo.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.delete("/{repo_id}", status_code=204)
def delete_repo(repo_id: str, current_user: dict = Depends(get_current_user)):
    repo = storage.get_repo(repo_id)
    if not repo or repo.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Cleanup files
    local_path = repo.get("local_path")
    if local_path and os.path.exists(local_path):
        shutil.rmtree(os.path.dirname(local_path), ignore_errors=True)
    faiss_path = repo.get("faiss_index_path")
    if faiss_path and os.path.exists(faiss_path):
        shutil.rmtree(faiss_path, ignore_errors=True)
    storage.delete_repo(repo_id)


@router.get("/{repo_id}/analysis")
def get_analysis(repo_id: str, current_user: dict = Depends(get_current_user)):
    repo = storage.get_repo(repo_id)
    if not repo or repo.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo["status"] != "ready":
        raise HTTPException(status_code=404, detail="Repository not ready")
    return run_static_analysis(repo["local_path"])


@router.get("/{repo_id}/dependencies")
def get_dependency_graph(repo_id: str, current_user: dict = Depends(get_current_user)):
    repo = storage.get_repo(repo_id)
    if not repo or repo.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo["status"] != "ready":
        raise HTTPException(status_code=404, detail="Repository not ready")
    return build_dependency_graph(repo["local_path"])
