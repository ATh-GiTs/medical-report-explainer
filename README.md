# 🏥 Medical Report Explainer

An AI-powered application that explains medical reports in simple language with multilingual support — built for Indian patients who receive English medical reports.

**Runs 100% locally — no cloud, no API costs, complete privacy.**

---

## 🌟 Features

- 📄 **PDF Upload** — Upload any medical report (blood tests, prescriptions, discharge summaries)
- 🤖 **AI Extraction** — MedGemma extracts and classifies medical parameters automatically
- 💬 **Q&A in Simple Language** — Ask questions, get patient-friendly answers
- 🌍 **Multilingual** — Supports Hindi, Marathi, Tamil, Bengali, Telugu, Gujarati
- 🔊 **Voice Output** — Listen to answers in your language
- 🔒 **100% Private** — Everything runs on your machine via Ollama

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| LLM | MedGemma 4B via Ollama |
| Embeddings | nomic-embed-text via Ollama |
| Vector DB | ChromaDB |
| Backend | FastAPI + Pydantic v2 |
| Frontend | Streamlit |
| Translation | deep-translator |
| Voice | gTTS |
| Logging | Loguru |

---

## 🚀 Setup Instructions

### 1. Prerequisites
- Python 3.11
- [Ollama](https://ollama.com/download) installed

### 2. Pull Ollama Models
```powershell
ollama pull alibayram/medgemma
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### 3. Clone & Setup
```powershell
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment
```powershell
# Copy example env file
copy .env.example .env
```

### 5. Run the Application

**Terminal 1 — Start FastAPI backend:**
```powershell
uvicorn main:app --reload
```

**Terminal 2 — Start Streamlit frontend:**
```powershell
streamlit run frontend/main.py
```

### 6. Open in Browser
- **App:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs

---

## 📁 Project Structure

```
medical-report-explainer/
├── app/
│   ├── agents/          # AI agents (extraction, query)
│   ├── api/             # FastAPI routes
│   ├── core/            # Config & logging
│   ├── models/          # Pydantic schemas
│   ├── services/        # Ollama, ChromaDB, Translation
│   └── utils/           # PDF parsing helpers
├── frontend/            # Streamlit UI
├── data/                # Local storage (gitignored)
├── tests/               # Unit tests
├── main.py              # FastAPI entry point
└── requirements.txt
```

---

## 🧪 Running Tests
```powershell
pytest tests/ -v
```

---

## 🔒 Privacy

All processing happens locally on your machine:
- No data sent to any external server
- No API keys required
- Patient data stays on your device
- Safe for sensitive medical documents

---

*Built as an internship project to solve the medical literacy gap for non-English speaking patients in India.*
