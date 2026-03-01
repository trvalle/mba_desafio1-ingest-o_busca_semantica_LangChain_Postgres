"""
Módulo de Configuração Centralizada — Saúde de Exames de Sangue

Concentra todas as constantes e configurações do projeto em um único lugar.
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# --- Configurações de API ---
GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")

# --- Configurações de LLM ---
LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))

# --- Configurações de Retry ---
MAX_RETRY_ATTEMPTS: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
RETRY_DELAY_SECONDS: int = int(os.getenv("RETRY_DELAY_SECONDS", "30"))

# --- Prompt de Análise da IA ---
ANALYSIS_PROMPT_TEMPLATE: str = """Você é um assistente de saúde especializado em interpretação de exames laboratoriais.
Analise os resultados abaixo e forneça:

1. **Resumo Geral**: Estado geral de saúde com base nos exames.
2. **Parâmetros Alterados**: Explique cada valor fora da faixa e seu significado clínico.
3. **Pontos de Atenção**: Destaque valores críticos ou correlações importantes entre parâmetros.
4. **Recomendações**: Sugira acompanhamento médico e mudanças de estilo de vida quando pertinente.

⚠️ IMPORTANTE: Esta análise é educacional e informativa. Não substitui a consulta médica.
O resultado deve ser apresentado sempre em português brasileiro.

Resultados do Exame:
{resultados}

Análise:"""


def validate_config() -> bool:
    """Valida se as configurações críticas estão presentes."""
    if not GOOGLE_API_KEY:
        print("❌ Erro: GOOGLE_API_KEY não configurada no arquivo .env")
        return False
    return True
