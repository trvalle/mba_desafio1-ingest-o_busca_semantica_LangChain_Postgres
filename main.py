import os
import time
from dotenv import load_dotenv

# 1. Carregamento das variáveis de ambiente
load_dotenv()


def main():
    """
    Interface principal de chat para o assistente RAG.
    
    Inicializa os componentes de IA, configuradores de retriever e chain,
    e fornece um loop interativo para perguntas do usuário.
    """
    # Inicialização preventiva para evitar erro de 'not defined'
    rag_chain = None
    
    from config import (
        GOOGLE_API_KEY, DATABASE_URL, EMBEDDING_MODEL, EMBEDDING_TASK_TYPE,
        LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS, RAG_PROMPT_TEMPLATE,
        COLLECTION_NAME, MAX_RETRY_ATTEMPTS, RETRY_DELAY_SECONDS,
        QUERY_EXPANSION_ENABLED, QUERY_EXPANSION_VARIANTS,
        validate_critical_config
    )
    
    # Validar configurações críticas
    if not validate_critical_config():
        return

    # 2. Imports internos para otimização
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
        from langchain_community.vectorstores import PGVector
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.runnables import RunnablePassthrough
        from langchain_core.output_parsers import StrOutputParser

        print("✅ Bibliotecas carregadas. Configurando IA...")

        # 3. Configuração dos Modelos
        embeddings = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            task_type=EMBEDDING_TASK_TYPE,
        )
        
        # Conexão com o Vector Store
        vector_store = PGVector(
            connection_string=DATABASE_URL,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME,
        )
        
        # Retriever configurado para buscar os 5 trechos mais relevantes
        # (aumentado de 3 para melhor cobertura com query expansion)
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        
        # Configuração do LLM
        llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=LLM_TEMPERATURE,
            max_output_tokens=LLM_MAX_TOKENS
        )

        # Template de Prompt
        prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

        # Função de Query Expansion para melhor recuperação semântica
        def expand_query(query: str) -> str:
            """
            Expande a pergunta do usuário em múltiplas variações semânticas.
            Aumenta a chance de encontrar conteúdo tabelar e textual relevante.
            """
            if not QUERY_EXPANSION_ENABLED:
                return query
            
            expansion_prompt = f"""Você é um especialista em reformulação de perguntas.
            Dada a pergunta do usuário, gere {QUERY_EXPANSION_VARIANTS} variações semanticamente diferentes
            que buscam a mesma informação mas com termos e estruturas diferentes.
            
            Pergunta original: {query}
            
            Retorne APENAS as variações separadas por '|', sem numeração ou explicações.
            Exemplo: variação1 | variação2 | variação3"""
            
            try:
                expansions = llm.invoke(expansion_prompt)
                expanded_queries = [query] + [q.strip() for q in expansions.split('|') if q.strip()]
                return " ".join(expanded_queries[:QUERY_EXPANSION_VARIANTS + 1])
            except:
                # Se falhar na expansão, usa a query original
                return query

        # Retriever com Query Expansion
        def retrieve_with_expansion(query: str):
            """Recupera documentos usando query expansion."""
            expanded = expand_query(query)
            return retriever.invoke(expanded)

        # Construção da Chain (LCEL) com Query Expansion
        rag_chain = (
            {"context": lambda x: retrieve_with_expansion(x), "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

    except Exception as e:
        print(f"❌ Erro crítico na inicialização: {e}")
        return

    # 4. Interface de Chat (CLI)
    if rag_chain:
        print("\n" + "="*40)
        print(f"🤖 Assistente RAG MBA-AI ({LLM_MODEL})")
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
                for tentativa in range(MAX_RETRY_ATTEMPTS):
                    try:
                        response = rag_chain.invoke(user_query)
                        print(f"\n💡 Resposta: {response}\n")
                        print("-" * 20)
                        break  # Sucesso, sai do loop de tentativas
                        
                    except Exception as e:
                        error_msg = str(e)
                        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                            if tentativa < MAX_RETRY_ATTEMPTS - 1:
                                print(f"⏳ Cota atingida. Aguardando {RETRY_DELAY_SECONDS}s para tentar novamente ({tentativa + 1}/{MAX_RETRY_ATTEMPTS})...")
                                time.sleep(RETRY_DELAY_SECONDS)
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