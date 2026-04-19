import streamlit as st
import requests
import os
import time

# ─── Page Config ──────────────────────────────────────────
st.set_page_config(
    page_title="Medical Report Explainer",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── Organic Warm Beige UI/UX CSS Injection ────────────────
def inject_custom_css():
    st.markdown("""
    <style>
        /* Restored the native Streamlit Header/Menu by removing the hidden visibility rules */
        footer {visibility: hidden;}

        /* APP BACKGROUND & TYPOGRAPHY */
        .stApp {
            background-color: #FDFBF9; 
            font-family: 'Inter', -apple-system, sans-serif;
            color: #4A3F35; 
        }

        h1, h2, h3, h4 {
            color: #2D241E; 
            font-weight: 800;
            letter-spacing: -0.02em;
        }

        /* =========================================
           TOP NAVIGATION SHAPES & BORDERS
           ========================================= */
        div[data-testid="stSelectbox"] > div[data-baseweb="select"] {
            border-radius: 25px !important;
            border: 1.5px solid #C4B5A5 !important;
            background-color: #FFFFFF !important;
            padding: 2px 10px !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
            transition: all 0.2s ease;
        }
        div[data-testid="stSelectbox"] > div[data-baseweb="select"]:hover {
            border-color: #A67C65 !important;
        }

        div[data-testid="stPopover"] > button {
            border-radius: 25px !important;
            border: 1.5px solid #C4B5A5 !important;
            background-color: #FFFFFF !important;
            color: #4A3F35 !important;
            padding: 5px 20px !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stPopover"] > button:hover {
            border-color: #A67C65 !important;
            background-color: #FCFAFA !important;
            transform: translateY(-1px);
        }

        /* MODERN TABS */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            background-color: #F2EBE5; 
            padding: 12px 12px 0px 12px;
            border-radius: 16px;
            box-shadow: inset 0 -2px 0 0 #E0D5CC;
            margin-bottom: 30px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            border-radius: 10px 10px 0px 0px;
            padding: 10px 24px;
            color: #8C7A6B; 
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important;
            border-bottom: 3px solid #1A1A1A !important; 
            color: #1A1A1A !important;
            font-weight: 800;
        }

        /* SLIDESPILOT-STYLE FILE UPLOADER HACK */
        [data-testid="stFileUploadDropzone"] {
            border: 2px dashed #D6C8B8 !important; 
            border-radius: 16px !important;
            background-color: #FFFFFF !important; 
            padding: 60px 20px !important; 
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02);
            transition: all 0.3s ease;
        }
        [data-testid="stFileUploadDropzone"]:hover {
            border-color: #1A1A1A !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        }
        
        [data-testid="stFileUploadDropzone"] svg { display: none !important; }
        
        [data-testid="stFileUploadDropzone"] > div > div::before {
            content: "Drag & drop your file here or";
            display: block;
            font-size: 1.15rem;
            color: #4A3F35;
            font-weight: 500;
            margin-bottom: 15px;
            text-align: center;
        }
        
        [data-testid="stFileUploadDropzone"] .css-1b1hlgl { display: none !important; }
        [data-testid="stFileUploadDropzone"] .css-1v0mbdj { display: none !important; }

        [data-testid="stFileUploadDropzone"] button {
            background-color: #1A1A1A !important; 
            color: #FFFFFF !important;
            border-radius: 8px !important;
            padding: 10px 30px !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            border: none !important;
            margin: 0 auto !important;
            display: block !important;
        }
        [data-testid="stFileUploadDropzone"] button:hover {
            background-color: #333333 !important;
        }
        [data-testid="stFileUploadDropzone"] small { display: none !important; }

        /* RESULT CARDS */
        [data-testid="stMetric"], .stExpander {
            background-color: #FFFFFF;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
            border: 1px solid #E0D5CC; 
        }
        
        /* SIDEBAR STYLING */
        [data-testid="stSidebar"] {
            background-color: #F2EBE5; 
            border-right: 1px solid #E0D5CC;
        }
        
        .check-text {
            text-align: center; 
            color: #8C7A6B; 
            font-size: 0.85rem; 
            margin-top: 15px;
            font-weight: 500;
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ─── API Base URL & Config ────────────────────────────────
API_URL = "http://localhost:8000/api/v1"

LANGUAGES = {
    "English": "en", "Hindi (हिंदी)": "hi", "Marathi (मराठी)": "mr",
    "Tamil (தமிழ்)": "ta", "Bengali (বাংলা)": "bn", "Telugu (తెలుగు)": "te",
    "Gujarati (ગુજરાતી)": "gu",
}

# ─── State Initialization ─────────────────────────────────
if "api_status" not in st.session_state:
    st.session_state["api_status"] = None
if "last_health_check" not in st.session_state:
    st.session_state["last_health_check"] = 0
if "is_processing" not in st.session_state:
    st.session_state["is_processing"] = False
if "prefill_question" not in st.session_state:
    st.session_state["prefill_question"] = ""
if "report_data" not in st.session_state:
    st.session_state["report_data"] = {}

# ─── Helper Functions ─────────────────────────────────────
def check_api_health(force=False):
    now = time.time()
    if force or (now - st.session_state["last_health_check"]) > 10:
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            st.session_state["api_status"] = response.json() if response.status_code == 200 else None
        except Exception:
            if not st.session_state["is_processing"]:
                st.session_state["api_status"] = None
        st.session_state["last_health_check"] = now
    return st.session_state["api_status"]

def upload_report(file_bytes, filename):
    try:
        st.session_state["is_processing"] = True
        response = requests.post(f"{API_URL}/report/upload", files={"file": (filename, file_bytes, "application/pdf")}, timeout=300)
        st.session_state["is_processing"] = False
        return response.json(), response.status_code
    except Exception as e:
        st.session_state["is_processing"] = False
        return {"detail": f"Error: {str(e)}"}, 500

def ask_question(report_id, question, language, include_voice):
    try:
        st.session_state["is_processing"] = True
        response = requests.post(f"{API_URL}/report/query", json={"report_id": report_id, "question": question, "target_language": language, "include_voice": include_voice}, timeout=300)
        st.session_state["is_processing"] = False
        return response.json(), response.status_code
    except Exception as e:
        st.session_state["is_processing"] = False
        return {"detail": f"Error: {str(e)}"}, 500

# ─── TOP NAVIGATION BAR ───────────────────────────────────
spacer, nav_lang, nav_voice, nav_help = st.columns([6.5, 1.5, 1.2, 1.5])

with nav_lang:
    selected_language_name = st.selectbox("Language", options=list(LANGUAGES.keys()), index=0, label_visibility="collapsed")
    selected_language_code = LANGUAGES[selected_language_name]

with nav_voice:
    st.write("") 
    include_voice = st.toggle("🔊 Voice", value=False)

with nav_help:
    with st.popover("⚙️ How It Works", use_container_width=True):
        st.markdown("**1. Ingest:** Drag & drop a PDF or Image.")
        st.markdown("**2. Extract:** Hybrid pipeline parses digital text or uses OCR for handwriting.")
        st.markdown("**3. Structure:** Local LLM structures the messy medical data safely.")
        st.markdown("**4. Chat:** Semantic search retrieves exact answers from your report.")

# ─── Sidebar Dashboard ────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/heart-with-pulse.png", width=60)
    st.markdown("<h2 style='margin-top: -10px; margin-bottom: 5px;'>System Health</h2>", unsafe_allow_html=True)
    st.divider()

    if st.session_state["is_processing"]:
        st.info("⏳ Processing data...", icon="🔄")
    else:
        health = check_api_health()
        if health:
            st.success("API Online", icon="🟢")
            if health.get("ollama_connected", False):
                st.success("Ollama Engine Online", icon="🧠")
            else:
                st.warning("Ollama Offline", icon="⚠️")
        else:
            st.error("API Offline - Start Uvicorn", icon="🔴")

    if st.button("🔄 Refresh Connection", use_container_width=True):
        check_api_health(force=True)
        st.rerun()

    st.divider()
    st.markdown("### 🛠️ Tech Stack")
    st.markdown("`Streamlit` `FastAPI` `MedGemma 1.5` `Ollama` `Tesseract OCR` `ChromaDB`")

# ─── Main Content Area (Hero Section) ──────────────────────
st.markdown("<h1 style='text-align: center; font-size: 3.5rem; margin-top: -20px; margin-bottom: 0px;'>Summarize Medical Reports with AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.25rem; margin-top: 10px; margin-bottom: 40px;'>Instant AI summaries and clinical insights for lab reports and prescriptions.</p>", unsafe_allow_html=True)

# ─── COMBINED TABS ────────────────────────────────────────
tab1, tab2 = st.tabs(["📄 AI Summarizer & Chat", "💊 AI Prescription Reader"])

# ════════════════════════════════════════════════════════
# TAB 1: Upload Report & Chat (Merged Workflow)
# ════════════════════════════════════════════════════════
with tab1:
    st.write("")
    col_l, col_m, col_r = st.columns([1, 2, 1]) 
    
    with col_m:
        uploaded_file = st.file_uploader("Upload Document", type=["pdf"], label_visibility="collapsed")
        
        if not uploaded_file:
            st.markdown("<p class='check-text'>✓ 10MB Maximum File Size &nbsp;&nbsp;&nbsp;&nbsp; ✓ PDF Formats</p>", unsafe_allow_html=True)

        if uploaded_file:
            st.success(f"✅ Securely Loaded: **{uploaded_file.name}**")
            
            # Show "Summarize" button ONLY if this file hasn't been processed yet
            if st.session_state.get("filename") != uploaded_file.name:
                process_btn = st.button("✨ Summarize with AI", type="primary")

                if process_btn:
                    with st.spinner("Extracting parameters and indexing data via MedGemma..."):
                        result, status_code = upload_report(uploaded_file.read(), uploaded_file.name)

                    if status_code == 200:
                        st.session_state["report_id"] = result["report_id"]
                        st.session_state["filename"] = result["filename"]
                        # Save metrics data so it survives reruns
                        st.session_state["report_data"] = {
                            "type": result["report_type"].replace("_", " ").title(),
                            "params": result["parameters_found"]
                        }
                        st.rerun() # Force a rerun to lock in the state and show the chat
                    else:
                        st.error(result.get('detail', 'Processing failed'))
            
            # If the file HAS been processed, show the permanent metrics
            if st.session_state.get("filename") == uploaded_file.name:
                st.markdown("### 📊 Document Summary")
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                metrics_col1.metric("Tracking ID", st.session_state["report_id"][:8])
                metrics_col2.metric("Category", st.session_state["report_data"].get("type", "Unknown"))
                metrics_col3.metric("Data Points", st.session_state["report_data"].get("params", 0))

    # --- CHAT INTERFACE (Appears Below Uploader Only If Processed) ---
    if uploaded_file and st.session_state.get("filename") == uploaded_file.name:
        st.divider()
        st.markdown("<h3 style='text-align: center;'>💬 Chat with your Document</h3>", unsafe_allow_html=True)
        st.write("")
        
        st.markdown("**Suggested Queries:**")
        cols = st.columns(4)
        suggestions = ["Is blood sugar normal?", "Explain my cholesterol", "Any abnormal values?", "Give a simple summary"]
        for i, suggestion in enumerate(suggestions):
            if cols[i].button(suggestion, key=f"sug_{i}"):
                st.session_state["prefill_question"] = suggestion
                st.rerun() 

        st.write("")
        question = st.text_input("Ask a specific question:", value=st.session_state.get("prefill_question", ""), placeholder="e.g., What does my Hemoglobin A1C indicate?")
        
        col_btn, _ = st.columns([1, 4])
        with col_btn:
            ask_btn = st.button("Submit Query", type="primary")

        if ask_btn and question:
            with st.spinner("Searching medical vector database..."):
                result, status_code = ask_question(st.session_state["report_id"], question, selected_language_code, include_voice)
            check_api_health(force=True)

            if status_code == 200:
                st.markdown("### 💡 Intelligence Report")
                if selected_language_code != "en" and result.get("answer_translated"):
                    st.success(result["answer_translated"])
                    with st.expander("Show Original English Transcript"):
                        st.write(result["answer_english"])
                else:
                    st.success(result["answer_english"])

                if include_voice and result.get("voice_file_path") and os.path.exists(result["voice_file_path"]):
                    with open(result["voice_file_path"], "rb") as audio_file:
                        st.audio(audio_file.read(), format="audio/mp3")

                st.caption(f"⚡ Latency: {result.get('response_time_ms', 0):.0f}ms | 📄 Vector Chunks: {len(result.get('source_chunks', []))}")
                st.session_state["prefill_question"] = "" 
            else:
                st.error(result.get('detail', 'Could not fetch answer.'))


# ════════════════════════════════════════════════════════
# TAB 2: Prescription Reader
# ════════════════════════════════════════════════════════
with tab2:
    st.write("")
    col_l, col_m, col_r = st.columns([1, 2, 1]) 
    with col_m:
        rx_file = st.file_uploader("Upload Image or PDF", type=["pdf", "jpg", "jpeg", "png"], key="rx_uploader", label_visibility="collapsed")
        
        if not rx_file:
            st.markdown("<p class='check-text'>✓ 10MB Maximum File Size &nbsp;&nbsp;&nbsp;&nbsp; ✓ PDF, JPG, or PNG Formats</p>", unsafe_allow_html=True)

        if rx_file:
            st.success(f"✅ Document Loaded: {rx_file.name}")
            if rx_file.type.startswith("image"):
                st.image(rx_file, use_container_width=True, clamp=True)
            
            st.caption("🔍 Uses Hybrid Tesseract + MedGemma Pipeline")
            read_btn = st.button("✨ Initiate Scan", type="primary")

            if read_btn:
                with st.spinner("Running visual analysis and medical structuring..."):
                    try:
                        response = requests.post(f"{API_URL}/prescription/upload", files={"file": (rx_file.name, rx_file.read(), rx_file.type)}, timeout=300)
                        result = response.json()
                        status_code = response.status_code
                    except Exception as e:
                        st.error(f"Engine Failure: {str(e)}")
                        st.stop()

                if status_code == 200:
                    explanation = result.get("explanation", {})
                    medicines = explanation.get("medicines", [])

                    st.markdown("### 🩺 Prescriber Details")
                    doc_col, pat_col, date_col = st.columns(3)
                    doc_col.metric("Attending Doctor", explanation.get("doctor_name") or "Unverified")
                    pat_col.metric("Patient Record", explanation.get("patient_name") or "Unverified")
                    date_col.metric("Date Issued", explanation.get("date") or "Unverified")

                    if medicines:
                        st.markdown(f"### 💊 Identified Medications ({len(medicines)})")
                        for med in medicines:
                            with st.expander(f"{med.get('medicine_name', 'Unknown Medication')}", expanded=True):
                                med_col1, med_col2 = st.columns(2)
                                with med_col1:
                                    st.markdown(f"**Dosage:** `{med.get('dosage') or 'Not specified'}`")
                                    st.markdown(f"**Frequency:** `{med.get('frequency') or 'Not specified'}`")
                                with med_col2:
                                    st.markdown(f"**Duration:** `{med.get('duration') or 'Not specified'}`")
                                    st.markdown(f"**Instructions:** `{med.get('instructions') or 'Not specified'}`")
                                
                                if med.get("purpose"):
                                    st.info(f"**Indication:** {med.get('purpose')}")
                                if med.get("warnings"):
                                    st.warning(f"**Clinical Warnings:** {med.get('warnings')}")

                    if explanation.get("general_instructions"):
                        st.markdown("### 📝 Clinical Notes")
                        st.info(explanation.get("general_instructions"))

                else:
                    st.error(result.get('detail', 'Scan failed.'))