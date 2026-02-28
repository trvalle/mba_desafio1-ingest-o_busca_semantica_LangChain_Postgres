"""
Módulo de Configuração Centralizada

Concentra todas as constantes e configurações do projeto em um único lugar,
facilitando manutenção e reutilização em diferentes módulos.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# --- Configurações de Banco de Dados ---
DB_USER: str = os.getenv("DB_USER", "postgres")
DB_PASS: str = os.getenv("DB_PASS", "postgres")
DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: str = os.getenv("DB_PORT", "5432")
DB_NAME: str = os.getenv("DB_NAME", "agroscholar_db")

# --- Configurações de API ---
GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL") or os.getenv("DB_URL")

# --- Configurações de LLM ---
EMBEDDING_MODEL: str = "models/gemini-embedding-001"
EMBEDDING_TASK_TYPE: str = "retrieval_document"
LLM_MODEL: str = "gemini-3-flash-preview"
LLM_TEMPERATURE: float = 0.2
LLM_MAX_TOKENS: int = 1024

# --- Configurações de Ingestão ---
COLLECTION_NAME: str = "agro_docs_collection"
CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 500  # Aumentado para melhor preservação de contexto

# --- Configurações de Query Expansion ---
QUERY_EXPANSION_ENABLED: bool = True
QUERY_EXPANSION_VARIANTS: int = 3  # Número de variações da pergunta

# --- Configurações de Tabelas ---
EXTRACT_TABLES_SEPARATELY: bool = True
TABLE_DESCRIPTION_PREFIX: str = "[TABELA] "

# --- Configurações de SQLAlchemy ---
DB_POOL_SIZE: int = 10
DB_MAX_OVERFLOW: int = 20

# --- Configurações de Retry ---
MAX_RETRY_ATTEMPTS: int = 3
RETRY_DELAY_SECONDS: int = 30

# --- Prompt Template ---
RAG_PROMPT_TEMPLATE: str = """Você é um assistente técnico especializado do MBA. 
Use o contexto abaixo para responder à pergunta. Se não encontrar a resposta, 
diga claramente que a informação não consta no documento.

Contexto: {context}
Pergunta: {question}
Resposta:"""

# --- Validação de Configurações Críticas ---
def validate_critical_config() -> bool:
    """Valida se as configurações críticas estão presentes."""
    if not GOOGLE_API_KEY:
        print("❌ Erro: GOOGLE_API_KEY não está configurada no .env")
        return False
    if not DATABASE_URL:
        print("❌ Erro: DATABASE_URL não está configurada no .env")
        return False
    return True
