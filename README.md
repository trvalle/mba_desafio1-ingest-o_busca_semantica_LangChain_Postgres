Desafio Técnico: Ingestão e Busca Semântica com LangChain e Postgres
Este repositório contém o desenvolvimento de uma aplicação Python voltada para o processamento de documentos PDF, armazenamento vetorial e interface de chat via terminal (CLI) utilizando modelos de linguagem de larga escala (LLM).

📌 Contexto do Projeto
O projeto foi desenvolvido como parte de um Desafio Técnico para o curso de MBA em Engenharia de Software com IA. O objetivo principal é criar um fluxo completo de RAG (Retrieval-Augmented Generation), permitindo que um usuário interaja com o conteúdo de documentos PDF de forma semântica.

🚀 Funcionalidades
Leitura de PDF: Extração de texto de documentos de forma automatizada.

Vetorização e Armazenamento: Processamento dos dados e armazenamento em um banco de dados PostgreSQL com a extensão pgVector.

Busca Semântica: Recuperação de informações baseada no contexto e significado das palavras utilizando embeddings.

Interface CLI: Chat interativo via terminal para realização de perguntas e respostas com base nos documentos ingeridos.

🛠️ Tecnologias Utilizadas
Linguagem: Python

Orquestração de IA: LangChain

Banco de Dados: PostgreSQL com pgVector

Modelos de LLM: Gemini (Google) ou OpenAI

📋 Pré-requisitos
Para executar este projeto, você precisará de:

Python 3.10+ instalado.

Instância do PostgreSQL com suporte a pgvector.

Chave de API (API Key) para o modelo LLM escolhido (Gemini ou OpenAI).
