"""
Script de Diagnóstico de Modelos

Este script se conecta diretamente à API do Google Generative AI para listar
todos os modelos disponíveis para a chave de API configurada no arquivo .env.

Ele filtra a lista para mostrar apenas os modelos que suportam o método
'embedContent', que é o que precisamos para a nossa aplicação.

A saída deste script nos dirá exatamente quais modelos de embedding
podemos usar.

Para executar:
    .venv/Scripts/python.exe check_models.py
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Configura a API key
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi encontrada no seu arquivo .env.")
    
    genai.configure(api_key=api_key)
    print("API Key configurada com sucesso.")

except Exception as e:
    print(f"Ocorreu um erro ao configurar a API Key: {e}")
    exit()

# Lista os modelos
print("\nBuscando modelos de embedding disponíveis para sua API Key...")
print("-" * 60)

found_models = []
try:
    for model in genai.list_models():
        if 'embedContent' in model.supported_generation_methods:
            found_models.append(model.name)

except Exception as e:
    print(f"Ocorreu um erro ao tentar listar os modelos: {e}")
    print("Isso pode indicar um problema com a chave de API ou com as permissões da sua conta Google Cloud.")
    exit()

# Exibe os resultados
if found_models:
    print("Modelos de embedding ('embedContent') encontrados:")
    for model_name in found_models:
        print(f"  - {model_name}")
else:
    print("Nenhum modelo de embedding foi encontrado para a sua chave de API.")
    # Usando aspas triplas para evitar erros de sintaxe com aspas simples/duplas internas.
    print("""Por favor, verifique se a 'Generative Language API' está ativa 
no seu projeto Google Cloud associado a esta chave.""")

print("-" * 60)
