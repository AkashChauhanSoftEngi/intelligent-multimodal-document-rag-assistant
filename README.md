# Intelligent Document QA System — Multimodal RAG

Upload a PDF or PPTX (e.g. an annual/revenue report) and ask questions in
plain English. Answers are grounded in the document's **text, tables, and
images**, and every answer cites the page and source that supports it.

```
   DOCUMENT
      │
 ┌────┼────┐
 ↓    ↓    ↓
TEXT TABLES IMAGES
 │    │      │
 ↓    ↓      ↓
Embed Table  Vision      <- Table parsing (API/local) + Vision (API only)
      Parse  Caption
 └────┼──────┘
      ↓
Multimodal Retrieval (FAISS)
      ↓
Relevant Evidence
      ↓
Gemini (LLM)
      ↓
Answer + Page Citation
```

## Architecture: API-first, locally-swappable

The app runs entirely on hosted APIs out of the box (the priority for this
build was **"make it work on Render"**), but every stage except vision is
built behind a small interface so it can be swapped for a local/offline
implementation with a single environment variable — no code changes.

| Stage | Default (API) | Local alternative | Switch |
|---|---|---|---|
| Embeddings | Gemini `models/gemini-embedding-001` | `sentence-transformers` (all-MiniLM-L6-v2, CPU, no key) | `EMBEDDING_BACKEND=gemini\|local` |
| Table parsing | pdfplumber extracts the grid locally, then Gemini cleans it into Markdown + a summary | pure heuristic formatting, no LLM call | `TABLE_PARSER_BACKEND=api\|local` |
| Vector store | FAISS (in-process, always local — FAISS has no hosted API) | — | wrapped behind `VectorStoreBase` for a future hosted DB |
| **Vision (image → caption)** | **Gemini Vision API — always.** A local vision model needs GPU memory a Render web dyno doesn't have, so this is the one deliberate non-swappable stage. | — | — |
| Answer generation | Gemini (Google AI API) | — | — |

See `rag/config.py` for the full switchboard and `rag/embeddings.py` /
`rag/table_parser.py` for the two-backend implementations.

## Project layout

```
app.py                  Flask app: routes for upload / ask / status / reset
rag/
  config.py              env-driven settings + backend switchboard
  parser.py               DOCUMENT -> raw text / tables / images (pdfplumber, PyMuPDF, python-pptx)
  table_parser.py          raw table grid -> clean Markdown + summary (api|local)
  vision.py                 image -> caption (Gemini Vision, API only)
  embeddings.py           text -> vector (gemini|local)
  vectorstore.py          FAISS index + metadata, persisted to disk
  pipeline.py             wires ingestion + retrieval together
  llm.py                  evidence -> answer + citations (Gemini)
templates/index.html    UI: header (tech-bar + pipeline diagram) + 3-column layout
                         (upload/quick-start, ask+answer cards, sample questions)
static/style.css, app.js
sample_data/             demo revenue report (PDF + PPTX + chart image)
scripts/                 scripts that generated the sample files
render.yaml, Procfile   deployment
```

## UI

Header shows a tech-bar (which embedding/table-parser/LLM backend is active,
read live from env vars) and a horizontal pipeline diagram
(📄→✂️→🧠→🗄️→🤖→💬). Below it, a 3-column layout: **Quick Start** (one-click
"Load Sample Revenue Report" button, drag-and-drop upload, document info)
on the left, **Ask Questions** (Question/Answer/Source cards with an
expandable "View Evidence" panel showing the actual table or image) in the
center, and clickable **Sample Questions** on the right once the sample doc
is loaded.

## Local setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in GEMINI_API_KEY (and GOOGLE_API_KEY if needed)
python app.py           # http://localhost:5000
```

Try it with the bundled sample files in `sample_data/` — a revenue report
with narrative text, a segment-revenue table, and a bar chart — then ask:

> "How much did the company's revenue increase between 2024 and 2025?"
> "Which segment grew the fastest?"
> "What does the revenue chart show?"

## Deploying to Render

1. Push this repo to GitHub.
2. In Render: **New → Blueprint**, point it at the repo (`render.yaml` is
   already configured), or **New → Web Service** manually with:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120`
3. Set environment variables in the Render dashboard:
   - `GEMINI_API_KEY` (required — powers answers + image captions)
4. `render.yaml` mounts a small persistent disk at `storage/` so the FAISS
   index and uploaded-image files survive restarts. On the free plan
   (no disk), the index just lives in memory and resets on redeploy — fine
   for a demo.

To run fully offline/local (no API key, slower cold start on Render's
free CPU): set `EMBEDDING_BACKEND=local` and `TABLE_PARSER_BACKEND=local`.
`GEMINI_API_KEY` is still required for image captions and answers.

## Notes / trade-offs

- Chunking is simple character-based splitting with overlap — good enough
  for report-sized PDFs/decks; swap in a smarter splitter for very long docs.
- The FAISS index is a single flat (exact) index — fine at demo scale;
  swap `IndexFlatIP` for an IVF/HNSW index if you index thousands of pages.
- Without `GEMINI_API_KEY` set, the app still parses, indexes, and
  retrieves correctly — it just returns the top retrieved chunk instead of
  a generated answer, so you can sanity-check retrieval without a key.
