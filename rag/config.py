"""
Central configuration for the RAG pipeline.

Architecture note
------------------
Three of the four pipeline stages are behind a small interface so the
backend can be swapped with a single environment variable, no code changes:

    EMBEDDING_BACKEND     = "api"   -> OpenAI text-embedding-3-small (default)
                             "local" -> sentence-transformers, runs on CPU, no key needed

    TABLE_PARSER_BACKEND  = "api"   -> pdfplumber extracts cell grid locally, then an
                                        LLM call (Claude) cleans/normalizes it to
                                        Markdown + a one-line summary (default)
                             "local" -> pure heuristic formatting, no LLM call

    VECTOR_STORE_BACKEND  = "faiss" -> local FAISS index (default, always local -
                                        FAISS has no hosted API, so "local" is the
                                        only real option; the interface exists so a
                                        hosted vector DB could be dropped in later)

The vision stage (image -> caption) is intentionally NOT swappable. Running a
local vision model needs GPU-class memory that a Render web instance doesn't
have, so image understanding always goes through the Claude Vision API.
"""
import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Model names
ANTHROPIC_TEXT_MODEL = os.environ.get("ANTHROPIC_TEXT_MODEL", "claude-sonnet-4-5")
ANTHROPIC_VISION_MODEL = os.environ.get("ANTHROPIC_VISION_MODEL", "claude-sonnet-4-5")
OPENAI_EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
GEMINI_TEXT_MODEL = os.environ.get("GEMINI_TEXT_MODEL", "models/gemini-3.7-flash")
GEMINI_VISION_MODEL = os.environ.get("GEMINI_VISION_MODEL", "models/gemini-3.7-flash")
GEMINI_EMBEDDING_MODEL = os.environ.get("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
LOCAL_EMBEDDING_MODEL = os.environ.get("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Backend toggles - this is the "flexible architecture" switchboard
EMBEDDING_BACKEND = os.environ.get("EMBEDDING_BACKEND", "gemini")       # gemini | openai | local
TABLE_PARSER_BACKEND = os.environ.get("TABLE_PARSER_BACKEND", "api")  # api | local
VECTOR_STORE_BACKEND = os.environ.get("VECTOR_STORE_BACKEND", "faiss")  # faiss only, for now

# Retrieval
TOP_K = int(os.environ.get("TOP_K", "5"))
CHUNK_SIZE_CHARS = int(os.environ.get("CHUNK_SIZE_CHARS", "1200"))
CHUNK_OVERLAP_CHARS = int(os.environ.get("CHUNK_OVERLAP_CHARS", "150"))

# Bundled sample document (see sample_data/) for one-click "try it now" demos
SAMPLE_DOC_PATH = os.path.join(os.path.dirname(__file__), "..", "sample_data", "Annual_Revenue_Report_2025.pdf")
SAMPLE_DOC_NAME = "Annual_Revenue_Report_2025.pdf"
SAMPLE_QUESTIONS = [
    "Summarize the document.",
    "How much did revenue increase between 2024 and 2025?",
    "Which segment grew the fastest year-over-year?",
    "Which segment declined in FY2025?",
    "What was the gross margin in FY2025 compared to FY2024?",
    "What does the revenue chart on page 3 show?",
    "What was the CAGR from FY2021 to FY2025?",
    "Which region grew the fastest and why?",
]

# Storage
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "storage"))
INDEX_PATH = os.path.join(DATA_DIR, "index.faiss")
META_PATH = os.path.join(DATA_DIR, "meta.pkl")
IMAGES_DIR = os.path.join(DATA_DIR, "images")

# Embedding dimensions per backend (needed to size the FAISS index)
EMBEDDING_DIMS = {
    "api": 1536,     # text-embedding-3-small
    "gemini": 3072,  # models/gemini-embedding-001
    "local": 384,    # all-MiniLM-L6-v2
}


def embedding_dim() -> int:
    return EMBEDDING_DIMS.get(EMBEDDING_BACKEND, 1536)
