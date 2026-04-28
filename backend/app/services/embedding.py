import os
import json
import numpy as np
import faiss
from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.services.ingestion import CodeChunk

# Singleton model — loaded once
_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def embed_texts(texts: List[str]) -> np.ndarray:
    """Generate embeddings for a list of texts."""
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.astype("float32")


def build_faiss_index(chunks: List[CodeChunk], index_dir: str) -> str:
    """
    Build a FAISS index from a list of code chunks.
    Saves both the FAISS index (.faiss) and metadata (.json) files.
    Returns the directory path.
    """
    os.makedirs(index_dir, exist_ok=True)

    # Prepare texts for embedding: include file path as prefix for context
    texts = [
        f"[{chunk.file_path}]\n{chunk.content}"
        for chunk in chunks
    ]

    embeddings = embed_texts(texts)
    dimension = embeddings.shape[1]

    # Use IndexFlatIP (cosine similarity after normalization)
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # Save FAISS index
    faiss_path = os.path.join(index_dir, "index.faiss")
    faiss.write_index(index, faiss_path)

    # Save chunk metadata alongside the index
    metadata = [chunk.to_dict() for chunk in chunks]
    meta_path = os.path.join(index_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return index_dir


def load_faiss_index(index_dir: str) -> Tuple[faiss.Index, List[dict]]:
    """Load a previously built FAISS index and its metadata."""
    faiss_path = os.path.join(index_dir, "index.faiss")
    meta_path = os.path.join(index_dir, "metadata.json")

    if not os.path.exists(faiss_path):
        raise FileNotFoundError(f"FAISS index not found at {faiss_path}")

    index = faiss.read_index(faiss_path)

    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return index, metadata


def search_index(
    index_dir: str,
    query: str,
    top_k: int = 8,
) -> List[Tuple[dict, float]]:
    """
    Search the FAISS index for the most relevant code chunks.
    Returns a list of (chunk_metadata, score) tuples.
    """
    index, metadata = load_faiss_index(index_dir)

    query_embedding = embed_texts([query]).astype("float32")
    faiss.normalize_L2(query_embedding)

    scores, indices = index.search(query_embedding, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        results.append((metadata[idx], float(score)))

    return results
