"""
Módulo de Geração de Relatórios de Exames de Sangue

Gera relatórios formatados em texto (terminal) e opcionalmente em arquivo .txt.
"""

from datetime import datetime
from models import ResultadoExame, Status


ICONES_STATUS = {
    Status.NORMAL: "✅",
    Status.BAIXO: "⬇️ ",
    Status.ALTO: "⬆️ ",
    Status.CRITICO_BAIXO: "🚨",
    Status.CRITICO_ALTO: "🚨",
}


def gerar_relatorio(resultado: ResultadoExame, analise_ia: str) -> str:
    """
    Gera o relatório completo do exame de sangue.

    Args:
        resultado: ResultadoExame com os dados do paciente e parâmetros
        analise_ia: Texto de análise gerado pela IA

    Returns:
        String com o relatório formatado
    """
    largura = 60
    linha = "=" * largura
    linha_simples = "-" * largura

    secoes = [
        linha,
        "        🩸 RELATÓRIO DE EXAME DE SANGUE",
        linha,
        f"  Paciente   : {resultado.paciente}",
        f"  Coleta     : {resultado.data_coleta}",
        f"  Gerado em  : {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        linha,
        "",
        "📊 RESULTADOS POR PARÂMETRO",
        linha_simples,
    ]

    # Tabela de parâmetros
    for p in resultado.parametros:
        icone = ICONES_STATUS.get(p.status, "  ")
        secoes.append(
            f"{icone} {p.nome:<35} {p.valor:>8.2f} {p.referencia.unidade:<8} "
            f"[{p.referencia.minimo}–{p.referencia.maximo}]"
        )

    # Resumo de parâmetros alterados
    alterados = resultado.parametros_alterados
    criticos = resultado.parametros_criticos
    total = len(resultado.parametros)
    normais = total - len(alterados)

    secoes += [
        "",
        linha_simples,
        f"  Total analisado : {total} parâmetros",
        f"  ✅ Normais       : {normais}",
        f"  ⚠️  Alterados    : {len(alterados)}",
        f"  🚨 Críticos      : {len(criticos)}",
    ]

    if resultado.observacoes:
        secoes += [
            "",
            f"  📝 Obs: {resultado.observacoes}",
        ]

    # Análise da IA
    secoes += [
        "",
        linha,
        "🤖 ANÁLISE POR INTELIGÊNCIA ARTIFICIAL",
        linha,
        "",
        analise_ia,
        "",
        linha,
        "⚠️  AVISO: Este relatório é de caráter informativo e educacional.",
        "    Não substitui avaliação, diagnóstico ou tratamento médico.",
        linha,
    ]

    return "\n".join(secoes)


def salvar_relatorio(relatorio: str, caminho: str) -> None:
    """
    Salva o relatório em um arquivo de texto.

    Args:
        relatorio: String com o conteúdo do relatório
        caminho: Caminho do arquivo de saída
    """
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(relatorio)
    print(f"✅ Relatório salvo em: {caminho}")
