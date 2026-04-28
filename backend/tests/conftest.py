import pytest
import os
import shutil
from tempfile import TemporaryDirectory
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings

@pytest.fixture(scope="session", autouse=True)
def test_settings():
    """Mock data directories for testing."""
    with TemporaryDirectory() as temp_dir:
        original_data_dir = settings.DATA_DIR
        original_upload_dir = settings.UPLOAD_DIR
        original_faiss_path = settings.FAISS_INDEX_PATH
        
        settings.DATA_DIR = os.path.join(temp_dir, "data")
        settings.UPLOAD_DIR = os.path.join(temp_dir, "uploads")
        settings.FAISS_INDEX_PATH = os.path.join(temp_dir, "faiss")
        
        os.makedirs(settings.DATA_DIR, exist_ok=True)
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.FAISS_INDEX_PATH, exist_ok=True)
        
        # Redefine file paths in storage (since they are global)
        from app.core import storage
        storage.REPOS_FILE = os.path.join(settings.DATA_DIR, "repos.json")
        storage.USERS_FILE = os.path.join(settings.DATA_DIR, "users.json")
        
        yield settings
        
        # Restore (optional but good practice)
        settings.DATA_DIR = original_data_dir
        settings.UPLOAD_DIR = original_upload_dir
        settings.FAISS_INDEX_PATH = original_faiss_path

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
