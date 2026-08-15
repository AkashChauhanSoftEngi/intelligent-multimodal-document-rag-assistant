"""
Stage 2a: TEXT / TABLE-MARKDOWN / IMAGE-CAPTION  ->  EMBEDDING

Same interface, two interchangeable backends, selected by
config.EMBEDDING_BACKEND ("gemini", "api" or "local"). Nothing else in the codebase
needs to know which one is active.
"""
from typing import List
import numpy as np

from . import config

_local_model = None  # lazy-loaded singleton so Render never pays for it unless used


class EmbeddingProvider:
    """Base interface. Returns an (n, dim) float32 numpy array, L2-normalized."""

    def embed(self, texts: List[str]) -> np.ndarray:
        raise NotImplementedError


class GeminiEmbedding(EmbeddingProvider):
    """Gemini text-embedding-004 via API."""

    def __init__(self):
        import google.generativeai as genai
        if not config.GOOGLE_API_KEY:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set."
            )
        genai.configure(api_key=config.GOOGLE_API_KEY)
        self.model_name = config.GEMINI_EMBEDDING_MODEL

    def embed(self, texts: List[str]) -> np.ndarray:
        import google.generativeai as genai
        vecs = []
        for text in texts:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            vecs.append(result["embedding"])
        vecs = np.array(vecs, dtype="float32")
        return _normalize(vecs)


class APIEmbedding(EmbeddingProvider):
    """OpenAI text-embedding-3-small via API. Default backend - no local model
    download, works out of the box on a small Render instance."""

    def __init__(self):
        from openai import OpenAI
        if not config.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Either set it, or run with "
                "EMBEDDING_BACKEND=local to use the offline embedding model instead."
            )
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    def embed(self, texts: List[str]) -> np.ndarray:
        # OpenAI embeddings endpoint accepts batches directly
        resp = self.client.embeddings.create(model=config.OPENAI_EMBEDDING_MODEL, input=texts)
        vecs = np.array([d.embedding for d in resp.data], dtype="float32")
        return _normalize(vecs)


class LocalEmbedding(EmbeddingProvider):
    """sentence-transformers running on CPU. No API key, no network call.
    Model weights (~90MB) are downloaded once and cached on first use."""

    def __init__(self):
        global _local_model
        if _local_model is None:
            from sentence_transformers import SentenceTransformer
            _local_model = SentenceTransformer(config.LOCAL_EMBEDDING_MODEL)
        self.model = _local_model

    def embed(self, texts: List[str]) -> np.ndarray:
        vecs = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return _normalize(vecs.astype("float32"))


def _normalize(vecs: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1e-8
    return vecs / norms


def get_embedding_provider() -> EmbeddingProvider:
    if config.EMBEDDING_BACKEND == "gemini":
        return GeminiEmbedding()
    if config.EMBEDDING_BACKEND == "local":
        return LocalEmbedding()
    return APIEmbedding()
