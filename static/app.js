const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const uploadStatus = document.getElementById("uploadStatus");
const sampleBtn = document.getElementById("sampleBtn");
const docInfoPanel = document.getElementById("docInfoPanel");
const docInfoList = document.getElementById("docInfoList");
const docInfoStats = document.getElementById("docInfoStats");
const askForm = document.getElementById("askForm");
const questionInput = document.getElementById("questionInput");
const askBtn = document.getElementById("askBtn");
const chatStream = document.getElementById("chatStream");
const emptyState = document.getElementById("emptyState");
const resetBtn = document.getElementById("resetBtn");
const rightPanel = document.getElementById("rightPanel");
const sampleQuestionList = document.getElementById("sampleQuestionList");

const cardTemplate = document.getElementById("cardTemplate");
const sourceTemplate = document.getElementById("sourceTemplate");

// ---------- Upload (drag & drop / click) ----------
dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("drag"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("drag");
  if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => {
  if (fileInput.files.length) uploadFile(fileInput.files[0]);
});

async function uploadFile(file) {
  uploadStatus.textContent = `Processing "${file.name}" — parsing text, tables & images…`;
  uploadStatus.className = "upload-status busy";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/upload", { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Upload failed");

    uploadStatus.textContent = `✓ Indexed: ${data.text_chunks} text block(s), ${data.tables} table(s), ${data.images} image(s)`;
    uploadStatus.className = "upload-status ok";
    addDocToInfoPanel(data);
  } catch (err) {
    uploadStatus.textContent = `✗ ${err.message}`;
    uploadStatus.className = "upload-status err";
  }
}

// ---------- Sample document ----------
sampleBtn.addEventListener("click", async () => {
  if (sampleBtn.classList.contains("loaded")) return;
  sampleBtn.textContent = "Loading sample…";

  try {
    const res = await fetch("/api/sample", { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Failed to load sample");

    sampleBtn.textContent = "✓ Sample Revenue Report Loaded";
    sampleBtn.classList.add("loaded");
    addDocToInfoPanel(data);
    showSampleQuestions(data.sample_questions || []);
  } catch (err) {
    sampleBtn.textContent = "Load Sample Revenue Report";
    uploadStatus.textContent = `✗ ${err.message}`;
    uploadStatus.className = "upload-status err";
  }
});

function showSampleQuestions(questions) {
  if (!questions.length) return;
  sampleQuestionList.innerHTML = "";
  questions.forEach((q) => {
    const card = document.createElement("div");
    card.className = "question-card";
    card.textContent = q;
    card.addEventListener("click", () => fillQuestion(card));
    sampleQuestionList.appendChild(card);
  });
  rightPanel.removeAttribute("hidden");
}

function fillQuestion(card) {
  questionInput.value = card.textContent.trim();
  questionInput.focus();
}
window.fillQuestion = fillQuestion; // used by inline onclick in server-rendered cards

// ---------- Document info panel ----------
function addDocToInfoPanel(data) {
  docInfoPanel.removeAttribute("hidden");
  const existing = Array.from(docInfoList.children).some((li) => li.textContent.includes(data.doc_name));
  if (!existing) {
    const li = document.createElement("li");
    li.textContent = `📄 ${data.doc_name}`;
    docInfoList.appendChild(li);
  }
  const parts = [];
  if (data.word_count) parts.push(`${data.word_count} words`);
  parts.push(`${data.text_chunks} text · ${data.tables} table(s) · ${data.images} image(s)`);
  if (data.embedding_backend) parts.push(`Embedding: ${data.embedding_backend}`);
  if (data.table_parser_backend) parts.push(`Table parsing: ${data.table_parser_backend}`);
  docInfoStats.textContent = parts.join("\n");
}

// ---------- Reset ----------
resetBtn.addEventListener("click", async () => {
  if (!confirm("Clear the entire index? This removes all uploaded documents.")) return;
  await fetch("/api/reset", { method: "POST" });
  docInfoList.innerHTML = "";
  docInfoStats.textContent = "";
  docInfoPanel.setAttribute("hidden", "");
  chatStream.innerHTML = "";
  chatStream.appendChild(emptyState);
  uploadStatus.textContent = "";
  sampleBtn.textContent = "Load Sample Revenue Report";
  sampleBtn.classList.remove("loaded");
  rightPanel.setAttribute("hidden", "");
});

// ---------- Ask ----------
askForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  emptyState.remove();
  askBtn.disabled = true;

  const loadingCard = document.createElement("div");
  loadingCard.className = "qa-card loading-card";
  
  const spinner = document.createElement("div");
  spinner.className = "spinner";
  loadingCard.appendChild(spinner);
  
  const textNode = document.createTextNode(`Searching documents for: "${question}"…`);
  loadingCard.appendChild(textNode);
  
  chatStream.prepend(loadingCard);
  loadingCard.scrollIntoView({ behavior: "smooth", block: "start" });

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    loadingCard.remove();
    if (!res.ok) throw new Error(data.error || "Something went wrong");
    renderCard(question, data);
  } catch (err) {
    loadingCard.remove();
    renderCard(question, { answer: `Error: ${err.message}`, citations: [] });
  } finally {
    askBtn.disabled = false;
    questionInput.value = "";
    questionInput.focus();
  }
});

function renderCard(question, result) {
  const node = cardTemplate.content.cloneNode(true);
  node.querySelector(".qa-question-text").textContent = question;
  node.querySelector(".qa-answer-text").textContent = result.answer || "(no answer)";

  const sourceList = node.querySelector(".qa-source-list");
  const citations = result.citations || [];

  if (citations.length === 0) {
    const none = document.createElement("div");
    none.className = "source-line";
    none.textContent = "No supporting source found.";
    sourceList.appendChild(none);
  }

  citations.forEach((cite) => {
    const srcNode = sourceTemplate.content.cloneNode(true);
    srcNode.querySelector(".source-doc").textContent = cite.doc_name;
    srcNode.querySelector(".source-page").textContent = `Page ${cite.page}`;
    srcNode.querySelector(".source-label").textContent = cite.display_label;

    const evidenceBody = srcNode.querySelector(".evidence-body");
    const btn = srcNode.querySelector(".evidence-btn");
    btn.addEventListener("click", () => {
      const isHidden = evidenceBody.hasAttribute("hidden");
      if (isHidden) {
        evidenceBody.innerHTML = renderEvidence(cite);
        evidenceBody.removeAttribute("hidden");
        btn.textContent = "Hide Evidence";
      } else {
        evidenceBody.setAttribute("hidden", "");
        btn.textContent = "View Evidence";
      }
    });

    sourceList.appendChild(srcNode);
  });

  chatStream.prepend(node);
  node.querySelector?.(".qa-card")?.scrollIntoView?.({ behavior: "smooth", block: "start" });
}

function renderEvidence(cite) {
  if (cite.type === "image" && cite.extra && cite.extra.image_path) {
    return `<div>${escapeHtml(cite.content)}</div><img src="/media/${cite.extra.image_path}" alt="evidence image">`;
  }
  if (cite.type === "table" && cite.extra && cite.extra.markdown) {
    return `<div>${escapeHtml(cite.content)}</div><pre style="white-space:pre-wrap;font-family:inherit;margin-top:8px;">${escapeHtml(cite.extra.markdown)}</pre>`;
  }
  return `<div>${escapeHtml(cite.content || "")}</div>`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
