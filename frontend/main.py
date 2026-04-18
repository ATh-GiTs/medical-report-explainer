import streamlit as st
import requests
import os
import time

# ─── Page Config ──────────────────────────────────────────
st.set_page_config(
    page_title="Medical Report Explainer",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── API Base URL ─────────────────────────────────────────
API_URL = "http://localhost:8000/api/v1"

# ─── Language Options ─────────────────────────────────────
LANGUAGES = {
    "English": "en",
    "Hindi (हिंदी)": "hi",
    "Marathi (मराठी)": "mr",
    "Tamil (தமிழ்)": "ta",
    "Bengali (বাংলা)": "bn",
    "Telugu (తెలుగు)": "te",
    "Gujarati (ગુજરાતી)": "gu",
}

# ─── Session State Initialization ─────────────────────────
if "api_status" not in st.session_state:
    st.session_state["api_status"] = None
if "last_health_check" not in st.session_state:
    st.session_state["last_health_check"] = 0
if "is_processing" not in st.session_state:
    st.session_state["is_processing"] = False


# ─── Helper: Check API Health (cached for 10 seconds) ─────
def check_api_health(force=False):
    """
    Check API health but cache result for 10 seconds.
    This prevents health check from running during active queries
    and falsely showing API as down.
    """
    now = time.time()
    # Only re-check if 10 seconds have passed OR force refresh
    if force or (now - st.session_state["last_health_check"]) > 10:
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            if response.status_code == 200:
                st.session_state["api_status"] = response.json()
            else:
                st.session_state["api_status"] = None
        except Exception:
            # If processing is happening, don't mark as down
            if not st.session_state["is_processing"]:
                st.session_state["api_status"] = None
        st.session_state["last_health_check"] = now

    return st.session_state["api_status"]


# ─── Helper: Upload Report ────────────────────────────────
def upload_report(file_bytes, filename):
    try:
        st.session_state["is_processing"] = True
        response = requests.post(
            f"{API_URL}/report/upload",
            files={"file": (filename, file_bytes, "application/pdf")},
            timeout=300
        )
        st.session_state["is_processing"] = False
        return response.json(), response.status_code
    except requests.exceptions.Timeout:
        st.session_state["is_processing"] = False
        return {"detail": "Request timed out. The AI is still processing — please wait and try again."}, 408
    except requests.exceptions.ConnectionError:
        st.session_state["is_processing"] = False
        return {"detail": "Cannot connect to API. Make sure FastAPI is running (uvicorn main:app --reload)"}, 503
    except Exception as e:
        st.session_state["is_processing"] = False
        return {"detail": f"Unexpected error: {str(e)}"}, 500


# ─── Helper: Ask Question ─────────────────────────────────
def ask_question(report_id, question, language, include_voice):
    try:
        st.session_state["is_processing"] = True
        response = requests.post(
            f"{API_URL}/report/query",
            json={
                "report_id": report_id,
                "question": question,
                "target_language": language,
                "include_voice": include_voice
            },
            timeout=300
        )
        st.session_state["is_processing"] = False
        return response.json(), response.status_code
    except requests.exceptions.Timeout:
        st.session_state["is_processing"] = False
        return {"detail": "The AI took too long to respond. Try a simpler question or restart Ollama."}, 408
    except requests.exceptions.ConnectionError:
        st.session_state["is_processing"] = False
        return {"detail": "Cannot connect to API. Make sure FastAPI is running."}, 503
    except Exception as e:
        st.session_state["is_processing"] = False
        return {"detail": f"Unexpected error: {str(e)}"}, 500


# ─── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/heart-with-pulse.png", width=80)
    st.title("🏥 Medical Report Explainer")
    st.markdown("*Powered by MedGemma AI — runs 100% locally*")
    st.divider()

    # ─── API Status ───────────────────────────────────────
    st.subheader("⚙️ System Status")

    # Show processing message instead of false API down
    if st.session_state["is_processing"]:
        st.warning("⏳ AI is processing... please wait")
        st.info("🤖 Ollama: Working")
    else:
        health = check_api_health()
        if health:
            st.success("✅ API is running")
            ollama_ok = health.get("ollama_connected", False)
            if ollama_ok:
                st.info("🤖 Ollama: ✅ Connected")
            else:
                st.warning("🤖 Ollama: ⚠️ Not connected — run: ollama serve")
        else:
            st.error("❌ API is not running")
            st.warning("Start FastAPI:\n```\nuvicorn main:app --reload\n```")

    # ─── Manual refresh button ────────────────────────────
    if st.button("🔄 Refresh Status", use_container_width=True):
        check_api_health(force=True)
        st.rerun()

    st.divider()

    # ─── Language Selector ────────────────────────────────
    st.subheader("🌍 Select Language")
    selected_language_name = st.selectbox(
        "Response Language",
        options=list(LANGUAGES.keys()),
        index=0
    )
    selected_language_code = LANGUAGES[selected_language_name]

    # ─── Voice Option ─────────────────────────────────────
    include_voice = st.toggle("🔊 Voice Output", value=False)

    st.divider()
    st.caption("Built with ❤️ using MedGemma, ChromaDB, FastAPI & Streamlit")


# ─── Main Content ─────────────────────────────────────────
st.title("🏥 Medical Report Explainer")
st.markdown("**Upload your medical report and ask questions in your language**")
st.divider()

# ─── Tab Layout ───────────────────────────────────────────
tab1, tab2 = st.tabs(["📤 Upload Report", "💬 Ask Questions"])


# ════════════════════════════════════════════════════════
# TAB 1: Upload Report
# ════════════════════════════════════════════════════════
with tab1:
    st.subheader("Upload Your Medical Report")
    st.markdown("Supported format: **PDF only** | Max size: **10MB**")

    uploaded_file = st.file_uploader(
        "Choose a medical report PDF",
        type=["pdf"],
        help="Upload blood test reports, prescriptions, discharge summaries etc."
    )

    if uploaded_file:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(f"📄 **File:** {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        with col2:
            process_btn = st.button("🚀 Process Report", type="primary", use_container_width=True)

        if process_btn:
            with st.spinner("🔍 AI is analyzing your medical report... this may take 30-60 seconds"):
                result, status_code = upload_report(uploaded_file.read(), uploaded_file.name)

            if status_code == 200:
                st.success(f"✅ {result.get('message', 'Report processed!')}")
                st.session_state["report_id"] = result["report_id"]
                st.session_state["filename"] = result["filename"]

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Report ID", result["report_id"])
                with col2:
                    st.metric("Report Type", result["report_type"].replace("_", " ").title())
                with col3:
                    st.metric("Parameters Found", result["parameters_found"])

                st.info("👉 Go to the **Ask Questions** tab to start asking about your report!")

            elif status_code == 408:
                st.warning(f"⏳ {result.get('detail')}")
            elif status_code == 503:
                st.error(f"🔌 {result.get('detail')}")
            else:
                st.error(f"❌ Error: {result.get('detail', 'Processing failed')}")


# ════════════════════════════════════════════════════════
# TAB 2: Ask Questions
# ════════════════════════════════════════════════════════
with tab2:
    st.subheader("Ask Questions About Your Report")

    if "report_id" not in st.session_state:
        st.warning("⚠️ Please upload a medical report first in the **Upload Report** tab.")
    else:
        st.success(f"📄 Active Report: **{st.session_state.get('filename', 'Unknown')}** (ID: `{st.session_state['report_id']}`)")
        st.divider()

        # ─── Suggested questions ──────────────────────────
        st.markdown("**💡 Suggested Questions:**")
        suggestions = [
            "Is my blood sugar normal?",
            "What does my cholesterol mean?",
            "Which values are abnormal?",
            "Summarize my report simply",
            "Should I be worried?",
        ]

        cols = st.columns(len(suggestions))
        for i, suggestion in enumerate(suggestions):
            if cols[i].button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                st.session_state["prefill_question"] = suggestion

        # ─── Question Input ───────────────────────────────
        question = st.text_input(
            "Your Question",
            value=st.session_state.pop("prefill_question", ""),
            placeholder="e.g. Is my hemoglobin level normal?",
        )

        ask_btn = st.button("🔍 Get Answer", type="primary")

        if ask_btn and question:
            # ─── Show clear processing state ──────────────
            with st.spinner(f"🤖 MedGemma is thinking... responding in {selected_language_name} — please wait up to 60 seconds"):
                result, status_code = ask_question(
                    report_id=st.session_state["report_id"],
                    question=question,
                    language=selected_language_code,
                    include_voice=include_voice
                )

            # ─── Force refresh status after query ─────────
            check_api_health(force=True)

            if status_code == 200:
                st.divider()

                # ─── Show Answer ──────────────────────────
                if selected_language_code != "en" and result.get("answer_translated"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**🇬🇧 English Answer:**")
                        st.info(result["answer_english"])
                    with col2:
                        st.markdown(f"**{selected_language_name} Answer:**")
                        st.success(result["answer_translated"])
                else:
                    st.markdown("**🤖 AI Answer:**")
                    st.info(result["answer_english"])

                # ─── Voice Output ─────────────────────────
                if include_voice and result.get("voice_file_path"):
                    voice_path = result["voice_file_path"]
                    if os.path.exists(voice_path):
                        st.markdown("**🔊 Listen to Answer:**")
                        with open(voice_path, "rb") as audio_file:
                            st.audio(audio_file.read(), format="audio/mp3")

                # ─── Response metadata ────────────────────
                st.caption(
                    f"⚡ Response time: {result.get('response_time_ms', 0):.0f}ms | "
                    f"🔒 Processed locally | "
                    f"📄 Based on {len(result.get('source_chunks', []))} relevant sections"
                )

            elif status_code == 408:
                st.warning(f"⏳ {result.get('detail')}")
                st.info("💡 **Tip:** Try asking a shorter, simpler question. Or restart Ollama and try again.")
            elif status_code == 503:
                st.error(f"🔌 {result.get('detail')}")
            else:
                st.error(f"❌ {result.get('detail', 'Could not get answer. Please try again.')}")

        elif ask_btn and not question:
            st.warning("Please type a question first!")
