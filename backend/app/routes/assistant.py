# app/routes/assistant.py
"""
Flask blueprint for the Clinical AI Assistant API.

Endpoints:
    POST /api/v1/assistant/query   — submit a clinical query
    POST /api/v1/assistant/ingest  — trigger re-ingestion (admin only)
    GET  /api/v1/assistant/status  — ingestion status and model info
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.utils.decorators import role_required
from app.utils.helpers import error_response, success_response

assistant_bp = Blueprint('assistant', __name__)


@assistant_bp.route('/query', methods=['POST'])
@jwt_required()
@role_required(['admin', 'doctor'])
def query_assistant():
    """
    Submit a natural language clinical query.

    POST /api/v1/assistant/query
    Body: { "query": "show me cardiac patients who missed follow-ups" }
    Auth: admin, doctor

    Auto-ingests if vector store is empty (handles Render cold starts).
    """
    from rag.assistant import ask
    from rag.ingestion import ingest_clinical_summaries
    from rag.providers.pgvector_store import PgVectorStore
    from rag.config import RENDER_DATABASE_URL, DATABASE_URL
    import os

    data = request.get_json()
    if not data:
        return error_response('Request body is required', 400)

    query = data.get('query', '').strip()
    if not query:
        return error_response('Query is required', 400)

    if len(query) > 500:
        return error_response('Query too long (max 500 characters)', 400)

    # Auto-ingest if vector store is empty
    try:
        render_url = os.getenv('RENDER_DATABASE_URL') or os.getenv('DATABASE_URL')
        store = PgVectorStore(database_url=render_url)
        if store.count() == 0:
            from app.extensions import db
            ingest_clinical_summaries(db=db)
    except Exception as e:
        return error_response(f'Vector store unavailable: {str(e)}', 503)

    try:
        result = ask(query)
        return success_response(result, 200)
    except Exception as e:
        return error_response(f'Query failed: {str(e)}', 500)


@assistant_bp.route('/ingest', methods=['POST'])
@jwt_required()
@role_required(['admin'])
def trigger_ingestion():
    """
    Trigger re-ingestion of clinical summaries into vector store.

    POST /api/v1/assistant/ingest
    Auth: admin only

    Re-embeds all patient summaries. Safe to run multiple times (idempotent).
    Takes 2-3 minutes for 7,631 patients.
    """
    from rag.ingestion import ingest_clinical_summaries
    from app.extensions import db

    try:
        stats = ingest_clinical_summaries(db=db)
        return success_response({
            'message': 'Ingestion complete',
            **stats,
        }, 200)
    except Exception as e:
        return error_response(f'Ingestion failed: {str(e)}', 500)


@assistant_bp.route('/status', methods=['GET'])
@jwt_required()
@role_required(['admin'])
def assistant_status():
    """
    Get vector store status and model configuration.

    GET /api/v1/assistant/status
    Auth: admin only
    """
    from rag.providers.pgvector_store import PgVectorStore
    from rag.config import (
        VOYAGE_MODEL, CLAUDE_MODEL, EMBEDDING_DIMENSION,
    )
    import os

    try:
        render_url = os.getenv('RENDER_DATABASE_URL') or os.getenv('DATABASE_URL')
        store = PgVectorStore(database_url=render_url)
        total_chunks = store.count()

        # Get last ingested timestamp
        import psycopg2
        conn = psycopg2.connect(render_url)
        with conn.cursor() as cur:
            cur.execute('SELECT MAX(updated_at) FROM analytics.clinical_embeddings')
            last_ingested = cur.fetchone()[0]
        conn.close()

        return success_response({
            'total_chunks': total_chunks,
            'embedding_model': VOYAGE_MODEL,
            'embedding_dimension': EMBEDDING_DIMENSION,
            'llm_model': CLAUDE_MODEL,
            'vector_store': 'pgvector',
            'last_ingested': last_ingested.isoformat() if last_ingested else None,
            'ready': total_chunks > 0,
        }, 200)
    except Exception as e:
        return error_response(f'Status check failed: {str(e)}', 500)