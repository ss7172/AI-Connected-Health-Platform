# rag/providers/voyage_provider.py
"""
Embedding provider using Voyage AI's voyage-3-lite model.

Voyage AI is a separate service from Anthropic (though Anthropic-affiliated).
Accessed via the `voyageai` Python package — NOT the `anthropic` SDK.
Uses the same ANTHROPIC_API_KEY which doubles as a Voyage API key.

voyage-3-lite: 1024 dimensions, strong semantic quality, fast and cheap.
Cost: ~$0.02 to embed all 7,631 patient summaries (~15K chunks).
"""
import voyageai
from rag.providers.base import EmbeddingProvider


class VoyageProvider(EmbeddingProvider):
    """Embedding provider backed by Voyage AI's voyage-3-lite model."""

    def __init__(self, api_key: str, model: str = 'voyage-3-lite') -> None:
        import voyageai as _voyageai
        _voyageai.api_key = api_key          # set globally — required for this SDK version
        self._client = voyageai.Client(api_key=api_key)
        self._model = model
        self._dimension = 512

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of document texts for storage.

        Voyage API accepts up to 128 texts per call — batches internally.
        Uses input_type='document' which optimizes for storage-side retrieval.

        Args:
            texts: List of chunk texts to embed.

        Returns:
            List of 1024-dim embedding vectors.
        """
        all_embeddings = []
        batch_size = 128

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            result = self._client.embed(
                batch,
                model=self._model,
                input_type='document',
            )
            all_embeddings.extend(result.embeddings)

        return all_embeddings

    def embed_query(self, text: str) -> list[float]:
        """
        Embed a single query for similarity search.

        Uses input_type='query' — Voyage uses a different representation
        for queries vs documents, which improves retrieval accuracy.

        Args:
            text: The user's natural language query.

        Returns:
            Single 1024-dim embedding vector.
        """
        result = self._client.embed(
            [text],
            model=self._model,
            input_type='query',
        )
        return result.embeddings[0]

    @property
    def dimension(self) -> int:
        """Return embedding dimension (1024 for voyage-3-lite)."""
        return self._dimension