# rag/synthesis.py
"""
Synthesis: retrieved chunks + query → Claude Haiku → grounded clinical answer.

The system prompt is the critical piece. It must:
1. Constrain Claude to ONLY use the provided records (no hallucination)
2. Require citations (patient names + IDs)
3. Explicitly state Claude is not a doctor
"""
import os
from rag.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from rag.providers.claude_provider import ClaudeHaikuProvider


SYSTEM_PROMPT = """You are a clinical data assistant for Redmond Polyclinic.
You answer questions using ONLY the patient records provided below.

RULES:
- Only reference patients and data present in the context.
- If the context doesn't contain enough information, say so explicitly.
- Never invent patient data, diagnoses, or medications.
- Always cite patient names and IDs when referencing records.
- Format responses clearly with numbered patient details.
- You are NOT a doctor. Do not provide medical advice or treatment recommendations.
- If asked about something outside the provided records, say "I don't have that information in the clinical records."

PATIENT RECORDS:
{retrieved_chunks}"""


def synthesize(query: str, retrieved_chunks: list[dict]) -> dict:
    """
    Generate a grounded clinical answer from retrieved chunks.

    Formats the retrieved chunks into a context string, injects into
    the system prompt, calls Claude Haiku, and extracts source citations
    from the chunk metadata.

    Args:
        query: The user's natural language query.
        retrieved_chunks: Output from retrieval.retrieve() —
                          list of {document, metadata, score}.

    Returns:
        Dict with keys:
            answer: Claude's response string.
            sources: List of {patient_id, patient_name, visit_date, department}.
            chunks_retrieved: Number of chunks used.
            model: Model identifier string.
    """
    if not retrieved_chunks:
        return {
            'answer': "I couldn't find any relevant patient records for that query.",
            'sources': [],
            'chunks_retrieved': 0,
            'model': CLAUDE_MODEL,
        }

    llm = ClaudeHaikuProvider(
        api_key=os.getenv('ANTHROPIC_API_KEY'),
        model=CLAUDE_MODEL,
    )

    # Format chunks as context — each chunk is self-contained (header + visit)
    chunk_texts = [r['document'] for r in retrieved_chunks]

    answer = llm.generate(
        system_prompt=SYSTEM_PROMPT,
        user_message=query,
        context_chunks=chunk_texts,
    )

    # Extract source citations from metadata
    sources = [
        {
            'patient_id': r['metadata'].get('patient_id'),
            'patient_name': r['metadata'].get('patient_name'),
            'visit_date': r['metadata'].get('visit_date'),
            'department': r['metadata'].get('department'),
        }
        for r in retrieved_chunks
    ]

    return {
        'answer': answer,
        'sources': sources,
        'chunks_retrieved': len(retrieved_chunks),
        'model': llm.model_name,
    }