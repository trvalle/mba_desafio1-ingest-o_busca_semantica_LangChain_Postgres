"""
Aplicação Principal — Análise de Saúde por Exames de Sangue

Interface de linha de comando (CLI) para análise de exames laboratoriais
com interpretação assistida por Inteligência Artificial (Google Gemini).

Uso:
    # Análise a partir de arquivo JSON:
    python main.py --arquivo exame.json

    # Análise interativa (preenchimento manual):
    python main.py

    # Salvar relatório em arquivo:
    python main.py --arquivo exame.json --saida relatorio.txt
"""

import sys
import os
import argparse

# Garante que os módulos locais sejam encontrados
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

load_dotenv()


def parse_args() -> argparse.Namespace:
    """Faz o parsing dos argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="🩸 Análise de Exames de Sangue com IA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py
  python main.py --arquivo sample_exam.json
  python main.py --arquivo sample_exam.json --saida meu_relatorio.txt
        """,
    )
    parser.add_argument(
        "--arquivo", "-a",
        metavar="CAMINHO",
        help="Caminho para o arquivo JSON com os dados do exame",
    )
    parser.add_argument(
        "--saida", "-s",
        metavar="CAMINHO",
        help="Caminho para salvar o relatório em .txt (opcional)",
    )
    return parser.parse_args()


def main() -> None:
    """Ponto de entrada principal da aplicação."""
    from config import validate_config
    from analyzer import AnalisadorExame
    from report import gerar_relatorio, salvar_relatorio

    print("\n🩸 Sistema de Análise de Exames de Sangue com IA")
    print("=" * 50)

    if not validate_config():
        print("\n💡 Dica: Configure a variável GOOGLE_API_KEY no arquivo .env")
        print("         A análise básica (sem IA) continuará disponível.\n")

    args = parse_args()
    analisador = AnalisadorExame()

    # Carrega o resultado do exame
    if args.arquivo:
        if not os.path.exists(args.arquivo):
            print(f"❌ Arquivo não encontrado: {args.arquivo}")
            sys.exit(1)
        print(f"\n📂 Carregando exame de: {args.arquivo}")
        resultado = analisador.carregar_de_json(args.arquivo)
    else:
        resultado = analisador.carregar_interativo()

    if not resultado.parametros:
        print("❌ Nenhum parâmetro foi informado. Encerrando.")
        sys.exit(0)

    # Executa a análise
    print(f"\n🔍 Analisando {len(resultado.parametros)} parâmetros...")
    analise = analisador.analisar(resultado)

    # Gera e exibe o relatório
    relatorio = gerar_relatorio(resultado, analise)
    print("\n" + relatorio)

    # Salva o relatório, se solicitado
    if args.saida:
        salvar_relatorio(relatorio, args.saida)


if __name__ == "__main__":
    main()
