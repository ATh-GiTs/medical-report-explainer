import time
from app.services.ollama_service import ollama_service
from app.services.vector_store import vector_store
from app.services.translation_service import translation_service
from app.models.schemas import QueryRequest, QueryResponse
from app.core.logger import logger


# ─── System prompt for medical Q&A ────────────────────────
QA_SYSTEM_PROMPT = """You are a helpful medical assistant explaining medical reports 
to patients in simple, clear language. 

Important rules:
1. Only answer based on the provided report context
2. Use simple language — avoid complex medical jargon
3. If a value is abnormal, explain what it means clearly
4. Always recommend consulting a doctor for medical decisions
5. Be compassionate and reassuring in your tone
6. Keep answers concise but complete"""


class QueryAgent:
    """
    RAG-powered Q&A agent — retrieves relevant context from the
    vector store and generates patient-friendly explanations
    using MedGemma locally via Ollama.
    """

    def answer(self, request: QueryRequest) -> QueryResponse:
        """
        Full RAG pipeline:
        Question → Retrieve chunks → Build prompt → Generate → Translate
        """
        start_time = time.time()
        logger.info(f"Processing query for report {request.report_id}: {request.question[:50]}...")

        # ─── Step 1: Retrieve relevant chunks ─────────────
        relevant_chunks = vector_store.retrieve(
            report_id=request.report_id,
            query=request.question,
            top_k=5
        )

        if not relevant_chunks:
            return self._empty_response(request, start_time)

        # ─── Step 2: Build RAG prompt ──────────────────────
        context = "\n\n".join(relevant_chunks)
        prompt = self._build_prompt(request.question, context)

        # ─── Step 3: Generate answer with MedGemma ────────
        answer_english = ollama_service.generate(prompt, QA_SYSTEM_PROMPT, model_type="report")

        # ─── Step 4: Translate if needed ──────────────────
        answer_translated = None
        if request.target_language != "en":
            answer_translated = translation_service.translate(
                text=answer_english,
                target_language=request.target_language
            )

        # ─── Step 5: Voice output if requested ────────────
        voice_path = None
        if request.include_voice:
            text_for_voice = answer_translated or answer_english
            voice_path = translation_service.text_to_speech(
                text=text_for_voice,
                language=request.target_language
            )

        response_time = (time.time() - start_time) * 1000

        return QueryResponse(
            report_id=request.report_id,
            question=request.question,
            answer_english=answer_english,
            answer_translated=answer_translated,
            target_language=request.target_language,
            source_chunks=relevant_chunks[:2],  # Return top 2 for transparency
            voice_file_path=voice_path,
            response_time_ms=round(response_time, 2)
        )

    def _build_prompt(self, question: str, context: str) -> str:
        """Build the RAG prompt with retrieved context."""
        return f"""Use the following medical report information to answer the patient's question.
        
MEDICAL REPORT CONTEXT:
{context}

PATIENT'S QUESTION:
{question}

Please explain in simple, easy-to-understand language that a non-medical person can understand.
If the answer involves abnormal values, explain what they mean and suggest the patient consult their doctor."""

    def _empty_response(self, request: QueryRequest, start_time: float) -> QueryResponse:
        """Return a helpful response when no relevant chunks found."""
        response_time = (time.time() - start_time) * 1000
        return QueryResponse(
            report_id=request.report_id,
            question=request.question,
            answer_english="I could not find relevant information in your report to answer this question. Please check if the report was uploaded correctly or try rephrasing your question.",
            target_language=request.target_language,
            response_time_ms=round(response_time, 2)
        )


# ─── Singleton ────────────────────────────────────────────
query_agent = QueryAgent()
