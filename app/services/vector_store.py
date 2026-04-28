import os
# Must be set BEFORE chromadb is imported — covers all ChromaDB versions
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"

import chromadb
from chromadb.utils import embedding_functions
from fastapi import HTTPException
from app.core.config import settings
from app.core.logger import logger


class VectorStoreService:
    """
    Manages ChromaDB vector store for storing and retrieving
    medical report embeddings using the built-in SentenceTransformer model,
    completely bypassing Ollama.
    """

    def __init__(self):
        # ─── Persistent ChromaDB client ───────────────────
        # FIX: anonymized_telemetry=False resolves the startup error:
        #   "capture() takes 1 positional argument but 3 were given"
        # This is a known ChromaDB bug where their internal posthog telemetry
        # client has a signature mismatch with certain installed versions.
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=chromadb.Settings(anonymized_telemetry=False),
        )

        # ─── Use Built-in SentenceTransformers Embeddings ─
        # Bypasses Ollama completely to avoid Windows C++ crashes.
        # Downloads a lightweight, highly accurate model the first time it runs.
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

# ─── Get or create collection ─────────────────────
        self.collection = self.client.get_or_create_collection(
            name="medical_reports_v2",  # <-- BYPASS: Forces a brand new database!
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, report_id: str, chunks: list[str]) -> None:
        """
        Store text chunks from a medical report into the vector store.
        Each chunk gets a unique ID based on report_id and chunk index.
        """
        if not chunks:
            logger.warning(f"No chunks to add for report {report_id}")
            return

        ids = [f"{report_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"report_id": report_id, "chunk_index": i} for i in range(len(chunks))]

        self.collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )
        logger.info(f"Stored {len(chunks)} chunks for report {report_id}")

    def retrieve(self, report_id: str, query: str, top_k: int = 5) -> list[str]:
        """
        Retrieve the most relevant chunks for a query from a specific report.
        Filters by report_id so answers are grounded in the right document.
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where={"report_id": report_id}
            )
            chunks = results["documents"][0] if results["documents"] else []
            logger.info(f"Retrieved {len(chunks)} relevant chunks for query")
            return chunks

        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return []

    def delete_report(self, report_id: str) -> None:
        """Delete all chunks for a specific report."""
        try:
            self.collection.delete(where={"report_id": report_id})
            logger.info(f"Deleted all chunks for report {report_id}")

        except ValueError as e:
            logger.error(f"Validation Error: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=422, detail=str(e))

    def report_exists(self, report_id: str) -> bool:
        """Check if a report has already been indexed."""
        results = self.collection.get(where={"report_id": report_id})
        return len(results["ids"]) > 0


# ─── Singleton ────────────────────────────────────────────
vector_store = VectorStoreService()