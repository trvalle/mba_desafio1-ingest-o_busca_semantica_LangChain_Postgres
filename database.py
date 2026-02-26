"""
Módulo de Configuração do Banco de Dados

Implementa o padrão Singleton para gerenciamento de conexões SQLAlchemy.
Garante a inicialização da extensão 'vector' e fornece a engine para a aplicação.

Para executar este módulo de forma independente e verificar a infraestrutura:
    python database.py
"""
import os
import time
from typing import Optional
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class DatabaseSingleton:
    """
    Gerenciador de conexão com o banco de dados usando o padrão Singleton.
    """
    _instance: Optional['DatabaseSingleton'] = None
    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseSingleton, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Inicializa a engine e verifica a extensão vector."""
        self.db_user = os.getenv("DB_USER", "postgres")
        self.db_pass = os.getenv("DB_PASS", "postgres")
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME", "agroscholar_db")

        if not all([self.db_user, self.db_pass, self.db_host, self.db_port, self.db_name]):
            raise ValueError("Variáveis de ambiente de banco de dados incompletas.")

        self.database_url = f"postgresql+psycopg2://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

        try:
            self._engine = create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            )
            self._session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
            self._enable_vector_extension()
        except SQLAlchemyError as e:
            print(f"Erro crítico na inicialização do Singleton de Banco de Dados: {e}")
            raise

    def _enable_vector_extension(self) -> None:
        """Garante que a extensão vector existe com mecanismo de retry."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self._engine.connect() as connection:
                    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    connection.commit()
                print("Extensão 'vector' verificada/habilitada com sucesso.")
                return
            except OperationalError as e:
                print(f"Tentativa {attempt + 1}/{max_retries} falhou ao conectar ao DB: {e}")
                time.sleep(2)
        raise ConnectionError("Não foi possível conectar ao banco de dados após várias tentativas.")

    def get_engine(self) -> Engine:
        """Retorna a engine SQLAlchemy."""
        if self._engine is None:
            self._initialize()
        return self._engine

# Instância global
db_instance = DatabaseSingleton()
DATABASE_URL = db_instance.database_url

def get_db_connection() -> Engine:
    """
    Retorna uma instância da engine de conexão do SQLAlchemy.
    """
    return db_instance.get_engine()

# Bloco principal para permitir a execução direta do script
if __name__ == "__main__":
    print("Iniciando verificação da infraestrutura do banco de dados...")
    try:
        # A inicialização do Singleton já executa a verificação
        _ = get_db_connection()
        print("Validação da conexão e da extensão concluída com sucesso!")
    except Exception as e:
        print("Falha na verificação da infraestrutura.")
        print(f"Erro: {e}")
