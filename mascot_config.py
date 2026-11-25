import streamlit as st
import base64
from pathlib import Path

def get_mascot_image_base64():
    """
    Retorna a imagem do mascote em base64.
    Coloque a imagem do mascote como 'mascot.png' na pasta do projeto.
    """
    import os
    
    # Tenta diferentes caminhos para encontrar o mascote
    possible_paths = [
        "masc_jur.png",  # Pasta atual
        os.path.join(os.path.dirname(__file__), "masc_jur.png"),  # Pasta do script
        os.path.join(os.getcwd(), "masc_jur.png"),  # Diretório de trabalho atual
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "masc_jur.png"),  # Pasta absoluta do script
    ]
    
    for mascot_path in possible_paths:
        if os.path.exists(mascot_path):
            try:
                with open(mascot_path, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode()
            except Exception as e:
                st.warning(f"Erro ao carregar mascote de {mascot_path}: {e}")
                continue
    
    # Se não encontrar a imagem, usa emoji como fallback
    return None


def get_mascot_avatar():
    """
    Retorna o avatar do mascote para uso no chat.
    Se tiver imagem, usa a imagem. Caso contrário, usa emoji.
    """
    image_b64 = get_mascot_image_base64()
    
    if image_b64:
        # Se tiver imagem, retorna data URI
        return f"data:image/png;base64,{image_b64}"
    else:
        # Fallback para emoji do robô
        return "🤖"

# Instruções para adicionar a imagem do mascote:
"""
INSTRUÇÕES PARA ADICIONAR O MASCOTE:

1. Salve a imagem do mascote como 'mascot.png' na pasta raiz do projeto
2. A imagem deve ter tamanho pequeno (recomendado: 64x64 pixels)
3. Formato PNG com fundo transparente funciona melhor
4. Se não adicionar a imagem, o sistema usará o emoji 🤖 automaticamente

Estrutura esperada:
lexmatch/
├── agent.py
├── mascot.png  ← Adicione a imagem aqui
├── mascot_config.py
└── style.css
"""
