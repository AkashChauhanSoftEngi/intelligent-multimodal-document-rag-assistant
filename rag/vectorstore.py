"""
Stage 3: MULTIMODAL RETRIEVAL

FAISS index over embeddings from all three modalities (text, table
summaries, image captions), each chunk carrying metadata for citation
(doc name, page/slide, type, and a pointer back to the original content).

FAISS itself has no hosted-API equivalent - it's a local vector search
library by design - so this is "local" regardless of the other backend
toggles. It's wrapped behind VectorStoreBase so a hosted vector DB (e.g.
Pinecone/Weaviate) could be substituted later without touching pipeline.py.
"""
import os
import pickle
from dataclasses import dataclass, asdict
from typing import List, Optional

import faiss
import numpy as np

from . import config


@dataclass
class Chunk:
    chunk_id: int
    doc_name: str
    page: int
    type: str            # "text" | "table" | "image"
    content: str          # text / markdown table / image caption - what gets embedded & shown
    display_label: str    # short label for the Source card, e.g. "Table 2" or "Figure 1"
    extra: dict           # e.g. {"image_path": "..."} for images, {"markdown": "..."} for tables


class VectorStoreBase:
    def add(self, chunks: List[Chunk], embeddings: np.ndarray):
        raise NotImplementedError

    def search(self, query_embedding: np.ndarray, top_k: int) -> List[tuple]:
        raise NotImplementedError

    def save(self):
        raise NotImplementedError

    def load(self) -> bool:
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError


class FaissVectorStore(VectorStoreBase):
    def __init__(self, dim: Optional[int] = None):
        self.dim = dim or config.embedding_dim()
        self.index = faiss.IndexFlatIP(self.dim)  # cosine similarity via normalized vectors
        self.chunks: List[Chunk] = []

    def add(self, chunks: List[Chunk], embeddings: np.ndarray):
        if embeddings.shape[0] == 0:
            return
        self.index.add(embeddings)
        self.chunks.extend(chunks)

    def search(self, query_embedding: np.ndarray, top_k: int) -> List[tuple]:
        if self.index.ntotal == 0:
            return []
        top_k = min(top_k, self.index.ntotal)
        scores, idxs = self.index.search(query_embedding.reshape(1, -1), top_k)
        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            results.append((self.chunks[idx], float(score)))
        return results

    def save(self):
        os.makedirs(config.DATA_DIR, exist_ok=True)
        faiss.write_index(self.index, config.INDEX_PATH)
        with open(config.META_PATH, "wb") as f:
            pickle.dump([asdict(c) for c in self.chunks], f)

    def load(self) -> bool:
        if not (os.path.exists(config.INDEX_PATH) and os.path.exists(config.META_PATH)):
            return False
        self.index = faiss.read_index(config.INDEX_PATH)
        with open(config.META_PATH, "rb") as f:
            raw = pickle.load(f)
        self.chunks = [Chunk(**c) for c in raw]
        return True

    def reset(self):
        self.index = faiss.IndexFlatIP(self.dim)
        self.chunks = []
        for p in (config.INDEX_PATH, config.META_PATH):
            if os.path.exists(p):
                os.remove(p)


# Module-level singleton so the whole app shares one in-memory index
_store: Optional[FaissVectorStore] = None


def get_store() -> FaissVectorStore:
    global _store
    if _store is None:
        _store = FaissVectorStore()
        _store.load()
    return _store
