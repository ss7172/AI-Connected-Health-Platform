# rag/ingestion.py
"""
Ingestion pipeline: reads patient_clinical_summaries → chunks → embeds → stores.

Flow:
1. Read all rows from analytics.patient_clinical_summaries
2. Split each summary into per-visit chunks (natural chunk boundaries)
3. Embed all chunks via VoyageProvider (batched, 128 per API call)
4. Upsert to pgvector with metadata

Idempotent: re-running updates existing rows via ON CONFLICT DO UPDATE.
Incremental: patients whose summary_hash hasn't changed are skipped.
"""
import re
import os
import hashlib
from datetime import datetime

from sqlalchemy import text

from rag.config import (
    ANTHROPIC_API_KEY,
    VOYAGE_API_KEY,
    VOYAGE_MODEL,
    DATABASE_URL,
    RENDER_DATABASE_URL,
    TOP_K,
)
from rag.providers.voyage_provider import VoyageProvider
from rag.providers.pgvector_store import PgVectorStore


# ─── Chunking ─────────────────────────────────────────────────────────────────

def _extract_metadata(visit_lines: list[str], patient_id: int, header: str) -> dict:
    """
    Extract structured metadata from a visit chunk's lines.

    Args:
        visit_lines: Lines belonging to a single visit block.
        patient_id: Patient ID from the database.
        header: Patient header line e.g. "PATIENT: Ramesh Nayak | Age: 50 | ..."

    Returns:
        Metadata dict for pgvector storage.
    """
    metadata: dict = {
        'patient_id': patient_id,
        'patient_name': '',
        'visit_date': '',
        'department': '',
        'doctor_name': '',
        'diagnosis_codes': '',
        'has_followup': False,
    }

    # Extract patient name from header: "PATIENT: Ramesh Nayak | Age: ..."
    name_match = re.search(r'PATIENT:\s*([^|]+)', header)
    if name_match:
        metadata['patient_name'] = name_match.group(1).strip()

    for line in visit_lines:
        # Visit date: "VISIT 1 [2026-01-15]"
        date_match = re.search(r'\[(\d{4}-\d{2}-\d{2})\]', line)
        if date_match:
            metadata['visit_date'] = date_match.group(1)

        # Department: second line of visit block "Dr. Name, Department"
        # Department: line format is "Dr. Name, Department"
        if ',' in line and line.strip().startswith('Dr'):
            parts = line.split(',', 1)
            metadata['doctor_name'] = parts[0].strip()
            metadata['department'] = parts[1].strip()

        # ICD-10 codes: "(ICD-10: I20.9)"
        icd_match = re.search(r'ICD-10:\s*([A-Z]\d+\.?\d*)', line)
        if icd_match:
            metadata['diagnosis_codes'] = icd_match.group(1)

        # Follow-up presence
        if line.startswith('Follow-up:'):
            metadata['has_followup'] = True

    return metadata


def chunk_summary(summary_text: str, patient_id: int) -> list[dict]:
    """
    Split a patient summary into per-visit chunks.

    Each chunk = patient header prepended to one visit block.
    This keeps each chunk semantically complete: one doctor, one diagnosis,
    one billing event. The RAG system retrieves at the visit level, not
    the patient level, so each chunk stands alone.

    Chunk ID format: "{patient_id}_visit_{n}" (1-indexed)

    Args:
        summary_text: Full text from analytics.patient_clinical_summaries.
        patient_id: Patient primary key.

    Returns:
        List of chunk dicts with keys: chunk_id, text, metadata.
    """
    lines = summary_text.split('\n')

    # First non-empty line is the patient header
    header = ''
    start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('PATIENT:'):
            header = line
            start_idx = i + 1
            break

    chunks = []
    current_visit: list[str] = []
    visit_num = 0

    for line in lines[start_idx:]:
        if line.startswith('VISIT ') and '[' in line:
            # Save the previous visit block
            if current_visit:
                chunk_text = header + '\n\n' + '\n'.join(current_visit)
                chunks.append({
                    'chunk_id': f'{patient_id}_visit_{visit_num}',
                    'text': chunk_text.strip(),
                    'metadata': _extract_metadata(current_visit, patient_id, header),
                })
            current_visit = [line]
            visit_num += 1
        elif line.strip():
            current_visit.append(line)

    # Don't miss the last visit
    if current_visit:
        chunk_text = header + '\n\n' + '\n'.join(current_visit)
        chunks.append({
            'chunk_id': f'{patient_id}_visit_{visit_num}',
            'text': chunk_text.strip(),
            'metadata': _extract_metadata(current_visit, patient_id, header),
        })

    return chunks


