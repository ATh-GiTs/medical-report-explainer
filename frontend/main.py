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

# ─── Modern Clinical AI UI/UX CSS Injection ────────────────
def inject_custom_css():
    st.markdown("""
    <style>
        /* Hide default Streamlit footer */
        footer {visibility: hidden;}

        /* APP BACKGROUND & TYPOGRAPHY */
        .stApp {
            background-color: #F8FAFC; 
            font-family: 'Inter', -apple-system, sans-serif;
            color: #0F172A; 
        }

        /* GLOBALLY INCREASE TEXT SIZE */
        .stMarkdown, .stText, p, span, li, label {
            font-size: 1.1rem !important;
        }

        h1 { color: #0F172A; font-weight: 800; font-size: 3rem !important; letter-spacing: -0.03em;}
        h2 { color: #1E293B; font-weight: 700; font-size: 2.2rem !important; letter-spacing: -0.02em;}
        h3 { color: #334155; font-weight: 700; font-size: 1.6rem !important; }

        /* HERO SECTION TYPOGRAPHY */
        .hero-title {
            text-align: center;
            font-size: 3.2rem !important;
            font-weight: 800;
            background: linear-gradient(135deg, #0F172A 0%, #334155 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-top: -20px;
            margin-bottom: 5px;
        }
        .hero-subtitle {
            text-align: center;
            font-size: 1.25rem !important;
            color: #64748B;
            font-weight: 500;
            margin-bottom: 20px;
        }

        /* =========================================
           TOP NAVIGATION SHAPES & BORDERS
           ========================================= */
        div[data-testid="stSelectbox"] > div[data-baseweb="select"] {
            border-radius: 12px !important;
            border: 1px solid #CBD5E1 !important;
            background-color: #FFFFFF !important;
            padding: 4px 12px !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        }

        div[data-testid="stPopover"] > button {
            border-radius: 12px !important;
            border: 1px solid #CBD5E1 !important;
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            padding: 5px 20px !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stPopover"] > button:hover {
            border-color: #0284C7 !important;
            color: #0284C7 !important;
            background-color: #F0F9FF !important;
        }

        /* PRIMARY GRADIENT BUTTONS */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 15px 30px !important;
            font-size: 1.15rem !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 14px rgba(2, 132, 199, 0.3) !important;
            transition: all 0.3s ease !important;
        }
        .stButton > button[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(2, 132, 199, 0.4) !important;
        }

        /* PILL-STYLE SEGMENTED TABS */
        .stTabs > div > div[data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #E2E8F0; 
            padding: 6px;
            border-radius: 100px; 
            border-bottom: none; 
            justify-content: center; 
            margin-bottom: 30px;
            display: flex;
            width: fit-content;
            margin-left: auto;
            margin-right: auto;
        }
        .stTabs > div > div[data-baseweb="tab-list"]::before {
            display: none !important; 
        }
        .stTabs [data-baseweb="tab"] {
            height: 45px;
            border-radius: 100px !important; 
            padding: 10px 30px;
            color: #64748B; 
            font-weight: 600;
            font-size: 1.1rem;
            border: none !important;
            background-color: transparent;
            transition: all 0.3s ease;
        }
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important;
            color: #0284C7 !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
            border: none !important;
        }

        /* FILE UPLOADER HACK */
        [data-testid="stFileUploadDropzone"] {
            border: 2px dashed #94A3B8 !important; 
            border-radius: 16px !important;
            background-color: #FFFFFF !important; 
            padding: 60px 20px !important; 
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02);
            transition: all 0.3s ease;
        }
        [data-testid="stFileUploadDropzone"]:hover {
            border-color: #0284C7 !important;
            background-color: #F0F9FF !important;
        }
        [data-testid="stFileUploadDropzone"] svg { display: none !important; }
        [data-testid="stFileUploadDropzone"] > div > div::before {
            content: "Drag & drop your file here or";
            display: block;
            font-size: 1.25rem;
            color: #334155;
            font-weight: 600;
            margin-bottom: 15px;
            text-align: center;
        }
        [data-testid="stFileUploadDropzone"] .css-1b1hlgl, [data-testid="stFileUploadDropzone"] .css-1v0mbdj { display: none !important; }
        [data-testid="stFileUploadDropzone"] button {
            background-color: #1E293B !important; 
            color: #FFFFFF !important;
            border-radius: 8px !important;
            padding: 10px 30px !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            border: none !important;
            margin: 0 auto !important;
            display: block !important;
        }
        [data-testid="stFileUploadDropzone"] button:hover { background-color: #0F172A !important; }
        [data-testid="stFileUploadDropzone"] small { display: none !important; }

        /* RESULT CARDS & EXPANDERS */
        [data-testid="stMetric"], .stExpander {
            background-color: #FFFFFF;
            border-radius: 16px;
            padding: 20px; 
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            border: 1px solid #E2E8F0; 
            transition: transform 0.2s ease;
        }
        [data-testid="stMetric"]:hover { transform: translateY(-2px); }
        [data-testid="stMetricValue"] > div {
            font-size: 1.7rem !important; 
            color: #0284C7 !important;
            font-weight: 800 !important;
            white-space: normal !important; 
            word-wrap: break-word !important; 
            line-height: 1.3 !important;
        }
        [data-testid="stMetricLabel"] p {
            font-size: 1.1rem !important;
            color: #64748B !important;
            font-weight: 600 !important;
        }
        
        /* SIDEBAR STYLING */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF; 
            border-right: 1px solid #E2E8F0;
        }
        
        .check-text {
            text-align: center; 
            color: #64748B; 
            font-size: 1rem; 
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
if "rx_result" not in st.session_state:
    st.session_state["rx_result"] = None
if "rx_filename" not in st.session_state:
    st.session_state["rx_filename"] = ""

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

# ─── Sidebar Dashboard ────────────────────────────────────
with st.sidebar:
    # INDESTRUCTIBLE INLINE SVG LOGO + CUSTOM HEADER
    logo_html = """
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 25px; margin-top: -10px;">
        <div style="background: linear-gradient(135deg, #0284C7, #0369A1); padding: 12px; border-radius: 12px; box-shadow: 0 4px 10px rgba(2,132,199,0.3);">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
            </svg>
        </div>
        <div>
            <h2 style="margin: 0; font-size: 1.4rem; color: #0F172A; line-height: 1.2; letter-spacing: -0.03em;">Report Explainer</h2>
            <h2 style="margin: 0; font-size: 1.4rem; color: #0284C7; line-height: 1.2; letter-spacing: -0.03em;">& RX Reader</h2>
        </div>
    </div>
    """
    st.markdown(logo_html, unsafe_allow_html=True)
    
    st.markdown("<h4 style='margin-top: 0px; margin-bottom: 5px; font-size: 1.2rem; color: #64748B;'>System Health</h4>", unsafe_allow_html=True)
    st.divider()

    if st.session_state["is_processing"]:
        st.info("⏳ Processing data...", icon="🔄")
    else:
        health = check_api_health()
        if health:
            st.success("API Online", icon="🟢")
            if health.get("ollama_connected", False):
                st.success("Groq Cloud Online", icon="⚡")
            else:
                st.warning("Groq Offline", icon="⚠️")
        else:
            st.error("API Offline - Start Uvicorn", icon="🔴")

    if st.button("🔄 Refresh Connection", use_container_width=True):
        check_api_health(force=True)
        st.rerun()

    st.divider()
    st.markdown("### 🛠️ Tech Stack")
    st.markdown("""
    <div style="font-size: 1rem; color: #475569; line-height: 2;">
        <b>✓ Streamlit</b> &middot; Frontend UI<br>
        <b>✓ FastAPI</b> &middot; Backend Server<br>
        <b>✓ Groq Llama 3.3</b> &middot; Text Engine<br>
        <b>✓ Groq Llama 4 Scout</b> &middot; Vision Engine<br>
        <b>✓ Local Nomic</b> &middot; Vector Embeddings<br>
        <b>✓ ChromaDB</b> &middot; Vector Database
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    with st.popover("⚙️ How It Works", use_container_width=True):
        st.markdown("**1. Ingest:** Drag & drop a PDF or Image.")
        st.markdown("**2. Extract:** Hybrid pipeline parses digital text or uses OCR for handwriting.")
        st.markdown("**3. Structure:** Groq AI structures the messy medical data safely.")
        st.markdown("**4. Chat:** Semantic search retrieves exact answers from your report.")

# ─── Main Content Area (Hero Section) ──────────────────────
st.write("") # Tiny top buffer
st.markdown("<div class='hero-title'>Summarize Medical Reports with AI</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-subtitle'>Instant AI summaries and clinical insights for lab reports and prescriptions.</div>", unsafe_allow_html=True)

# ─── ACTION TOOLBAR (Right Aligned above tabs) ────────────
col_spacer, col_lang, col_voice = st.columns([7.5, 1.8, 1.2])

with col_lang:
    selected_language_name = st.selectbox("Language", options=list(LANGUAGES.keys()), index=0, label_visibility="collapsed")
    selected_language_code = LANGUAGES[selected_language_name]
with col_voice:
    # A small CSS nudge to make the toggle switch align perfectly with the selectbox
    st.markdown("<div style='margin-top: 4px;'></div>", unsafe_allow_html=True)
    include_voice = st.toggle("🔊 Voice", value=False)

# ─── COMBINED TABS ────────────────────────────────────────
tab1, tab2 = st.tabs(["📄 AI Summarizer & Chat", "💊 AI Prescription Reader"])

# ════════════════════════════════════════════════════════
# TAB 1: Upload Report & Chat
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
            
            if st.session_state.get("filename") != uploaded_file.name:
                process_btn = st.button("✨ Summarize with AI", type="primary", use_container_width=True)

                if process_btn:
                    with st.spinner("Extracting parameters and indexing data via Groq Llama 3.3..."):
                        result, status_code = upload_report(uploaded_file.read(), uploaded_file.name)

                    if status_code == 200:
                        st.session_state["report_id"] = result["report_id"]
                        st.session_state["filename"] = result["filename"]
                        st.session_state["report_data"] = {
                            "type": result["report_type"].replace("_", " ").title(),
                            "params": result["parameters_found"]
                        }
                        st.rerun() 
                    else:
                        st.error(result.get('detail', 'Processing failed'))
            
            if st.session_state.get("filename") == uploaded_file.name:
                st.markdown("### 📊 Document Summary")
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                metrics_col1.metric("Tracking ID", st.session_state["report_id"][:8])
                metrics_col2.metric("Category", st.session_state["report_data"].get("type", "Unknown"))
                metrics_col3.metric("Data Points", st.session_state["report_data"].get("params", 0))

    if uploaded_file and st.session_state.get("filename") == uploaded_file.name:
        st.divider()
        st.markdown("<h3 style='text-align: center; color: #0284C7;'>💬 Chat with your Document</h3>", unsafe_allow_html=True)
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
    
    col_img, col_spacer, col_results = st.columns([1, 0.1, 1.2]) 
    
    with col_img:
        rx_file = st.file_uploader("Upload Image or PDF", type=["pdf", "jpg", "jpeg", "png"], key="rx_uploader", label_visibility="collapsed")
        
        if not rx_file:
            st.markdown("<p class='check-text'>✓ 10MB Maximum File Size &nbsp;&nbsp;&nbsp;&nbsp; ✓ PDF, JPG, or PNG Formats</p>", unsafe_allow_html=True)

        if rx_file:
            st.success(f"✅ Loaded: {rx_file.name}")
            if rx_file.type.startswith("image"):
                st.image(rx_file, use_container_width=True, clamp=True)
            
            st.caption("🔍 Powered by Groq Llama 4 Scout Vision")
            
            if st.session_state["rx_filename"] != rx_file.name:
                st.session_state["rx_result"] = None
                
            read_btn = st.button("✨ Initiate Scan", type="primary", use_container_width=True)
            
            if read_btn:
                with st.spinner("Running visual analysis via Groq Vision API..."):
                    try:
                        response = requests.post(f"{API_URL}/prescription/upload", files={"file": (rx_file.name, rx_file.read(), rx_file.type)}, timeout=300)
                        
                        if response.status_code == 200:
                            st.session_state["rx_result"] = response.json()
                            st.session_state["rx_filename"] = rx_file.name
                        else:
                            st.error(response.json().get('detail', 'Scan failed.'))
                    except Exception as e:
                        st.error(f"Engine Failure: {str(e)}")

    with col_results:
        result = st.session_state.get("rx_result")
        
        if result:
            explanation = result.get("explanation", {})
            medicines = explanation.get("medicines", [])

            st.markdown("### 🩺 Prescriber Details")
            doc_col, pat_col = st.columns(2)
            with doc_col:
                st.metric("Attending Doctor", explanation.get("doctor_name") or "Unverified")
            with pat_col:
                st.metric("Patient Record", explanation.get("patient_name") or "Unverified")
            
            st.metric("Date Issued", explanation.get("date") or "Unverified")

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

        elif not rx_file:
            st.info("👈 Upload a prescription image to see the extracted data here.")