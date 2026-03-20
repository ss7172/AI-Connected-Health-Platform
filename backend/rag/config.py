# rag/config.py
"""
Configuration for the RAG system.
All values read from environment variables with sensible defaults.
Swap providers by changing env vars — no code changes needed.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Provider selection ---
RAG_LLM_PROVIDER = os.getenv('RAG_LLM_PROVIDER', 'claude')        # claude | ollama (v2)
RAG_EMBEDDING_MODEL = os.getenv('RAG_EMBEDDING_MODEL', 'voyage-3-lite')
RAG_VECTOR_STORE = os.getenv('RAG_VECTOR_STORE', 'pgvector')       # pgvector | chromadb (v2)

# --- Anthropic (embeddings + LLM — same API key) ---
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-haiku-4-5')
VOYAGE_MODEL = os.getenv('VOYAGE_MODEL', 'voyage-3-lite')
EMBEDDING_DIMENSION = 512  # voyage-3-lite produces 1024-dim vectors
VOYAGE_API_KEY = os.getenv('VOYAGE_API_KEY')

# --- Database (same Postgres as PMS) ---
DATABASE_URL = os.getenv('DATABASE_URL')
RENDER_DATABASE_URL = os.getenv('RENDER_DATABASE_URL')

# --- Retrieval ---
TOP_K = int(os.getenv('RAG_TOP_K', '10'))
COLLECTION_NAME = 'clinical_summaries'  # logical name, used in pgvector table