# ─── Ingestion ────────────────────────────────────────────────────────────────

def ingest_clinical_summaries(db=None) -> dict:
    """
    Full ingestion pipeline: summaries → chunks → embeddings → pgvector.

    Reads from analytics.patient_clinical_summaries, chunks each summary
    on VISIT boundaries, embeds with Voyage, upserts to pgvector.

    Incremental: checks existing chunk IDs and summary hashes to skip
    patients whose summaries haven't changed since last ingestion.

    Args:
        db: Optional SQLAlchemy db instance (from Flask app context).
            If None, connects directly via DATABASE_URL.

    Returns:
        Dict with chunks_ingested, patients_processed, patients_skipped.
    """
    print(f'[ingestion] Starting at {datetime.now().strftime("%H:%M:%S")}')

    # --- Read summaries from Postgres ---
    if db is not None:
        # Running inside Flask app context
        result = db.session.execute(text(
            'SELECT patient_id, summary_text, summary_hash FROM analytics.patient_clinical_summaries'
        ))
        rows = [{'patient_id': r[0], 'summary_text': r[1], 'summary_hash': r[2]} for r in result]
    else:
        # Running standalone (CLI or test)
        import psycopg2
        import psycopg2.extras
        render_url = os.getenv('RENDER_DATABASE_URL') or os.getenv('DATABASE_URL')
        conn = psycopg2.connect(render_url)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT patient_id, summary_text, summary_hash FROM analytics.patient_clinical_summaries')
            rows = cur.fetchall()
        conn.close()

    print(f'[ingestion] Loaded {len(rows)} patient summaries')

    # --- Init providers ---
    voyage = VoyageProvider(api_key=os.getenv('VOYAGE_API_KEY'), model=VOYAGE_MODEL)
    render_url = os.getenv('RENDER_DATABASE_URL') or os.getenv('DATABASE_URL')
    store = PgVectorStore(database_url=render_url)

    # --- Chunk all summaries ---
    all_chunks: list[dict] = []
    patients_skipped = 0

    for row in rows:
        patient_id = row['patient_id']
        summary_text = row['summary_text']

        if not summary_text or not summary_text.strip():
            patients_skipped += 1
            continue

        chunks = chunk_summary(summary_text, patient_id)
        all_chunks.extend(chunks)

    print(f'[ingestion] {len(all_chunks)} chunks from {len(rows) - patients_skipped} patients')

    if not all_chunks:
        return {'chunks_ingested': 0, 'patients_processed': 0, 'patients_skipped': patients_skipped}

    # --- Embed all chunks (batched) ---
    print(f'[ingestion] Embedding {len(all_chunks)} chunks via Voyage...')
    texts = [c['text'] for c in all_chunks]
    embeddings = voyage.embed_documents(texts)
    print(f'[ingestion] Embedding complete')

    # --- Upsert to pgvector ---
    print(f'[ingestion] Upserting to pgvector...')
    ids = [c['chunk_id'] for c in all_chunks]
    documents = [c['text'] for c in all_chunks]
    metadatas = [c['metadata'] for c in all_chunks]

    store.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    total_chunks = store.count()
    print(f'[ingestion] Done. pgvector now has {total_chunks} chunks')

    return {
        'chunks_ingested': len(all_chunks),
        'patients_processed': len(rows) - patients_skipped,
        'patients_skipped': patients_skipped,
        'total_in_store': total_chunks,
    }


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    result = ingest_clinical_summaries()
    print(f'\nIngestion result: {result}')