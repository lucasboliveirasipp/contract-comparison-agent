import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
import logging

#load_dotenv()


class Config:
    # MongoDB
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    MONGODB_DB = os.getenv('MONGODB_DB', 'mng_p_automate')
    MONGODB_COLLECTIONS = {
        'analyses': 'analyses',
        'feedback': 'feedback',
        'prompts': 'analysis_prompts',
        'padrao_ouro': 'padrao_ouro',
        'clausulas_justificadas': 'clausulas_justificadas'
    }

    # Arquivos
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
    
    # Limites de processamento baseados na capacidade do modelo o3-mini (128k tokens)
    MAX_FILE_SIZE_MB = 25  # Tamanho máximo do arquivo em MB
    MAX_TEXT_CHARACTERS = 400000  # ~100k tokens (4 chars ≈ 1 token)
    MAX_PAGES_PDF = 100  # Máximo de páginas para PDF
    
    # Reserva de tokens para prompt do sistema e resposta
    SYSTEM_PROMPT_TOKENS = 2000  # Tokens reservados para prompts do sistema
    RESPONSE_TOKENS = 4000  # Tokens reservados para resposta (max_tokens)
    AVAILABLE_CONTEXT_TOKENS = 122000  # 128k - reservas = ~122k tokens disponíveis


  
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", "")
    API_VERSION = os.getenv("API_VERSION", "2024-12-01-preview")
    DEPLOYMENT_NAME = os.getenv("GPT4", "o3-mini")
    OPENAI_API_TYPE = os.getenv("OPENAI_API_TYPE", "azure")


    MODEL_CONFIG = {
        "temperature": float(os.getenv("MODEL_TEMPERATURE", 0.2)),
        "max_tokens": int(os.getenv("MODEL_MAX_TOKENS", 4000))
    }
