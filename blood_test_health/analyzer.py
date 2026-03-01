"""
Módulo de Análise de Exames de Sangue

Responsável por:
- Carregar dados de exame a partir de JSON ou entrada interativa
- Comparar valores com as faixas de referência
- Enviar resultados para o LLM para interpretação clínica
"""

import json
from typing import Optional

from models import (
    Parametro, ResultadoExame, ValorReferencia,
    REFERENCIAS_PADRAO, DESCRICOES_PARAMETROS, Status
)
from config import (
    GOOGLE_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    ANALYSIS_PROMPT_TEMPLATE, MAX_RETRY_ATTEMPTS, RETRY_DELAY_SECONDS
)


class AnalisadorExame:
    """
    Analisa resultados de exames de sangue e gera interpretação por IA.
    """

    def __init__(self):
        """Inicializa o analisador com o modelo de linguagem."""
        try:
            import time
            self._time = time
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser

            self.llm = ChatGoogleGenerativeAI(
                model=LLM_MODEL,
                google_api_key=GOOGLE_API_KEY,
                temperature=LLM_TEMPERATURE,
                max_output_tokens=LLM_MAX_TOKENS,
            )
            self.prompt = ChatPromptTemplate.from_template(ANALYSIS_PROMPT_TEMPLATE)
            self.chain = self.prompt | self.llm | StrOutputParser()
            self._ia_disponivel = True

        except Exception as e:
            print(f"⚠️  IA não disponível: {e}")
            self._ia_disponivel = False

    def carregar_de_json(self, caminho: str) -> ResultadoExame:
        """
        Carrega um resultado de exame a partir de um arquivo JSON.

        Estrutura esperada do JSON:
        {
            "paciente": "Nome",
            "data_coleta": "DD/MM/AAAA",
            "sexo": "M" ou "F",
            "observacoes": "...",
            "parametros": {
                "glicose_jejum": 95.0,
                "colesterol_total": 210.0,
                ...
            }
        }

        Args:
            caminho: Caminho para o arquivo JSON

        Returns:
            ResultadoExame populado com os parâmetros
        """
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)

        return self._construir_resultado(dados)

    def carregar_interativo(self) -> ResultadoExame:
        """
        Guia o usuário no preenchimento interativo dos dados do exame via CLI.

        Returns:
            ResultadoExame populado com os parâmetros informados
        """
        print("\n" + "=" * 50)
        print("📋 CADASTRO DE EXAME DE SANGUE")
        print("=" * 50)
        paciente = input("Nome do paciente: ").strip() or "Não informado"
        data = input("Data da coleta (DD/MM/AAAA): ").strip() or "Não informada"
        sexo = input("Sexo (M/F): ").strip().upper()
        obs = input("Observações (opcional): ").strip()

        dados = {
            "paciente": paciente,
            "data_coleta": data,
            "sexo": sexo,
            "observacoes": obs,
            "parametros": {},
        }

        print("\nInforme os valores dos exames (pressione Enter para pular):")
        parametros_disponiveis = self._obter_parametros_por_sexo(sexo)

        for chave, ref in parametros_disponiveis.items():
            nome_exibicao = chave.replace("_masculino", "").replace("_feminino", "").replace("_", " ").title()
            entrada = input(f"  {nome_exibicao} ({ref.unidade}): ").strip()
            if entrada:
                try:
                    dados["parametros"][chave] = float(entrada.replace(",", "."))
                except ValueError:
                    print(f"  ⚠️  Valor inválido para {nome_exibicao}, ignorado.")

        return self._construir_resultado(dados)

    def _obter_parametros_por_sexo(self, sexo: str) -> dict:
        """Retorna o dicionário de referências filtrado para o sexo informado."""
        resultado = {}
        for chave, ref in REFERENCIAS_PADRAO.items():
            if "_masculino" in chave and sexo == "F":
                continue
            if "_feminino" in chave and sexo == "M":
                continue
            resultado[chave] = ref
        return resultado

    def _construir_resultado(self, dados: dict) -> ResultadoExame:
        """
        Constrói um ResultadoExame a partir de um dicionário de dados.

        Args:
            dados: Dicionário com dados do paciente e parâmetros

        Returns:
            ResultadoExame populado
        """
        sexo = dados.get("sexo", "").upper()
        resultado = ResultadoExame(
            paciente=dados.get("paciente", "Não informado"),
            data_coleta=dados.get("data_coleta", "Não informada"),
            observacoes=dados.get("observacoes", ""),
        )

        for chave, valor in dados.get("parametros", {}).items():
            # Resolve a chave de referência considerando variantes por sexo
            chave_ref = self._resolver_chave_referencia(chave, sexo)
            if chave_ref not in REFERENCIAS_PADRAO:
                print(f"  ⚠️  Parâmetro desconhecido ignorado: {chave}")
                continue

            ref = REFERENCIAS_PADRAO[chave_ref]
            nome_exibicao = chave.replace("_masculino", "").replace("_feminino", "").replace("_", " ").title()
            chave_desc = chave.replace("_masculino", "").replace("_feminino", "")
            descricao = DESCRICOES_PARAMETROS.get(chave_desc, "")

            parametro = Parametro(
                nome=nome_exibicao,
                valor=float(valor),
                referencia=ref,
                descricao=descricao,
            )
            resultado.adicionar_parametro(parametro)

        return resultado

    def _resolver_chave_referencia(self, chave: str, sexo: str) -> str:
        """
        Resolve a chave de referência considerando variantes por sexo.
        Exemplo: 'hemoglobina' + sexo 'M' → 'hemoglobina_masculino'
        """
        if chave in REFERENCIAS_PADRAO:
            return chave
        sufixo = "_masculino" if sexo == "M" else "_feminino"
        candidata = chave + sufixo
        if candidata in REFERENCIAS_PADRAO:
            return candidata
        return chave

    def analisar(self, resultado: ResultadoExame) -> str:
        """
        Executa a análise completa: verifica referências e gera interpretação por IA.

        Args:
            resultado: ResultadoExame a ser analisado

        Returns:
            String com a análise gerada pela IA ou análise básica se IA indisponível
        """
        resumo = resultado.resumo_para_ia()

        if not self._ia_disponivel:
            return self._analise_basica(resultado)

        for tentativa in range(MAX_RETRY_ATTEMPTS):
            try:
                analise = self.chain.invoke({"resultados": resumo})
                return analise
            except Exception as e:
                erro = str(e)
                if "429" in erro or "RESOURCE_EXHAUSTED" in erro:
                    if tentativa < MAX_RETRY_ATTEMPTS - 1:
                        print(f"⏳ Cota da API atingida. Aguardando {RETRY_DELAY_SECONDS}s ({tentativa + 1}/{MAX_RETRY_ATTEMPTS})...")
                        self._time.sleep(RETRY_DELAY_SECONDS)
                        continue
                print(f"⚠️  Erro na análise por IA: {e}")
                return self._analise_basica(resultado)

        return self._analise_basica(resultado)

    def _analise_basica(self, resultado: ResultadoExame) -> str:
        """
        Gera uma análise textual básica sem uso de IA, útil como fallback.

        Args:
            resultado: ResultadoExame a ser analisado

        Returns:
            Análise textual básica baseada nas faixas de referência
        """
        linhas = ["=== ANÁLISE BÁSICA (sem IA) ===", ""]
        criticos = resultado.parametros_criticos
        alterados = resultado.parametros_alterados

        if criticos:
            linhas.append("🚨 VALORES CRÍTICOS — BUSQUE ATENÇÃO MÉDICA IMEDIATA:")
            for p in criticos:
                linhas.append(f"  • {p.nome}: {p.valor} {p.referencia.unidade} ({p.status.value})")
            linhas.append("")

        if alterados:
            linhas.append("⚠️  PARÂMETROS FORA DA FAIXA DE REFERÊNCIA:")
            for p in alterados:
                linhas.append(
                    f"  • {p.nome}: {p.valor} {p.referencia.unidade} "
                    f"(Ref: {p.referencia.minimo}–{p.referencia.maximo}) — {p.status.value}"
                )
        else:
            linhas.append("✅ Todos os parâmetros analisados estão dentro das faixas de referência.")

        linhas += [
            "",
            "⚠️  Esta análise é informativa e não substitui a consulta com um profissional de saúde.",
        ]
        return "\n".join(linhas)
