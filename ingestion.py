"""
Módulo de Ingestão de Documentos

Este script é responsável por processar um arquivo PDF, extrair seu texto,
dividi-lo em segmentos (chunks), gerar embeddings vetoriais para cada segmento
e armazená-los em um banco de dados PostgreSQL com a extensão pgvector.

Uso:
    python ingestion.py <caminho_para_o_pdf>
"""

import os
import sys
import re
from typing import List, Dict

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores.pgvector import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from sqlalchemy.engine import Engine

from database import get_db_connection, DATABASE_URL
from config import (
    EMBEDDING_MODEL, EMBEDDING_TASK_TYPE, COLLECTION_NAME,
    CHUNK_SIZE, CHUNK_OVERLAP, GOOGLE_API_KEY, 
    EXTRACT_TABLES_SEPARATELY, TABLE_DESCRIPTION_PREFIX,
    validate_critical_config
)

# Carrega variáveis de ambiente
load_dotenv()


class DocumentIngestor:
    """
    Responsável pelo pipeline de ingestão de documentos PDF.
    
    Processa PDFs, divide em chunks, gera embeddings e armazena no vector store.
    Implementa detecção e processamento especial de tabelas para melhor recuperação.
    """
    
    def __init__(self, db_engine: Engine, db_connection_string: str):
        """
        Inicializa o ingestor com configurações de splitting e embeddings.
        
        Args:
            db_engine: Engine SQLAlchemy para conexão com o BD
            db_connection_string: String de conexão do banco de dados
        """
        self.db_engine = db_engine
        self.connection_string = db_connection_string
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        self.embeddings_model = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            task_type=EMBEDDING_TASK_TYPE,
        )

    def detect_tables(self, text: str) -> List[Dict[str, str]]:
        """
        Detecta possíveis tabelas no texto baseado em padrões estruturais.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Lista de dicionários contendo tabelas detectadas e sua descrição
        """
        if not EXTRACT_TABLES_SEPARATELY:
            return []
        
        tables = []
        # Padrões para detectar tabelas: múltiplas linhas com pipes ou espaçamento alinhado
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Detecta padrão de tabela markdown (|content|)
            if '|' in line and line.count('|') >= 2:
                table_lines = [line]
                # Coleta linhas adjacentes que parecem ser da tabela
                j = i + 1
                while j < len(lines) and ('|' in lines[j] or lines[j].strip() == ''):
                    table_lines.append(lines[j])
                    j += 1
                
                if len(table_lines) > 1:
                    table_text = '\n'.join(table_lines)
                    # Cria descrição contextual da tabela
                    description = f"{TABLE_DESCRIPTION_PREFIX}Tabela com {len(table_lines)} linhas. Conteúdo: {table_text[:200]}..."
                    tables.append({
                        'original': table_text,
                        'description': description
                    })
        
        return tables

    def enhance_chunks_with_tables(self, chunks: List) -> List:
        """
        Enriquece chunks com informações sobre tabelas detectadas.
        
        Args:
            chunks: Lista de chunks do LangChain
            
        Returns:
            Lista de chunks enriquecidos com metadados de tabelas
        """
        enhanced_chunks = []
        
        for chunk in chunks:
            tables = self.detect_tables(chunk.page_content)
            
            if tables:
                # Se contém tabelas, cria um chunk adicional com a descrição
                for table in tables:
                    enhanced_chunks.append(chunk)
                    # Cria um novo documento com a descrição da tabela
                    table_chunk = Document(
                        page_content=table['description'],
                        metadata={
                            **chunk.metadata,
                            'is_table_description': True,
                            'table_content': table['original']
                        }
                    )
                    enhanced_chunks.append(table_chunk)
            else:
                enhanced_chunks.append(chunk)
        
        return enhanced_chunks

    def ingest_pdf(self, pdf_path: str) -> None:
        """
        Executa o pipeline completo de ingestão de um PDF.
        
        Inclui:
            1. Carregamento do PDF
            2. Divisão em chunks com overlap aprimorado
            3. Detecção de tabelas e enriquecimento de metadados
            4. Sanitização de caracteres
            5. Geração e armazenamento de embeddings
        
        Args:
            pdf_path: Caminho do arquivo PDF a ser processado
        """
        if not os.path.exists(pdf_path):
            print(f"❌ Erro: O arquivo '{pdf_path}' não foi encontrado.")
            return

        print(f"📄 Iniciando a ingestão do arquivo: {pdf_path}")

        try:
            # 1. Carregar o documento
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            print(f"✅ PDF carregado. {len(documents)} página(s) encontradas.")

            # 2. Dividir o texto em chunks
            text_chunks = self.text_splitter.split_documents(documents)
            
            # 3. Enriquecer chunks com detecção de tabelas
            if EXTRACT_TABLES_SEPARATELY:
                text_chunks = self.enhance_chunks_with_tables(text_chunks)
                print(f"📊 Tabelas detectadas e enriquecidas nos chunks.")
            
            # 4. Sanitização de caracteres inválidos para PostgreSQL
            for chunk in text_chunks:
                chunk.page_content = chunk.page_content.replace('\x00', '')
            
            print(f"✂️  Texto dividido em {len(text_chunks)} chunks (com overlap de {CHUNK_OVERLAP}).")

            # 5. Gerar e armazenar os embeddings
            print("🔄 Gerando e armazenando embeddings no PGVector...")
            PGVector.from_documents(
                documents=text_chunks,
                embedding=self.embeddings_model,
                collection_name=COLLECTION_NAME,
                connection_string=self.connection_string,
                pre_delete_collection=False,
            )
            print("✅ Embeddings armazenados com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro no processamento: {e}")
            raise


def main():
    """Ponto de entrada para execução do script de ingestão."""
    if not validate_critical_config():
        sys.exit(1)
        
    if len(sys.argv) < 2:
        print("❌ Uso: python ingestion.py <caminho_para_o_pdf>")
        print("\n📝 Exemplo: python ingestion.py documentos/meu_arquivo.pdf")
        sys.exit(1)

    pdf_file_path = sys.argv[1]

    try:
        db_engine = get_db_connection()
        ingestor = DocumentIngestor(
            db_engine=db_engine,
            db_connection_string=DATABASE_URL
        )
        ingestor.ingest_pdf(pdf_file_path)
        print("\n✅ Processo de ingestão concluído com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Falha crítica durante a ingestão: {e}")
        print("Verifique a conexão com o banco e a chave de API.")
        sys.exit(1)


if __name__ == "__main__":
    main()
    main()