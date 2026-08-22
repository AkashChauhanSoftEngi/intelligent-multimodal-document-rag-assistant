# 📄 Multimodal Intelligent Document Question Answering System (RAG + Gemini AI)

![Live Demo](https://img.shields.io/badge/LIVE_DEMO-RENDER-46E3B7?style=for-the-badge)

A robust, enterprise-grade Retrieval-Augmented Generation (RAG) based Multimodal Document Assistant. This application processes **PDF and PPTX** files, extracting **text, tables, and images/charts** to enable semantic, context-aware question answering grounded in the uploaded content. Powered by **Google Gemini (LLM & Embeddings)**, **FAISS Vector Database**, and **Flask**.

🔗 **Try it live:** https://intelligent-multimodal-document-rag.onrender.com/

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-BACKEND-black?style=for-the-badge&logo=flask)
![RAG](https://img.shields.io/badge/RAG-Multimodal_Retrieval_Augmented_Generation-orange?style=for-the-badge)
![Gemini](https://img.shields.io/badge/GEMINI-2.5_FLASH-4285F4?style=for-the-badge)
![FAISS](https://img.shields.io/badge/FAISS-VECTOR_DATABASE-purple?style=for-the-badge)

---

# 📚 Table of Contents

- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [System Architecture](#%EF%B8%8F-system-architecture)
- [Project Workflow](#-project-workflow)
- [Technologies Used](#%EF%B8%8F-technologies-used)
- [Project Layout](#-project-layout)
- [Installation & Local Setup](#-installation--local-setup)
- [How to Use](#-how-to-use)
- [Sample Questions](#-sample-questions)
- [Architecture Details & Swappable Backends](#-architecture-details--swappable-backends)
- [Deploying to Render](#-deploying-to-render)
- [Notes & Trade-offs](#-notes--trade-offs)
- [License](#-license)

---

# 📖 Project Overview

While conventional RAG systems excel at retrieving and answering questions from plain-text documents, real-world business documents (like financial reports, pitch decks, and scientific papers) are packed with **structured tables** and **visual charts/images**. Ignoring these visual and structured components leads to incomplete or inaccurate answers.

This project implements an **API-first, locally-swappable Multimodal RAG pipeline** designed to ingest, comprehend, and retrieve information across three distinct document modalities:
1. **Narrative Text:** standard narrative paragraphs embedded semantically.
2. **Structured Tables:** tables extracted with layout-preservation, processed into clean Markdown and summarized.
3. **Visual Elements:** charts, graphs, and images extracted, visually interpreted using Gemini Vision, and indexed via descriptive text captions.

With a beautiful, modern 3-column Flask interface, users can upload complex files, view the active backend status, and ask questions. The application provides grounded answers accompanied by precise page-level citations and an expandable "View Evidence" drawer displaying the exact table or image supporting the answer.

---

# ✨ Key Features

- 📁 **Multimodal Document Support:** Seamlessly upload and process complex PDFs and PPTX slideshows.
- 📐 **Layout-aware Extraction:** Automatic extraction of clean text, structural tables (via `pdfplumber`), and embedded images/charts (via `PyMuPDF` or `python-pptx`).
- 📊 **Intelligent Table Parsing:** Raw tables are converted into clean, readable Markdown and summarized using an LLM to preserve structural relationships.
- 🖼️ **Visual Comprehension (Gemini Vision):** Charts and images are analyzed and transformed into rich textual captions, enabling seamless semantic retrieval.
- ⚙️ **Locally-Swappable Backends:** Switch between high-performance cloud APIs (Gemini) and offline, local equivalents (Sentence-Transformers, heuristic formatters) with simple environment variables.
- ⚡ **Fast Vector Similarity Search:** FAISS index stores and retrieves matching chunks, tables, or visual captions based on semantic similarity.
- 🏷️ **Citations & Evidence Display:** Displays clear page citations for every response, including an interactive viewer to inspect retrieved tables or images directly in the UI.
- 💻 **Responsive Flask Web Interface:** Features an active backend monitor, a visual horizontal pipeline diagram, drag-and-drop uploading, and quick-start sample loading.

---

# 🏗️ System Architecture

```text
                     DOCUMENT (PDF / PPTX Upload)
                                   │
                      ┌────────────┼────────────┐
                      ▼            ▼            ▼
                    TEXT        TABLES       IMAGES
                      │            │            │
                      ▼            ▼            ▼
                 Narrative       Table        Vision
                 Embedding     Parsing &     Captioning
                               Cleaning      (Gemini API)
                      │            │            │
                      └────────────┼────────────┘
                                   ▼
                     Multimodal Retrieval (FAISS)
                                   │
                                   ▼
                           Relevant Evidence
                     (Text / Clean Tables / Image Captions)
                                   │
                                   ▼
                           Gemini LLM Synthesis
                                   │
                                   ▼
                      Answer + Precise Page Citations
```

---

# 🔄 Project Workflow

### Step 1 – Upload Document
Users upload complex multi-page files (PDFs, PPTX presentation decks) or load the pre-bundled Sample Revenue Report with a single click.

### Step 2 – Layout-Aware Parsing
The document parser processes the file page-by-page:
- Extracts narrative paragraph text.
- Extracts structured tables with their cell grids.
- Extracts embedded visual components (charts, graphs, images).

### Step 3 – Multimodal Processing & Captioning
- **Tables:** Extracted cell grids are converted into readable Markdown and paired with a concise descriptive summary.
- **Images:** Visual elements are sent to the Gemini Vision API to generate highly detailed captions explaining the content (e.g., "A bar chart showing segment revenues for 2024 vs 2025").

### Step 4 – Semantic Indexing (FAISS)
Narrative text chunks, cleaned markdown tables, and descriptive image captions are converted into vector embeddings (via Gemini or Sentence-Transformers) and stored inside a local **FAISS vector database**.

### Step 5 – User Question & Retrieval
When a user asks a question, the query is embedded and matched against the FAISS index to retrieve the most semantically relevant chunks (which can be text, a formatted table, or an image caption).

### Step 6 – Context-Aware Synthesis & Citation
The retrieved context is passed to **Gemini 2.5 Flash**, which synthesizes a natural language answer. The response includes structured citation metadata, allowing the UI to highlight exactly which page, table, or chart supported the answer.

---

# 🛠️ Technologies Used

| Category | Technology |
|-----------|------------|
| **Programming Language** | Python 3.11 |
| **Backend Framework** | Flask |
| **Frontend** | HTML, CSS (Vanilla), JavaScript |
| **Embedding Models** | Google Gemini Embedding API (`gemini-embedding-001`) / Local `sentence-transformers` |
| **Vector Database** | FAISS (In-process, locally persisted) |
| **Generative LLM** | Google Gemini 2.5 Flash |
| **Multimodal Vision** | Google Gemini Vision API |
| **Document Parsing** | `pdfplumber` (Tables), `PyMuPDF`/`fitz` (PDF Text & Images), `python-pptx` (PowerPoint slides) |
| **Environment Config** | `python-dotenv` |
| **Deployment** | Render, Gunicorn |

---

# 📂 Project Layout

```text
5-intelligent-multimodal-document-rag-assistant/
│
├── rag/
│   ├── config.py          # Environment settings & backend switchboard
│   ├── parser.py          # Document parsers (extracts text, tables, and images)
│   ├── table_parser.py    # Raw table grid conversion into Markdown and summaries
│   ├── vision.py          # Image captioning using Gemini Vision API
│   ├── embeddings.py      # Embedding generation (Gemini API vs Local Sentence-Transformers)
│   ├── vectorstore.py     # FAISS vector store creation, querying, and storage
│   ├── pipeline.py        # Connects ingestion, vector index, and retrieval together
│   └── llm.py             # Context-aware answer generation and citation crafting
│
├── sample_data/           # Sample business files (PDF, PPTX, and charts)
│   ├── Annual_Revenue_Report_2025.pdf
│   ├── Q4_Revenue_Deck.pptx
│   └── revenue_chart.png
│
├── scripts/               # Helper scripts to generate sample data files
│   ├── make_sample_pdf.py
│   └── make_sample_pptx.py
│
├── static/
│   ├── app.js             # Form handling, chat, drawer slide-outs, and evidence display
│   └── style.css          # Modern 3-column UI styles
│
├── templates/
│   └── index.html         # Main dashboard layout, tech-bar, pipeline diagram
│
├── .env.example           # Shared environment variable templates
├── .gitignore
├── app.py                 # Flask server routes and entry point
├── Procfile               # Production startup command for Render
├── render.yaml            # Render blueprint containing disk mount configs
└── requirements.txt       # Project python dependencies
```

---

# ⚙️ Installation & Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/AkashChauhanSoftEngi/5-intelligent-multimodal-document-rag-assistant.git
cd 5-intelligent-multimodal-document-rag-assistant
```

### 2. Create and Activate a Virtual Environment
```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your Gemini API key:
```bash
cp .env.example .env
```
Open `.env` and configure:
```text
GEMINI_API_KEY=your_google_gemini_api_key_here
EMBEDDING_BACKEND=gemini     # Set to 'local' for offline embedding support
TABLE_PARSER_BACKEND=api     # Set to 'local' for offline heuristic table formatting
```

### 5. Run the Application
```bash
python app.py
```
The application will start running locally at: **`http://127.0.0.1:5000`**

---

# 💡 How to Use

1. **Load a Document:** Drag and drop your own PDF or PPTX into the upload zone, or click **"Load Sample Revenue Report"** for an instant demo using the pre-packaged dataset.
2. **Explore Ingestion Progress:** Watch the real-time layout analysis process the pages, extract tables, and caption images.
3. **Ask Questions:** Enter natural language questions in the text box.
4. **Inspect Answers & Evidence:** 
   - View the generated response grounded strictly in your document.
   - Click on page citations to jump to specific source sections.
   - Expand the **"View Evidence"** drawer to look at the exact table format or raw image that informed the system's answer.

---

# ❓ Sample Questions

Once the sample document is loaded, try asking these multimodal questions:
- *"How much did the company's revenue increase between 2024 and 2025?"* (Requires reading structured table cells)
- *"Which business segment grew the fastest and what was its profit margin?"* (Requires reasoning over tables)
- *"What does the revenue chart show?"* (Requires visual reasoning over the extracted chart image)
- *"Who are the authors of the presentation?"* (Requires extracting text from PPTX slides)

---

# 🔧 Architecture Details & Swappable Backends

This application is built with an **API-first, locally-swappable design**. While Gemini APIs run out of the box, core stages can be dynamically routed to local components to save cost or run fully offline.

| Stage | Default (API Backend) | Local Alternative Backend | Switch Env Variable |
|---|---|---|---|
| **Embeddings** | Gemini `models/gemini-embedding-001` | `sentence-transformers` (`all-MiniLM-L6-v2` running on CPU) | `EMBEDDING_BACKEND=gemini\|local` |
| **Table Parsing** | Gemini API (Cleans extracted grid into Markdown + concise summary) | Layout-preserved heuristic formatting (No API calls) | `TABLE_PARSER_BACKEND=api\|local` |
| **Vector Store** | Local in-process FAISS index (persisted locally under `storage/`) | — (Extensible via `VectorStoreBase`) | Always Local |
| **Vision Stage** | Gemini Vision API (Converts charts/images to captions) | — (GPU memory constraint on basic servers) | Always API |
| **Generation (LLM)** | Gemini 2.5 Flash | — | Always API |

---

# ☁️ Deploying to Render

This repository includes a `render.yaml` blueprint configured for easy automated hosting on **Render**.

### Persistent Storage Setup
Because FAISS databases and uploaded image files are saved locally, a persistent disk is highly recommended so files survive server restarts.
- `render.yaml` automatically mounts a persistent disk at `storage/`.
- *(Note: On Render's free tier, local file storage resets during redeployment; the system is designed to gracefully fall back to storing indices temporarily in memory during those sessions).*

### To Deploy Manually:
1. Push your repository to GitHub.
2. Go to **Render** -> **New** -> **Blueprint**.
3. Link your GitHub repository.
4. Render will automatically detect `render.yaml` and configure your build and start scripts:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120`
5. Add your **`GEMINI_API_KEY`** to the environment variables under the settings dashboard.

---

# ⚠️ Notes & Trade-offs

- **Chunking Method:** Employs character-based sliding window chunking with semantic overlap. This is highly efficient for document and slideshow lengths; for novels or multi-thousand-page dossiers, a hierarchical split is recommended.
- **FAISS Configuration:** Built using an exact-matching `IndexFlatIP` vector index which is exceptionally fast for smaller-to-medium files. Scale up to HNSW or IVF indexes if deploying index sizes exceeding tens of thousands of pages.
- **Offline Fallback / Key Verification:** If a `GEMINI_API_KEY` is not present, the system remains operational for ingestion. It will parse and index files using local backends and return the exact retrieved text chunk or clean table in place of an LLM-synthesized answer.

---

# 🚀 Technical Considerations & Future Improvements

While the current system architecture is modular and optimized for multimodal accuracy, the following areas have been identified for future scalability improvements:

- **Asynchronous Ingestion:** Implement background task queues (e.g., Celery/Redis) to handle document processing, improving user experience by avoiding synchronous blocking during high-latency VLM/parsing tasks.
- **VLM Output Caching:** Introduce a persistent cache layer for VLM-generated descriptions (captions and table summaries) to avoid redundant computation for previously processed assets.
- **Hybrid Table Indexing:** Implement a dual-index approach for tabular data—storing both the LLM-generated summary and the raw Markdown structure—to improve performance for data-heavy, query-specific reasoning.

---

# 📝 License

Distributed under the MIT License. See `LICENSE` for more information (if applicable).
