# rag/providers/pgvector_store.py
"""
Vector store backed by pgvector in the existing PostgreSQL database.

Why pgvector over ChromaDB:
- Lives in the same Postgres as the PMS — persists across Render restarts
- ChromaDB writes to local disk which is ephemeral on Render free tier
- No new service, no new infrastructure, same DATABASE_URL

Uses psycopg2 directly (not SQLAlchemy ORM) because SQLAlchemy doesn't
natively handle pgvector's <=> cosine distance operator in queries.
"""
import os
import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector

from rag.providers.base import VectorStore


# SQL executed once on init — idempotent (IF NOT EXISTS throughout)
_SETUP_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS analytics.clinical_embeddings (
    id            TEXT PRIMARY KEY,
    patient_id    INTEGER NOT NULL,
    document      TEXT NOT NULL,
    embedding     vector(512),
    patient_name  TEXT,
    visit_date    TEXT,
    department    TEXT,
    doctor_name   TEXT,
    diagnosis_codes TEXT,
    has_followup  BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS clinical_embeddings_hnsw
    ON analytics.clinical_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
"""

_UPSERT_SQL = """
INSERT INTO analytics.clinical_embeddings
    (id, patient_id, document, embedding,
     patient_name, visit_date, department, doctor_name,
     diagnosis_codes, has_followup, updated_at)
VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
ON CONFLICT (id) DO UPDATE SET
    document        = EXCLUDED.document,
    embedding       = EXCLUDED.embedding,
    patient_name    = EXCLUDED.patient_name,
    visit_date      = EXCLUDED.visit_date,
    department      = EXCLUDED.department,
    doctor_name     = EXCLUDED.doctor_name,
    diagnosis_codes = EXCLUDED.diagnosis_codes,
    has_followup    = EXCLUDED.has_followup,
    updated_at      = NOW();
"""

_SEARCH_SQL = """
SELECT
    id,
    patient_id,
    document,
    patient_name,
    visit_date,
    department,
    doctor_name,
    diagnosis_codes,
    has_followup,
    1 - (embedding <=> %s::vector) AS score
FROM analytics.clinical_embeddings
ORDER BY embedding <=> %s::vector
LIMIT %s;
"""

_COUNT_SQL = "SELECT COUNT(*) FROM analytics.clinical_embeddings;"

_DELETE_SQL = "DELETE FROM analytics.clinical_embeddings;"


class PgVectorStore(VectorStore):
    """Vector store backed by pgvector in PostgreSQL."""

    def __init__(self, database_url: str) -> None:
        """
        Initialize the PgVectorStore.

        Creates the clinical_embeddings table and HNSW index if they
        don't exist. Safe to call multiple times (idempotent).

        Args:
            database_url: PostgreSQL connection string (same as PMS DATABASE_URL).
        """
        self._database_url = database_url
        self._setup()

    def _get_conn(self):
        """
        Get a new psycopg2 connection with pgvector types registered.

        We create a new connection per operation rather than a persistent
        connection pool to avoid issues with Render's connection limits
        on the free tier. For production, use a connection pool.
        """
        conn = psycopg2.connect(self._database_url)
        register_vector(conn)
        return conn

    def _setup(self) -> None:
        """
        Create extension, table, and index if they don't exist.
        Called once on initialization.
        """
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(_SETUP_SQL)
            conn.commit()
        finally:
            conn.close()

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        """
        Insert or update vectors with metadata. Idempotent.

        Args:
            ids: Chunk IDs e.g. "42_visit_1"
            embeddings: 512-dim vectors from VoyageProvider
            documents: Raw chunk text
            metadatas: Dicts with patient_id, visit_date, department, etc.
        """
        rows = []
        for i, chunk_id in enumerate(ids):
            meta = metadatas[i]
            rows.append((
                chunk_id,
                meta.get('patient_id'),
                documents[i],
                embeddings[i],
                meta.get('patient_name'),
                meta.get('visit_date'),
                meta.get('department'),
                meta.get('doctor_name'),
                meta.get('diagnosis_codes'),
                meta.get('has_followup', False),
            ))

        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                psycopg2.extras.execute_batch(cur, _UPSERT_SQL, rows, page_size=100)
            conn.commit()
        finally:
            conn.close()

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        """
        Find the top_k most similar chunks using cosine similarity.

        The <=> operator computes cosine distance (0 = identical, 2 = opposite).
        We return 1 - distance as the score so higher = more similar.

        Note: filters param is accepted for interface compatibility but not
        yet implemented at the SQL level. Add WHERE clauses here if needed.

        Args:
            query_embedding: 512-dim query vector from VoyageProvider
            top_k: Number of results to return
            filters: Optional metadata filters (not yet implemented)

        Returns:
            List of dicts with keys: document, metadata, score
        """
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(_SEARCH_SQL, (query_embedding, query_embedding, top_k))
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

    def count(self) -> int:
        """Return total number of stored vectors."""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(_COUNT_SQL)
                return cur.fetchone()[0]
        finally:
            conn.close()

    def delete_collection(self) -> None:
        """Delete all stored vectors. Used before full re-ingestion."""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(_DELETE_SQL)
            conn.commit()
        finally:
            conn.close()