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

---

## 🩸 Saúde Track — Aplicativo de Exames de Sangue (PWA)

Um novo módulo foi adicionado ao repositório: um aplicativo **mobile-first** para organizar exames de sangue e acompanhar a evolução da saúde ao longo do tempo. Funciona como **PWA (Progressive Web App)** — pode ser instalado no Android e iPhone diretamente pelo navegador, sem precisar de app store.

### ✨ Funcionalidades

- **📋 Organização de Exames**: Registre exames por data e laboratório com biomarcadores e valores de referência.
- **📊 Gráficos de Evolução**: Visualize a evolução de cada biomarcador ao longo do tempo com linhas de referência (mín/máx).
- **📈 Análise de Impacto**: Tendências automáticas a **curto prazo (3 meses)**, **médio prazo (12 meses)** e **longo prazo (histórico completo)**.
- **🚨 Alertas Inteligentes**: Indicadores visuais de status (Normal 🟢 / Atenção 🟡 / Crítico 🔴) baseados nos valores de referência.
- **🏥 20 Biomarcadores Pré-configurados**: Glicose, Colesterol Total, HDL, LDL, Triglicerídeos, Hemoglobina, TSH, Vitamina D, e muito mais.
- **📱 Compatível com Android e iPhone**: Interface mobile-first instalável como PWA.

### 🚀 Como executar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Inicie o servidor:
   ```bash
   uvicorn blood_tests_app:app --host 0.0.0.0 --port 8080
   ```

3. Acesse no navegador do celular:
   ```
   http://<seu-ip>:8080
   ```

4. Para instalar como app no celular: toque em **"Adicionar à tela inicial"** no menu do navegador.

### 📱 Como instalar como App no celular

**Android (Chrome):**
1. Abra o endereço no Chrome
2. Toque nos três pontos (⋮) no canto superior direito
3. Selecione "Adicionar à tela inicial"

**iPhone (Safari):**
1. Abra o endereço no Safari
2. Toque no ícone de compartilhamento (□↑)
3. Selecione "Adicionar à Tela de Início"

### 🛠️ Tecnologias do Módulo

| Componente | Tecnologia |
|---|---|
| Backend | FastAPI + Python |
| Banco de Dados | SQLite (sem configuração extra) |
| Gráficos | Canvas 2D API (sem dependências externas) |
| Frontend | HTML5 + CSS3 + JavaScript puro |
| Instalação Mobile | PWA (Progressive Web App) |

### 📡 API REST

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/exames` | Lista todos os exames |
| `POST` | `/api/exames` | Cria novo exame |
| `GET` | `/api/exames/{id}` | Detalhe de um exame |
| `DELETE` | `/api/exames/{id}` | Remove um exame |
| `GET` | `/api/evolucao` | Série temporal por biomarcador |
| `GET` | `/api/analise_impacto` | Análise curto/médio/longo prazo |

Documentação interativa disponível em: `http://localhost:8080/docs`

