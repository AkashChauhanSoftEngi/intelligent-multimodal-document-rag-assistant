"""
Wires the full diagram together:

DOCUMENT -> TEXT/TABLES/IMAGES -> Embedding/Table Parsing/Vision -> Multimodal
Retrieval -> Relevant Evidence -> LLM -> Answer + Citation
"""
import os
from typing import List

from . import config
from .parser import parse_document
from .table_parser import parse_table
from .vision import caption_image
from .embeddings import get_embedding_provider
from .vectorstore import Chunk, get_store, FaissVectorStore


def _chunk_text(text: str, size: int = None, overlap: int = None) -> List[str]:
    size = size or config.CHUNK_SIZE_CHARS
    overlap = overlap or config.CHUNK_OVERLAP_CHARS
    if len(text) <= size:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


def ingest_file(file_path: str, doc_name: str) -> dict:
    """Parses a file and adds all its chunks (text/table/image) to the vector store."""
    parsed = parse_document(file_path, doc_name, images_dir=config.IMAGES_DIR)
    embedder = get_embedding_provider()
    store = get_store()

    next_id = max([c.chunk_id for c in store.chunks], default=-1) + 1
    new_chunks: List[Chunk] = []
    contents_to_embed: List[str] = []

    # --- TEXT ---
    for t in parsed.texts:
        for piece in _chunk_text(t.text):
            new_chunks.append(Chunk(
                chunk_id=next_id, doc_name=t.doc_name, page=t.page, type="text",
                content=piece, display_label=f"Page {t.page}", extra={},
            ))
            contents_to_embed.append(piece)
            next_id += 1

    # --- TABLES ---
    for tbl in parsed.tables:
        result = parse_table(tbl.rows)
        embed_text = f"{result['summary']}\n{result['markdown']}"
        label = f"Table {tbl.table_index + 1} (page {tbl.page})"
        new_chunks.append(Chunk(
            chunk_id=next_id, doc_name=tbl.doc_name, page=tbl.page, type="table",
            content=result["summary"], display_label=label,
            extra={"markdown": result["markdown"]},
        ))
        contents_to_embed.append(embed_text)
        next_id += 1

    # --- IMAGES ---
    for img in parsed.images:
        caption = caption_image(img.path)
        label = f"Figure {img.image_index + 1} (page {img.page})"
        rel_path = os.path.relpath(img.path, config.DATA_DIR)
        new_chunks.append(Chunk(
            chunk_id=next_id, doc_name=img.doc_name, page=img.page, type="image",
            content=caption, display_label=label,
            extra={"image_path": rel_path.replace(os.sep, "/")},
        ))
        contents_to_embed.append(caption)
        next_id += 1

    if contents_to_embed:
        embeddings = embedder.embed(contents_to_embed)
        store.add(new_chunks, embeddings)
        store.save()

    word_count = sum(len(t.text.split()) for t in parsed.texts)

    return {
        "doc_name": doc_name,
        "text_chunks": len(parsed.texts),
        "tables": len(parsed.tables),
        "images": len(parsed.images),
        "total_chunks_added": len(new_chunks),
        "word_count": word_count,
        "embedding_backend": config.EMBEDDING_BACKEND,
        "table_parser_backend": config.TABLE_PARSER_BACKEND,
    }


def retrieve(question: str, top_k: int = None):
    top_k = top_k or config.TOP_K
    embedder = get_embedding_provider()
    store = get_store()
    q_emb = embedder.embed([question])[0]
    return store.search(q_emb, top_k)


def reset_index():
    store = get_store()
    store.reset()
