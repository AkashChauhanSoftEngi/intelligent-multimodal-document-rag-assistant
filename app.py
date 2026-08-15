import os
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv

load_dotenv(override=True)

from rag import config
from rag.pipeline import ingest_file, retrieve, reset_index
from rag.llm import answer_question
from rag.vectorstore import get_store

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25MB upload cap

UPLOAD_DIR = os.path.join(config.DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(config.IMAGES_DIR, exist_ok=True)

ALLOWED_EXT = {".pdf", ".pptx"}


@app.route("/")
def index():
    store = get_store()
    doc_names = sorted({c.doc_name for c in store.chunks})
    sample_loaded = config.SAMPLE_DOC_NAME in doc_names
    return render_template(
        "index.html",
        doc_names=doc_names,
        embedding_backend=config.EMBEDDING_BACKEND,
        table_parser_backend=config.TABLE_PARSER_BACKEND,
        has_gemini_key=bool(config.GOOGLE_API_KEY),
        sample_doc_name=config.SAMPLE_DOC_NAME,
        sample_loaded=sample_loaded,
        sample_questions=config.SAMPLE_QUESTIONS,
    )


@app.route("/api/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400

    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        return jsonify({"error": f"Unsupported file type '{ext}'. Upload a .pdf or .pptx"}), 400

    doc_name = f.filename
    save_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex[:8]}_{f.filename}")
    f.save(save_path)

    try:
        result = ingest_file(save_path, doc_name)
        return jsonify({"ok": True, **result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sample", methods=["POST"])
def load_sample():
    """One-click 'try it now' - ingests the bundled sample revenue report
    (already added to the index, no-op) so visitors don't need a file handy."""
    store = get_store()
    already_loaded = config.SAMPLE_DOC_NAME in {c.doc_name for c in store.chunks}
    if already_loaded:
        chunks = [c for c in store.chunks if c.doc_name == config.SAMPLE_DOC_NAME]
        return jsonify({
            "ok": True, "doc_name": config.SAMPLE_DOC_NAME,
            "text_chunks": sum(1 for c in chunks if c.type == "text"),
            "tables": sum(1 for c in chunks if c.type == "table"),
            "images": sum(1 for c in chunks if c.type == "image"),
            "total_chunks_added": 0,
            "word_count": None,
            "already_loaded": True,
            "sample_questions": config.SAMPLE_QUESTIONS,
        })
    try:
        result = ingest_file(config.SAMPLE_DOC_PATH, config.SAMPLE_DOC_NAME)
        return jsonify({"ok": True, "already_loaded": False, "sample_questions": config.SAMPLE_QUESTIONS, **result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ask", methods=["POST"])
def ask():
    data = request.get_json(force=True, silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Question is required"}), 400

    retrieved = retrieve(question)
    result = answer_question(question, retrieved)
    return jsonify(result)


@app.route("/api/status")
def status():
    store = get_store()
    docs = sorted({c.doc_name for c in store.chunks})
    return jsonify({
        "documents": docs,
        "chunks_indexed": len(store.chunks),
        "embedding_backend": config.EMBEDDING_BACKEND,
        "table_parser_backend": config.TABLE_PARSER_BACKEND,
        "has_gemini_key": bool(config.GOOGLE_API_KEY),
    })


@app.route("/api/reset", methods=["POST"])
def reset():
    reset_index()
    return jsonify({"ok": True})


@app.route("/media/images/<path:filename>")
def media_images(filename):
    return send_from_directory(config.IMAGES_DIR, filename)

@app.route("/sample_data/<path:filename>")
def sample_data(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), "sample_data"), filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
