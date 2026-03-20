# rag/assistant.py
"""
Orchestrator: query → retrieve → synthesize → response.

Single entry point for the Flask routes and CLI.
Chains retrieval and synthesis, returns structured response.
"""
import os
import sys
from dotenv import load_dotenv

from rag.retrieval import retrieve
from rag.synthesis import synthesize
from rag.config import TOP_K


def ask(query: str, top_k: int = TOP_K) -> dict:
    """
    Main entry point for the Clinical AI Assistant.

    Chains retrieval + synthesis into a single call:
    1. retrieve(query) → top_k most relevant patient chunks
    2. synthesize(query, chunks) → grounded clinical answer

    Args:
        query: Natural language clinical query from the user.
        top_k: Number of patient chunks to retrieve (default from config).

    Returns:
        Dict with keys:
            answer: Grounded clinical response string.
            sources: List of {patient_id, patient_name, visit_date, department}.
            chunks_retrieved: Number of chunks used for synthesis.
            model: LLM model identifier.
    """
    chunks = retrieve(query, top_k=top_k)
    result = synthesize(query, chunks)
    return result


if __name__ == '__main__':
    load_dotenv()
    query = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else 'show me cardiac patients who missed follow-ups'
    print(f'Query: {query}\n')
    result = ask(query)
    print('─' * 60)
    print(result['answer'])
    print('─' * 60)
    print(f'\nSources ({result["chunks_retrieved"]} chunks retrieved):')
    for s in result['sources']:
        print(f"  • {s['patient_name']} (ID #{s['patient_id']}) | {s['department']} | {s['visit_date']}")
    print(f'\nModel: {result["model"]}')