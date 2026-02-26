from langchain_community.vectorstores.pgvector import PGVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from database import DATABASE_URL

# Configuração igual ao seu ingestion
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vector_store = PGVector(
    connection_string=DATABASE_URL,
    embedding_function=embeddings,
    collection_name="agro_docs_collection",
)

# Teste de busca
query = "O que o PDF diz sobre a história da IA?"
docs = vector_store.similarity_search(query, k=2)

for i, doc in enumerate(docs):
    print(f"Trecho {i+1}: {doc.page_content[:200]}...")