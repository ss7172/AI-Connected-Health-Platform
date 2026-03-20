# rag/providers/claude_provider.py
"""
LLM provider using Claude Haiku for clinical query synthesis.

Claude Haiku is fast and cheap — ideal for structured clinical text
where the answer is grounded in retrieved context, not open-ended generation.
The system prompt is injected with retrieved chunks before synthesis.
"""
import anthropic
from rag.providers.base import LLMProvider


class ClaudeHaikuProvider(LLMProvider):
    """LLM provider backed by Claude Haiku via the Anthropic API."""

    def __init__(self, api_key: str, model: str = 'claude-haiku-4-5') -> None:
        """
        Initialize the Claude Haiku provider.

        Args:
            api_key: Anthropic API key.
            model: Claude model string.
        """
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        context_chunks: list[str],
    ) -> str:
        """
        Generate a grounded clinical response.

        Injects retrieved chunks into the system prompt at the
        {retrieved_chunks} placeholder, then calls Claude Haiku.

        Args:
            system_prompt: Clinical assistant instructions with {retrieved_chunks}.
            user_message: The user's natural language query.
            context_chunks: Retrieved document chunks to ground the response.

        Returns:
            Claude's response string.
        """
        context = '\n\n---\n\n'.join(context_chunks)
        full_system = system_prompt.replace('{retrieved_chunks}', context)

        response = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=full_system,
            messages=[{'role': 'user', 'content': user_message}],
        )
        return response.content[0].text

    @property
    def model_name(self) -> str:
        """Return the model identifier."""
        return self._model