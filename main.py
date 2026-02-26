import os
import sys
import time
from dotenv import load_dotenv

# 1. Carregamento das variáveis de ambiente
load_dotenv()

def main():
    # Inicialização preventiva para evitar erro de 'not defined'
    rag_chain = None
    
    api_key = os.getenv("GOOGLE_API_KEY")
    # Usando DATABASE_URL conforme seu .env ou o padrão do docker
    db_url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
    
    if not api_key or not db_url:
        print("❌ Erro: Verifique as variáveis GOOGLE_API_KEY e DATABASE_URL no seu .env")
        return

    # 2. Imports internos para otimização
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
        from langchain_community.vectorstores import PGVector
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.runnables import RunnablePassthrough
        from langchain_core.output_parsers import StrOutputParser

        print("✅ Bibliotecas carregadas. Configurando IA...")

         # 3. Configuração dos Modelos (Ajustados para o seu ambiente)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-001")
        
        embeddings= GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001",
                task_type="retrieval_document",
        )
        
        # Conexão com o Vector Store
        vector_store = PGVector(
            connection_string=db_url,
            embedding_function=embeddings,
            collection_name="agro_docs_collection",
        )
        
        # Retriever configurado para buscar os 3 trechos mais relevantes
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        
        # No local onde você define o LLM, mude para:
        llm = ChatGoogleGenerativeAI(
            model="gemini-3-flash-preview", # Nome exato e estável
            google_api_key=api_key, 
            temperature=0.2,
            max_output_tokens=1024 # Boa prática para economizar cota e evitar truncamento
        )

        # Template de Prompt
        template = """Você é um assistente técnico especializado do MBA. 
        Use o contexto abaixo para responder à pergunta. Se não encontrar a resposta, 
        diga claramente que a informação não consta no documento.

        Contexto: {context}
        Pergunta: {question}
        Resposta:"""
        
        prompt = ChatPromptTemplate.from_template(template)

        # Construção da Chain (LCEL)
        rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

    except Exception as e:
        print(f"❌ Erro crítico na inicialização: {e}")
        return

    # 3. Interface de Chat (CLI)
    if rag_chain:
        print("\n" + "="*40)
        print("🤖 Assistente RAG MBA-AI (gemini-3-flash-preview)")
        print("Digite 'sair' para encerrar a sessão.")
        print("="*40 + "\n")

        while True:
            try:
                user_query = input("Sua pergunta: ").strip()
                
                if not user_query:
                    continue
                
                if user_query.lower() in ["sair", "exit", "quit"]:
                    print("Encerrando assistente... Até logo!")
                    break
                
                # Implementação de Retry para gerenciar cotas (429)
                for tentativa in range(3):
                    try:
                        response = rag_chain.invoke(user_query)
                        print(f"\n💡 Resposta: {response}\n")
                        print("-" * 20)
                        break # Sucesso, sai do loop de tentativas
                        
                    except Exception as e:
                        error_msg = str(e)
                        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                            if tentativa < 2:
                                print(f"⏳ Cota atingida. Aguardando 30s para tentar novamente ({tentativa + 1}/3)...")
                                time.sleep(30)
                                continue
                        # Se for outro erro ou esgotar tentativas, exibe o erro
                        print(f"⚠️ Erro na geração: {e}")
                        break

            except KeyboardInterrupt:
                print("\nInterrompido pelo usuário. Saindo...")
                break
            except Exception as e:
                print(f"\n⚠️ Ocorreu um erro inesperado: {e}")
                continue
    else:
        print("❌ Falha: A estrutura de busca (rag_chain) não foi inicializada.")

if __name__ == "__main__":
    main()