# rag/retrieval.py
"""
Retrieval: embed query → search pgvector → de-duplicate by patient.

For name-based queries (e.g. "what medications is Ramesh Nayak on"),
a metadata pre-filter is applied directly in SQL before vector search.
"""
import os
import re
import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

from rag.config import (
    VOYAGE_API_KEY,
    VOYAGE_MODEL,
    TOP_K,
)
from rag.providers.voyage_provider import VoyageProvider
from rag.providers.pgvector_store import PgVectorStore


def _get_providers():
    voyage = VoyageProvider(api_key=os.getenv('VOYAGE_API_KEY'), model=VOYAGE_MODEL)
    render_url = os.getenv('RENDER_DATABASE_URL') or os.getenv('DATABASE_URL')
    store = PgVectorStore(database_url=render_url)
    return voyage, store


def _detect_patient_name(query: str) -> str | None:
    """Detect if the query contains a patient name lookup."""
    clinical_keywords = {'cardiology', 'gastroenterology', 'hepatology',
                         'medicine', 'diagnosis', 'patient', 'show', 'what',
                         'which', 'find', 'list', 'how', 'who', 'are', 'is',
                         'me', 'the', 'for', 'with', 'and', 'or', 'in', 'on'}
    words = query.split()
    for i in range(len(words) - 1):
        w1, w2 = words[i].rstrip('.,?'), words[i+1].rstrip('.,?')
        if (w1[0].isupper() and w2[0].isupper()
                and w1.lower() not in clinical_keywords
                and w2.lower() not in clinical_keywords
                and len(w1) > 2 and len(w2) > 2):
            return f'{w1} {w2}'
    return None


def _search_by_name(name: str, top_k: int) -> list[dict]:
    """Direct metadata lookup by patient name."""
    render_url = os.getenv('RENDER_DATABASE_URL') or os.getenv('DATABASE_URL')
    conn = psycopg2.connect(render_url)
    register_vector(conn)
    sql = """
        SELECT id, patient_id, document, patient_name, visit_date,
               department, doctor_name, diagnosis_codes, has_followup,
               1.0 AS score
        FROM analytics.clinical_embeddings
        WHERE patient_name ILIKE %s
        ORDER BY visit_date DESC
        LIMIT %s;
    """
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (f'%{name}%', top_k))
            rows = cur.fetchall()
    finally:
        conn.close()
    return [
        {
            'document': row['document'],
            'metadata': {
                'patient_id': row['patient_id'],
                'patient_name': row['patient_name'],
                'visit_date': row['visit_date'],
                'department': row['department'],
                'doctor_name': row['doctor_name'],
                'diagnosis_codes': row['diagnosis_codes'],
                'has_followup': row['has_followup'],
            },
            'score': float(row['score']),
        }
        for row in rows
    ]


def retrieve(query: str, top_k: int = TOP_K, filters: dict | None = None) -> list[dict]:
    """
    Retrieve the most relevant clinical chunks for a query.

    For name-based queries: metadata pre-filter (partial name match).
    For all other queries: vector similarity search with de-duplication.
    """
    detected_name = _detect_patient_name(query)
    if detected_name:
        results = _search_by_name(detected_name, top_k)
        if results:
            return results

    voyage, store = _get_providers()
    query_embedding = voyage.embed_query(query)
    candidates = store.search(query_embedding=query_embedding, top_k=top_k * 3, filters=filters)

    seen_patients: set[int] = set()
    deduplicated: list[dict] = []
    for result in candidates:
        patient_id = result['metadata'].get('patient_id')
        if patient_id not in seen_patients:
            seen_patients.add(patient_id)
            deduplicated.append(result)
        if len(deduplicated) >= top_k:
            break

    return deduplicated


if __name__ == '__main__':
    load_dotenv()
    import sys
    query = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else 'cardiac patient with chest pain'
    print(f'Query: {query}\n')
    results = retrieve(query)
    for i, r in enumerate(results, 1):
        meta = r['metadata']
        print(f"{i}. {meta.get('patient_name')} (ID #{meta.get('patient_id')}) "
              f"| {meta.get('department')} | {meta.get('visit_date')} "
              f"| score: {r['score']:.4f}")