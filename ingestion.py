"""
Módulo de Ingestão de Documentos

Este script é responsável por processar um arquivo PDF, extrair seu texto,
dividi-lo em segmentos (chunks), gerar embeddings vetoriais para cada segmento
e armazená-los em um banco de dados PostgreSQL com a extensão pgvector.
"""

import os
import sys
from typing import List

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores.pgvector import PGVector
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy.engine import Engine

from database import get_db_connection, DATABASE_URL

# Carrega variáveis de ambiente
load_dotenv()

# --- Constantes de Configuração ---
COLLECTION_NAME: str = "agro_docs_collection"
CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 200

if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi definida.")

class DocumentIngestor:
    def __init__(self, db_engine: Engine, db_connection_string: str):
        self.db_engine = db_engine
        self.connection_string = db_connection_string
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )
        self.embeddings_model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            task_type="retrieval_document",
        )

    def ingest_pdf(self, pdf_path: str) -> None:
        if not os.path.exists(pdf_path):
            print(f"Erro: O arquivo '{pdf_path}' não foi encontrado.")
            return

        print(f"Iniciando a ingestão do arquivo: {pdf_path}")

        # 1. Carregar o documento
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        print(f"PDF carregado. {len(documents)} página(s) encontradas.")

        # 2. Dividir o texto em chunks
        text_chunks = self.text_splitter.split_documents(documents)
        
        # --- CORREÇÃO AQUI: Sanitização de caracteres NUL ---
        # Remove caracteres \x00 que o PostgreSQL não aceita em strings literais
        for chunk in text_chunks:
            chunk.page_content = chunk.page_content.replace('\x00', '')
        
        print(f"Texto dividido e sanitizado em {len(text_chunks)} chunks.")

        # 3. Gerar e armazenar os embeddings
        print("Gerando e armazenando embeddings no PGVector...")
        try:
            PGVector.from_documents(
                documents=text_chunks,
                embedding=self.embeddings_model,
                collection_name=COLLECTION_NAME,
                connection_string=self.connection_string,
                pre_delete_collection=False,
            )
            print("Embeddings armazenados com sucesso!")
        except Exception as e:
            print(f"Erro no armazenamento: {e}")
            raise

def main():
    if len(sys.argv) < 2:
        print("Uso: python ingestion.py <caminho_para_o_pdf>")
        sys.exit(1)

    pdf_file_path = sys.argv[1]

    try:
        db_engine = get_db_connection()
        ingestor = DocumentIngestor(
            db_engine=db_engine, db_connection_string=DATABASE_URL
        )
        ingestor.ingest_pdf(pdf_file_path)
        print("Processo de ingestão concluído.")
    except Exception as e:
        print(f"Ocorreu uma falha crítica durante a ingestão: {e}")
        print("Verifique a conexão com o banco e a chave de API.")

if __name__ == "__main__":
    main()