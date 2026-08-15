"""
Stage 5-6: RELEVANT EVIDENCE -> VLM / MULTIMODAL LLM -> ANSWER + PAGE CITATION

Takes the retrieved chunks (text / table markdown / image captions) and asks
Gemini to answer using only that evidence, returning strict JSON so the UI
can render the Question / Answer / Source card shown in the mockup.
"""
import json
import re
from typing import List
import google.generativeai as genai
from . import config
from .vectorstore import Chunk


SYSTEM_PROMPT = """You are a document QA assistant. Answer ONLY using the EVIDENCE
provided. Every evidence item is labeled with a document name, page/slide number,
type (text/table/image), and a display label.

Rules:
- If the evidence doesn't contain the answer, say so plainly - never guess or use outside knowledge.
- Be concise and quantitative: prefer exact figures, percentages, and deltas over vague language.
- Pick the 1-3 evidence items that actually support your answer as citations.
- Respond with ONLY a JSON object, no markdown fences, no commentary:

{
  "answer": "<concise answer, 1-3 sentences>",
  "citations": [
    {"doc_name": "...", "page": <int>, "type": "text|table|image", "display_label": "...", "chunk_id": <int>}
  ]
}
"""


def _format_evidence(chunks: List[Chunk]) -> str:
    blocks = []
    for c in chunks:
        blocks.append(
            f"[chunk_id={c.chunk_id} | doc=\"{c.doc_name}\" | page={c.page} | "
            f"type={c.type} | label=\"{c.display_label}\"]\n{c.content}"
        )
    return "\n\n---\n\n".join(blocks)


def answer_question(question: str, retrieved: List[tuple]) -> dict:
    """retrieved: list of (Chunk, score) tuples from vectorstore.search"""
    if not retrieved:
        return {
            "answer": "I couldn't find anything relevant in the uploaded documents to answer that.",
            "citations": [],
        }

    chunks = [c for c, _ in retrieved]
    evidence_text = _format_evidence(chunks)

    if not config.GOOGLE_API_KEY:
        # Graceful degradation so the app still demonstrates retrieval without a key
        best = chunks[0]
        return {
            "answer": "(No GOOGLE_API_KEY set - showing top retrieved evidence instead of a generated answer.)",
            "citations": [{
                "doc_name": best.doc_name, "page": best.page, "type": best.type,
                "display_label": best.display_label, "chunk_id": best.chunk_id,
                "content": best.content, "extra": best.extra,
            }],
        }

    genai.configure(api_key=config.GOOGLE_API_KEY)
    model = genai.GenerativeModel(config.GEMINI_TEXT_MODEL, system_instruction=SYSTEM_PROMPT)
    
    resp = model.generate_content(f"QUESTION: {question}\n\nEVIDENCE:\n{evidence_text}")
    
    raw = resp.text.strip()
    raw = re.sub(r"^```json|```$", "", raw.strip(), flags=re.MULTILINE).strip()

    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {"answer": raw, "citations": []}

    # Attach full chunk objects to citations so the UI can render evidence previews
    by_id = {c.chunk_id: c for c in chunks}
    enriched = []
    for cite in parsed.get("citations", []):
        chunk = by_id.get(cite.get("chunk_id"))
        if chunk:
            enriched.append({
                "doc_name": chunk.doc_name,
                "page": chunk.page,
                "type": chunk.type,
                "display_label": chunk.display_label,
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "extra": chunk.extra,
            })
    parsed["citations"] = enriched
    return parsed
