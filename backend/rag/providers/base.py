# rag/providers/base.py
"""
Abstract base classes for all RAG provider interfaces.

Three abstractions:
- LLMProvider: swappable LLM backend (Claude, Ollama, GPT-4)
- EmbeddingProvider: swappable embedding model (Voyage, sentence-transformers)
- VectorStore: swappable vector storage (pgvector, ChromaDB, Pinecone)

Why ABCs? So we can swap any component without changing application code.
ClaudeHaikuProvider today, OllamaProvider tomorrow — same interface, different backend.
"""
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base for LLM synthesis backends."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_message: str,
        context_chunks: list[str],
    ) -> str:
        """
        Generate a response given system prompt, user query, and retrieved context.

        Args:
            system_prompt: Instructions for the model (grounding rules, format).
                           Contains {retrieved_chunks} placeholder.
            user_message: The user's natural language query.
            context_chunks: List of retrieved document chunks to inject into prompt.

        Returns:
            Generated response string.
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier for logging and status responses."""
        ...


class EmbeddingProvider(ABC):
    """Abstract base for text embedding models."""

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of document texts for storage in the vector store.

        Args:
            texts: List of document strings to embed.

        Returns:
            List of embedding vectors, one per input text.
        """
        ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """
        Embed a single query string for similarity search.

        Note: Some models use different representations for queries vs documents
        (e.g., Voyage's input_type='query' vs 'document'). This method handles
        query-specific embedding.

        Args:
            text: The query string to embed.

        Returns:
            Single embedding vector.
        """
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension (e.g., 1024 for voyage-3-lite)."""
        ...


class VectorStore(ABC):
    """Abstract base for vector storage and similarity search."""

    @abstractmethod
    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        """
        Insert or update vectors with associated metadata.

        Idempotent: running twice with the same IDs updates existing rows.

        Args:
            ids: Unique identifiers for each chunk (e.g., "42_visit_1").
            embeddings: Embedding vectors, one per chunk.
            documents: Raw chunk text, one per chunk.
            metadatas: Metadata dicts (patient_id, visit_date, department, etc.).
        """
        ...

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        """
        Return top_k most similar documents to the query embedding.

        Args:
            query_embedding: Embedded query vector.
            top_k: Number of results to return.
            filters: Optional metadata filters (e.g., {"department": "Cardiology"}).

        Returns:
            List of dicts, each with keys: document, metadata, score.
            Ordered by similarity descending (most similar first).
        """
        ...

    @abstractmethod
    def count(self) -> int:
        """
        Return total number of stored vectors.
        Used for auto-ingestion check: if count() == 0, trigger ingestion.
        """
        ...

    @abstractmethod
    def delete_collection(self) -> None:
        """
        Delete all stored vectors.
        Used before full re-ingestion to start fresh.
        """
        ...