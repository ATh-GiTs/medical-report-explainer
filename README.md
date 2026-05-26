# Pulse AI: The Medical Explainer 🩺
**A Privacy-Preserving Hybrid RAG Framework for Enterprise Medical Analysis**

Pulse AI bridges the gap between complex clinical data and patient understanding. It acts as an enterprise-grade medical document explainer, utilizing a hybrid privacy architecture to securely process, index, and interpret 20-page lab reports and handwritten prescriptions.

## 🚀 Enterprise-Grade Features
* **Privacy-First Hybrid Architecture:** Sensitive medical documents are embedded and indexed strictly on local hardware (ChromaDB, 384-dim vectors). Only anonymized, context-specific chunks are sent to the cloud reasoning engine.
* **Large-Scale "Blind Test" RAG:** Implements a 3500-character header truncation algorithm, allowing seamless ingestion of massive 20+ page clinical reports without triggering token rate limits.
* **Vision & Selective Translation:** Integrates Llama 4 Scout for native multimodal OCR of cursive handwriting. Uses strict selective translation protocols to translate patient instructions into local languages (e.g., Hindi) while enforcing English for medication names to ensure clinical safety.
* **Deterministic Factual Grounding:** LLM temperature is mechanically restricted to `0.1` across the service layer. The reasoning agent is constrained by strict context-locked prompts to prevent unprompted lifestyle or medical advice (Zero-Hallucination protocol).

## 🧠 System Architecture
1. **Frontend:** Streamlit 
2. **Backend Gateway:** FastAPI
3. **Local Vector Store:** ChromaDB + SentenceTransformers (`all-MiniLM-L6-v2`)
4. **Cloud Reasoning Engine:** Groq LPU (Llama 3.3 70B & Llama 4 Scout)

## ⚙️ Core Agents
* `extraction_agent.py`: Handles dynamic document chunking, metadata classification (Blood Test, Lab Report, Radiology), and semantic retrieval.
* `prescription_agent.py`: Manages the Vision OCR pipeline and multilingual clinical safety formatting.
* `query_agent.py`: Executes the RAG reasoning loop to provide patient-friendly explanations grounded *only* in the provided text.
