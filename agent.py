import streamlit as st
from .document_processor import DocumentProcessor
from .contract_analyzer import ContractAnalyzer
from .hitl_system import HITLSystem
from .database import MongoDB
import pandas as pd
from datetime import datetime
import logging
import os
import base64
from .utils import search_padrao_ouro_by_keyword
from .utils import build_comparison_prompt
from typing import List
from .utils import get_theme_terms, normalize_text

from .config  import Config
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
import re


from .smart_contract_analyzer import SmartContractAnalyzer
from .export_utils import export_to_word, get_export_filename
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# Pushfront

def load_css():
    """Carrega o CSS personalizado"""
    import os
    from pathlib import Path
    
    # Tenta diferentes caminhos para encontrar o CSS
    possible_paths = [
        'style.css',  # Pasta atual
        os.path.join(os.path.dirname(__file__), 'style.css'),  # Pasta do script
        os.path.join(os.getcwd(), 'style.css'),  # Diretório de trabalho atual
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css'),  # Pasta absoluta do script
    ]
    
    css_content = None
    css_path = None
    
    for path in possible_paths:
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                    css_path = path
                    break
        except Exception as e:
            continue
    
    if css_content:
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
        # Opcional: mostrar onde encontrou o CSS (apenas em debug)
        # st.success(f"CSS carregado de: {css_path}")
    else:
        st.warning("Arquivo style.css não encontrado. Usando estilo padrão.")
        # Lista os caminhos que tentou (para debug)
        st.info(f"Tentou encontrar em: {possible_paths}")


def get_mascot_avatar():
    """Retorna o avatar do mascote para o chat"""
    from mascot_config import get_mascot_avatar as get_avatar
    return get_avatar()

def get_logo_image():
    """Retorna a imagem do logo em base64"""
    import os
    
    # Tenta diferentes caminhos para encontrar o logo
    possible_paths = [
        "consultoria.png",  # Pasta atual
        os.path.join(os.path.dirname(__file__), "consultoria.png"),  # Pasta do script
        os.path.join(os.getcwd(), "consultoria.png"),  # Diretório de trabalho atual
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "consultoria.png"),  # Pasta absoluta do script
    ]
    
    for logo_path in possible_paths:
        if os.path.exists(logo_path):
            try:
                with open(logo_path, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode()
            except Exception as e:
                st.warning(f"Erro ao carregar logo de {logo_path}: {e}")
                continue
    
    return None


# def create_header():
#     """Cria o cabeçalho personalizado"""
#     st.markdown("""
#     <div class="main-header">
#         <h1>🏛️ consultoria</h1>
#         <p style="margin: 0; font-size: 1.1rem; opacity: 0.9;">
#             Análise Inteligente de Contratos com IA
#         </p>
#     </div>
#     """, unsafe_allow_html=True)

def create_header():
    """Cria o cabeçalho personalizado com logo"""
    logo_b64 = get_logo_image()
    
    if logo_b64:
        # Se tiver a imagem do logo, usa ela
        st.markdown(f"""
        <div class="main-header">
            <img src="data:image/png;base64,{logo_b64}" alt="consultoria" class="logo-image">
        </div>
        """, unsafe_allow_html=True)
    else:
        # Fallback para texto se não tiver imagem
        st.markdown("""
        <div class="main-header">
            <h1>🏛️ consultoria</h1>
        </div>
        """, unsafe_allow_html=True)


def create_info_box(title, content):
    """Cria uma caixa de informação estilizada"""
    st.markdown(f"""
    <div class="info-box">
        <strong>{title}</strong><br>
        {content}
    </div>
    """, unsafe_allow_html=True)

class ContractAnalysisApp:

    def __init__(self):

        self.doc_processor = DocumentProcessor()

        self.analyzer = ContractAnalyzer()

       

        if 'db' not in st.session_state:

            st.session_state.db = MongoDB()

            # create_text_index(st.session_state.db.db)

        self.db = st.session_state.db

        self.hitl_system = HITLSystem(self.db)

        self.smart_analyzer = SmartContractAnalyzer()

       

        # Inicialização do estado da sessão

        if 'messages' not in st.session_state:

            st.session_state.messages = []

        if 'contracts_loaded' not in st.session_state:

            st.session_state.contracts_loaded = False

        if 'contract_texts' not in st.session_state:

            st.session_state.contract_texts = {'contratante': '', 'contratada': ''}

        if 'smart_analysis_result' not in st.session_state:

            st.session_state.smart_analysis_result = None  

        if 'analysis_result' not in st.session_state:

            st.session_state.analysis_result = None

   

    def run(self):
        # Carrega o CSS personalizado
        load_css()
        
        st.markdown('<div class="lexmatch-agent-container">', unsafe_allow_html=True) 

        # Cria o cabeçalho personalizado
        create_header()

        # CSS personalizado para tabs maiores
        st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 0px;
            width: 100%;
            justify-content: space-between;
        }
        
        .stTabs [data-baseweb="tab"] {
            flex: 1;
            min-width: 0;
            padding: 1rem 0.5rem;
            font-size: 1.1rem;
            font-weight: bold;
            text-align: center;
            background-color: var(--background-light);
            border: 2px solid var(--primary-color);
            border-radius: 8px;
            color: var(--primary-color);
            margin: 0 2px;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background-color: var(--light-color);
            color: white;
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: var(--primary-color);
            color: white;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        
        .stTabs [data-baseweb="tab-highlight"] {
            display: none;
        }
        </style>
        """, unsafe_allow_html=True)
        
        tab1, tab2, tab3,tab4 = st.tabs(["📋 Análise de Contratos", "💬 Chat de Análise", "🔄 Original/Modificado","📖 Guia Prompt"])

 

        with tab1:

            # Upload de contratos dentro da aba

            st.markdown("### 📊 Análise de Contratos vs Padrão Ouro")

            create_info_box(
                "🎯 Importante", 
                "O Agente realiza o comparativo entre a minuta da Contratada e o Clausulado padrão da Acme Seguros (Padrão Ouro), apoiando os advogados na análise comparativa dos instrumentos."
            )
            
            # Info box com limites de processamento
            create_info_box(
                "📏 Limites de Processamento (Modelo o3-mini)", 
                f"• Tamanho máximo: {Config.MAX_FILE_SIZE_MB}MB por arquivo<br>"
                f"• Contexto máximo: ~{Config.AVAILABLE_CONTEXT_TOKENS:,} tokens (~{Config.MAX_TEXT_CHARACTERS:,} caracteres)<br>"
                f"• PDF máximo: {Config.MAX_PAGES_PDF} páginas<br>"
                f"• Formatos: PDF e DOCX apenas"
            )

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Minuta da Contratante")
                contract1 = st.file_uploader("Drag and drop file here", type=['pdf', 'docx'], key="contratante", label_visibility="collapsed")

            with col2:
                st.markdown("#### Minuta da Contratada")
                contract2 = st.file_uploader("Drag and drop file here", type=['pdf', 'docx'], key="contratada", label_visibility="collapsed")

            if contract1 and contract2:

                if st.button("Analisar Minuta da Contratada vs. Padrão Ouro", use_container_width=True, type="primary"):

                    self.process_contracts(contract1, contract2)

            elif contract2 and not contract1:

                st.warning("⚠️ Por favor, faça upload do contrato da contratante também para análise completa.")

            elif contract1 and not contract2:

                st.warning("⚠️ Por favor, faça upload do contrato da contratada para análise.")

            # Resultados e feedback

            self.run_analysis_interface()

 

        with tab2:

            self.run_chat_interface()

 

        with tab3:

            # Info box com limites de processamento
            create_info_box(
                "📏 Limites de Processamento (Modelo o3-mini)", 
                f"• Tamanho máximo: {Config.MAX_FILE_SIZE_MB}MB por arquivo<br>"
                f"• Contexto máximo: ~{Config.AVAILABLE_CONTEXT_TOKENS:,} tokens (~{Config.MAX_TEXT_CHARACTERS:,} caracteres)<br>"
                f"• PDF máximo: {Config.MAX_PAGES_PDF} páginas<br>"
                f"• Formatos: PDF e DOCX apenas"
            )

            # Uploads para comparação original/modificado

            original = st.file_uploader("Contrato da original", type=['pdf', 'docx'], key="original")

            modified = st.file_uploader("Contrato do Modificado", type=['pdf', 'docx'], key="modified")

            # Botão para limpar dados carregados e resultados
            if st.button("🧹 Limpar Dados e Resultados", type="primary"):
                st.session_state.clear()
                st.experimental_rerun()

            # Botão de teste de extração
            if original or modified:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Comparar Contratos", use_container_width=True):
                        self.process_smart_analysis(original, modified)
                with col2:
                    if st.button("🧪 Testar Extração", use_container_width=True):
                        if original:
                            st.write("**Testando arquivo Original:**")
                            self.test_comment_extraction(original)
                        if modified:
                            st.write("**Testando arquivo Modificado:**")
                            self.test_comment_extraction(modified)

            self.run_smart_analysis_interface()

 

        with tab4:

            self.run_prompt_guide_interface()   

    def process_smart_analysis(self, original_contract, modified_contract):

        """Processa os contratos para análise inteligente"""

        try:
            # Valida os arquivos antes de processar
            with st.spinner("Validando arquivos..."):
                
                # Valida contrato original
                if original_contract:
                    is_valid1, message1 = self.doc_processor.validate_file_format(original_contract)
                    if not is_valid1:
                        st.error(f"**Erro no Contrato Original:**\n{message1}")
                        return
                
                # Valida contrato modificado
                if modified_contract:
                    is_valid2, message2 = self.doc_processor.validate_file_format(modified_contract)
                    if not is_valid2:
                        st.error(f"**Erro no Contrato Modificado:**\n{message2}")
                        return
                
                # Se chegou até aqui, os arquivos são válidos
                st.success("✅ Arquivos validados com sucesso!")

            with st.spinner("Processando contratos para análise inteligente..."):

                # Extrai texto dos documentos

                original_text = self.doc_processor.extract_text(original_contract)

                modified_text = self.doc_processor.extract_text(modified_contract)

               

                # Realiza análise inteligente

                smart_analysis_result = self.smart_analyzer.analyze_contracts(

                    original_text,

                    modified_text

                )

                # Salva o resultado na sessão
                st.session_state.smart_analysis_result = smart_analysis_result

                st.session_state.contracts_loaded = True

                # Recarrega a página para atualizar a interface
                st.rerun()

        except Exception as e:
            logger.error(f"Erro durante a análise inteligente: {str(e)}")

            st.error(f"Erro durante a análise inteligente: {str(e)}")

    def run_smart_analysis_interface(self):

        """Interface da análise inteligente"""

        if st.session_state.contracts_loaded and st.session_state.smart_analysis_result:

            # Exibe o resumo geral
            try:
                # Exibe o resumo geral

                summary = st.session_state.smart_analysis_result.get('summary', {})

                st.markdown("### 📊 Resumo da Análise Inteligente")

                # Métricas principais

                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.metric("Total de Modificações", summary.get('total_modifications', 0))

                with col2:

                    st.metric("Riscos Altos", summary.get('high_risk_count', 0), delta_color="inverse")

                with col3:

                    st.metric("Riscos Médios", summary.get('medium_risk_count', 0))

                with col4:

                    st.metric("Riscos Baixos", summary.get('low_risk_count', 0), delta_color="normal")

                # Nível de risco geral
                overall_risk = summary.get('overall_risk', 'unknown')

                risk_color = self.smart_analyzer.get_risk_color(overall_risk)

                st.markdown(f"### Quantidade de modificações: :{risk_color}[{overall_risk.upper()}]")

               
                # Exibe as modificações

                modifications = st.session_state.smart_analysis_result.get('modifications', [])

                formatted_mods = self.smart_analyzer.format_modifications_for_display(modifications)

                # Adições
                if formatted_mods.get('additions'):

                    with st.expander("➕ Adições", expanded=True):

                        for mod in formatted_mods['additions']:

                            st.markdown(f"**Contexto:** {mod.get('context', 'N/A')}")

                            st.markdown(f"**Texto Adicionado:** {mod.get('modified', 'N/A')}")

                            st.markdown(f"**Impacto:** {mod.get('impact', 'N/A')}")

                            st.markdown(f"**Qtd Modificações:** :{self.smart_analyzer.get_risk_color(mod.get('risk_level', 'unknown'))}[{mod.get('risk_level', 'UNKNOWN').upper()}]")

                            st.markdown(f"**Sugestão:** {mod.get('suggestion', 'N/A')}")

                            st.markdown("---")

                # Remoções
                if formatted_mods.get('removals'):

                    with st.expander("➖ Remoções", expanded=True):

                        for mod in formatted_mods['removals']:

                            st.markdown(f"**Contexto:** {mod.get('context', 'N/A')}")

                            st.markdown(f"**Texto Removido:** {mod.get('original', 'N/A')}")

                            st.markdown(f"**Impacto:** {mod.get('impact', 'N/A')}")

                            st.markdown(f"**Qtd Modificações:** :{self.smart_analyzer.get_risk_color(mod.get('risk_level', 'unknown'))}[{mod.get('risk_level', 'UNKNOWN').upper()}]")

                            st.markdown(f"**Sugestão:** {mod.get('suggestion', 'N/A')}")

                            st.markdown("---")

                # Alterações
                if formatted_mods.get('changes'):

                    with st.expander("🔄 Alterações", expanded=True):

                        for mod in formatted_mods['changes']:

                            st.markdown(f"**Contexto:** {mod.get('context', 'N/A')}")

                            col1, col2 = st.columns(2)

                            with col1:

                                st.markdown("**Texto Original:**")

                                st.text(mod.get('original', 'N/A'))
                            with col2:

                                st.markdown("**Texto Modificado:**")

                                st.text(mod.get('modified', 'N/A'))

                           

                            st.markdown(f"**Impacto:** {mod.get('impact', 'N/A')}")

                            st.markdown(f"**Qtd Modificações:** :{self.smart_analyzer.get_risk_color(mod.get('risk_level', 'unknown'))}[{mod.get('risk_level', 'UNKNOWN').upper()}]")

                            st.markdown(f"**Sugestão:** {mod.get('suggestion', 'N/A')}")

                            st.markdown("---")

                # Botão de exportação
                st.markdown("### 📥 Exportar Relatório de Modificações")
                
                if st.button("📄 Exportar Modificações para Word", use_container_width=True, key="export_smart_word"):
                    try:
                        with st.spinner("Gerando arquivo Word..."):
                            word_buffer = export_to_word(st.session_state.smart_analysis_result, "smart_analysis")
                            filename = get_export_filename("smart_analysis", "word")
                            
                            st.download_button(
                                label="⬇️ Download Word",
                                data=word_buffer.getvalue(),
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True,
                                key="download_smart_word"
                            )
                    except Exception as e:
                        st.error(f"Erro ao gerar Word: {str(e)}")

                # Interface de feedback
                # self.display_feedback_interface(st.session_state.smart_analysis_result)

            except Exception as e:

                logger.error(f"Erro ao exibir resultados da análise inteligente: {str(e)}")

                st.error(f"Erro ao exibir resultados: {str(e)}")

        else:

            st.warning("Por favor, faça o upload e análise dos contratos primeiro.")


    def process_contracts(self, contract1, contract2):

        """Processa os contratos e realiza a análise inicial comparando contratada com padrão ouro"""
        try:
            # Valida os arquivos antes de processar
            with st.spinner("Validando arquivos..."):
                
                # Valida contrato da contratante
                is_valid1, message1 = self.doc_processor.validate_file_format(contract1)
                if not is_valid1:
                    st.error(f"**Erro no Contrato da Contratante:**\n{message1}")
                    return
                
                # Valida contrato da contratada
                is_valid2, message2 = self.doc_processor.validate_file_format(contract2)
                if not is_valid2:
                    st.error(f"**Erro no Contrato da Contratada:**\n{message2}")
                    return
                
                # Se chegou até aqui, os arquivos são válidos
                st.success("✅ Arquivos validados com sucesso!")

            with st.spinner("Processando contratos e comparando com padrão ouro..."):

                # Extrai texto dos documentos

                text1 = self.doc_processor.extract_text(contract1)  # Contratante

                text2 = self.doc_processor.extract_text(contract2)  # Contratada

               

                # Salva os textos na sessão

                st.session_state.contract_texts = {

                    'contratante': text1,

                    'contratada': text2

                }

                # Realiza análise comparando contratada com padrão ouro
                analysis_result = self.analyzer.analyze_contracts_with_padrao_ouro(

                    text2,  # Contratada

                    text1,  # Contratante (para contexto)

                    self.db.db  # Banco de dados para buscar padrão ouro

                )
                # Salva o resultado na sessão
                st.session_state.analysis_result = analysis_result

                st.session_state.contracts_loaded = True

               
                # Recarrega a página para atualizar a interface

                st.rerun()

               
        except Exception as e:

            logger.error(f"Erro durante a análise: {str(e)}")

            st.error(f"Erro durante a análise: {str(e)}")

    def run_analysis_interface(self):

        """Interface principal de análise de contratos"""

        if st.session_state.contracts_loaded and st.session_state.analysis_result:

            # Exibe resultados

            self.display_results(st.session_state.analysis_result)

           

            # Interface de feedback

            self.display_feedback_interface(st.session_state.analysis_result)

 
    def is_casual_greeting(self, message):
        """
        Detecta se a mensagem é uma saudação ou conversa casual.
        
        Args:
            message (str): Mensagem do usuário
            
        Returns:
            bool: True se for uma saudação casual
        """
        import re
        
        # Normaliza a mensagem
        message_lower = message.lower().strip()
        
        # Lista de saudações e frases casuais
        casual_patterns = [
            r'^(oi|olá|ola|hey|hi|hello)$',
            r'^(bom dia|boa tarde|boa noite)$',
            r'^(como vai|como está|tudo bem)$',
            r'^(obrigado|obrigada|valeu|thanks)$',
            r'^(tchau|até logo|bye|até mais)$',
            r'^(qual seu nome|quem é você)$',
            r'^(o que você faz|para que serve)$',
            r'^(help|ajuda|socorro)$',
            r'^(teste|testando)$',
            r'^(ok|okay|beleza|blz)$',
            r'^(sim|não|não|yes|no)$',
            r'^(legal|bacana|show|massa)$'
        ]
        
        # Verifica se a mensagem corresponde a algum padrão casual
        for pattern in casual_patterns:
            if re.match(pattern, message_lower):
                return True
        
        # Verifica se é uma mensagem muito curta (provavelmente casual)
        if len(message_lower.split()) <= 2 and len(message_lower) <= 20:
            return True
            
        return False

    def get_casual_response(self, message):
        """
        Retorna uma resposta casual apropriada baseada na mensagem.
        
        Args:
            message (str): Mensagem do usuário
            
        Returns:
            str: Resposta casual
        """
        import random
        
        message_lower = message.lower().strip()
        
        # Respostas para saudações
        if any(greeting in message_lower for greeting in ['oi', 'olá', 'ola', 'hey', 'hi', 'hello']):
            responses = [
                "Olá! Como posso ajudar em sua análise hoje?",
                "Oi! Estou aqui para analisar contratos e identificar riscos. O que gostaria de saber?",
                "Olá! Pronto para analisar contratos e proteger os interesses da contratante. Como posso ajudar?"
            ]
        
        # Respostas para cumprimentos de horário
        elif any(time in message_lower for time in ['bom dia', 'boa tarde', 'boa noite']):
            responses = [
                "Bom dia! Como posso ajudar em sua análise de contratos hoje?",
                "Boa tarde! Estou aqui para analisar contratos e comparar com o padrão ouro. O que precisa?",
                "Boa noite! Pronto para identificar riscos nos contratos. Como posso ajudar?"
            ]
        
        # Respostas para perguntas sobre o agente
        elif any(q in message_lower for q in ['qual seu nome', 'quem é você', 'o que você faz']):
            responses = [
                "Sou o assistente jurídico da LexMatch! Ajudo a analisar contratos, comparar com padrões de excelência e identificar riscos para proteger a contratante.",
                "Sou seu advogado virtual! Especializado em análise de contratos e identificação de riscos para defender os interesses da contratante.",
                "Sou o agente de análise contratual! Minha função é comparar contratos com o padrão ouro e alertar sobre possíveis riscos."
            ]
        
        # Respostas para agradecimentos
        elif any(thanks in message_lower for thanks in ['obrigado', 'obrigada', 'valeu', 'thanks']):
            responses = [
                "De nada! Estou aqui sempre que precisar de ajuda com análise de contratos.",
                "Por nada! Qualquer dúvida sobre contratos ou padrão ouro, é só perguntar!",
                "Disponha! Sempre pronto para ajudar na análise contratual."
            ]
        
        # Respostas para despedidas
        elif any(bye in message_lower for bye in ['tchau', 'até logo', 'bye', 'até mais']):
            responses = [
                "Até logo! Qualquer dúvida sobre contratos, estarei aqui!",
                "Tchau! Volte sempre que precisar analisar contratos.",
                "Até mais! Lembre-se: sempre analise os contratos antes de assinar!"
            ]
        
        # Resposta padrão para outras mensagens casuais
        else:
            responses = [
                "Olá! Como posso ajudar em sua análise hoje?",
                "Oi! Estou aqui para analisar contratos e identificar riscos. O que gostaria de saber?",
                "Olá! Pronto para analisar contratos e proteger os interesses da contratante. Como posso ajudar?"
            ]
        
        return random.choice(responses) 


    def run_chat_interface(self):
        """
        Executa a interface de chat para análise de contratos no Streamlit.
        Permite ao usuário fazer perguntas sobre os contratos carregados ou cláusulas padrão ouro.
        """
        if not st.session_state.contracts_loaded:
            st.warning("Por favor, primeiro faça o upload e análise dos contratos na aba 'Análise de Contratos'.")
            return
        st.header("Chat de Análise de Contratos")
        if st.button("Limpar Chat", type="secondary"):
            st.session_state.messages = []
            st.rerun()
        chat_container = st.container()
        input_container = st.container()
        with input_container:
            prompt = st.chat_input("Faça uma pergunta sobre os contratos ou cláusulas padrão ouro...")
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "assistant":
                    with st.chat_message(message["role"], avatar=get_mascot_avatar()):
                        st.markdown(message["content"])
                else:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            try:
                if hasattr(self.analyzer.model, 'messages'):
                    self.analyzer.model.messages = []
                    logger.info("Histórico de mensagens do modelo limpo.")
                if self.is_casual_greeting(prompt):
                    # Resposta casual e amigável
                    casual_response = self.get_casual_response(prompt)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": casual_response
                    })
                    st.rerun()
                    return
    
                # Usa o prompt do chat (mais humano e natural)
                system_prompt = self.analyzer.get_chat_advogado_contratante_prompt() 
                user_prompt = prompt
                # Busca semântica por tema para padrão ouro
                padrao_ouro_clauses = search_padrao_ouro_by_keyword(
                    prompt,
                    self.db.db,
                    top_n=1
                )
                padrao_ouro_clause = padrao_ouro_clauses[0] if padrao_ouro_clauses else None
                # Busca semântica por tema no contrato da contratada
                import re
                from .utils import get_theme_terms, normalize_text
                contract_text = st.session_state.contract_texts['contratada']
                contract_clause_text = None
                theme_terms = get_theme_terms(prompt)
                # Busca por título ou termo relacionado no contrato carregado
                for term in theme_terms:
                    pattern = re.compile(rf"CL[ÁA]USULA[^\n]*{re.escape(term)}[^\n]*.*?(?=CL[ÁA]USULA|$)", re.IGNORECASE | re.DOTALL)
                    match = pattern.search(contract_text)
                    if match:
                        contract_clause_text = match.group(0).strip()
                        break
                # Monta o prompt com os contextos encontrados
                if padrao_ouro_clause and contract_clause_text:
                    user_prompt = (
                        f"{prompt}\n\nAqui está o texto da cláusula relevante do padrão ouro para seu contexto:\n"
                        f"Título: {padrao_ouro_clause.get('titulo', 'N/A')}\n"
                        f"Texto: {padrao_ouro_clause.get('texto', 'N/A')}\n"
                        f"\nAqui está o texto da cláusula correspondente do contrato da contratada:\n"
                        f"{contract_clause_text}\n"
                    )
                elif padrao_ouro_clause:
                    user_prompt = (
                        f"{prompt}\n\nAqui está o texto da cláusula relevante do padrão ouro para seu contexto:\n"
                        f"Título: {padrao_ouro_clause.get('titulo', 'N/A')}\n"
                        f"Texto: {padrao_ouro_clause.get('texto', 'N/A')}\n"
                    )
                elif contract_clause_text:
                    user_prompt = (
                        f"{prompt}\n\nAqui está o texto da cláusula correspondente do contrato da contratada:\n"
                        f"{contract_clause_text}\n"
                    )
                else:
                    user_prompt = (
                        f"{prompt}\n\nNão foi possível localizar uma cláusula relevante nem no padrão ouro nem no contrato carregado para o tema pesquisado.\n"
                    )
                if hasattr(self.analyzer.model, 'add_message'):
                    self.analyzer.model.add_message("developer", system_prompt)
                    if user_prompt:
                        self.analyzer.model.add_message("user", user_prompt)
                    logger.info("Mensagens adicionadas ao histórico do modelo via 'add_message'.")
                else:
                    logger.warning("Modelo não suporta 'add_message'. Usando invocação direta.")
                if hasattr(self.analyzer.model, 'send_chat'):
                    response = self.analyzer.model.send_chat()
                    logger.info("Resposta obtida via 'send_chat'.")
                else:
                    response = self.analyzer.model.invoke([
                        {"role": "developer", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ])
                    logger.info("Resposta obtida via 'invoke'.")
                resposta = response.content if hasattr(response, 'content') else str(response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": resposta
                })
                st.rerun()
            except Exception as e:
                logger.error(f"Erro ao processar pergunta: {str(e)}")
                st.error(f"Erro ao processar sua pergunta: {str(e)}")

    def display_results(self, analysis_result):

        """Exibe os resultados da análise comparativa com padrão ouro"""

        st.markdown("### 📊 Resultados da Análise: Contratada vs Padrão Ouro")

        # Informações sobre a análise
        metadata = analysis_result.get('metadata', {})
        if metadata.get('analysis_type') == 'contratada_vs_padrao_ouro':
            st.success("✅ Análise realizada comparando contrato da contratada com padrão ouro")
            
            # # Métricas da análise em containers estilizados
            # col1, col2, col3 = st.columns(3)
            # with col1:
            #     st.markdown("""
            #     <div class="metric-container">
            #         <h4 style="color: var(--primary-color); margin: 0;">Cláusulas Padrão Ouro</h4>
            #         <h2 style="margin: 0;">{}</h2>
            #     </div>
            #     """.format(metadata.get('padrao_ouro_clauses_count', 0)), unsafe_allow_html=True)
                
            # with col2:
            #     st.markdown("""
            #     <div class="metric-container">
            #         <h4 style="color: var(--primary-color); margin: 0;">Contrato Contratada</h4>
            #         <h2 style="margin: 0;">{:,} chars</h2>
            #     </div>
            #     """.format(metadata.get('contratada_text_length', 0)), unsafe_allow_html=True)
                
            # with col3:
            #     st.markdown("""
            #     <div class="metric-container">
            #         <h4 style="color: var(--primary-color); margin: 0;">Contrato Contratante</h4>
            #         <h2 style="margin: 0;">{:,} chars</h2>
            #     </div>
            #     """.format(metadata.get('contratante_text_length', 0)), unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["📋 Análise Detalhada", "📊 Metadados"])

        with tab1:
            st.markdown("""
            <div class="analysis-container">
                <h3>🎯 Análise detalhada</h3>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(analysis_result['analysis'])

        with tab2:
            st.json(analysis_result['metadata'])
        
        # Botão de exportação
        st.markdown("### 📥 Exportar Relatório")
        
        if st.button("📄 Exportar para Word", use_container_width=True):
            try:
                with st.spinner("Gerando arquivo Word..."):
                    word_buffer = export_to_word(analysis_result, "contract_analysis")
                    filename = get_export_filename("contract_analysis", "word")
                    
                    st.download_button(
                        label="⬇️ Download Word",
                        data=word_buffer.getvalue(),
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Erro ao gerar Word: {str(e)}")

 

    def run_prompt_guide_interface(self):

        """Interface do guia de prompts"""

        st.header("📝 Guia de Prompts para Análise de Contratos")

       

        st.markdown("""

        ### 🎯 Como Formular Perguntas Efetivas

       

        Este guia ajudará você a obter as melhores respostas do nosso sistema de análise de contratos.

        """)

       

        # Seção de Exemplos de Prompts

        with st.expander("📋 Exemplos de Prompts Efetivos", expanded=False):

            st.markdown("""

            #### Análise de Cláusulas Específicas

            - "Compare as cláusulas de rescisão entre os contratos"

            - "Quais são as diferenças na cláusula de confidencialidade?"

            - "Analise as obrigações da contratada em ambos os contratos"

           

            #### Análise de Riscos

            - "Identifique os principais riscos na cláusula de pagamento"

            - "Quais são os pontos de atenção na cláusula de garantia?"

            - "Analise os riscos associados ao prazo de execução"

           

            #### Análise de Modificações

            - "Quais foram as principais alterações na cláusula de preço?"

            - "Compare as versões da cláusula de responsabilidade"

            - "Identifique as mudanças no escopo do contrato"

            """)

       

        # Seção de Dicas

        with st.expander("💡 Dicas para Melhores Resultados", expanded=False):

            st.markdown("""

            #### 1. Seja Específico

            - ❌ "Analise o contrato"

            - ✅ "Analise as cláusulas de pagamento e prazo"

           

            #### 2. Use Contexto

            - ❌ "Quais são as diferenças?"

            - ✅ "Quais são as diferenças nas obrigações da contratada?"

           

            #### 3. Foque em Aspectos Específicos

            - ❌ "O contrato está bom?"

            - ✅ "Quais são os riscos na cláusula de confidencialidade?"

            """)

       

        # Seção de Estrutura de Perguntas

        with st.expander("🔍 Estrutura Recomendada para Perguntas", expanded=False):

            st.markdown("""

            #### Modelo de Pergunta Efetiva:

            1. **Contexto**: Especifique qual aspecto você quer analisar

            2. **Foco**: Indique qual parte do contrato interessa

            3. **Objetivo**: Diga o que você quer descobrir

           

            #### Exemplo:

            "Analise as diferenças nas obrigações de confidencialidade entre os contratos, focando nos prazos e penalidades"

            """)

       

        # Seção de Boas Práticas

        with st.expander("✨ Boas Práticas", expanded=False):

            st.markdown("""

           #### O que Fazer:

            - ✅ Use termos jurídicos específicos

            - ✅ Faça uma pergunta por vez

            - ✅ Seja claro sobre o que quer analisar

            - ✅ Use o contexto do seu caso específico

           

            #### O que Evitar:

            - ❌ Perguntas muito genéricas

            - ❌ Múltiplas perguntas em uma só

            - ❌ Linguagem muito informal

            - ❌ Pedidos vagos ou ambíguos

            """)

       

        # Seção de Exemplos Práticos

        with st.expander("📚 Exemplos Práticos", expanded=True):

            st.markdown("""

            #### Camadas

            1. **Requisitos funcionais da análise**   

                • Quais são os resultados esperados? 

                • Gere contexto antes de realizar perguntas. 

                É necessário  que as cláusulas, minutas e artigos entre os contratos **contratada/contratante** sejam comparadas, quero entender se existem riscos no contrato,

                principalmente em cláusulas que são divergentes do "padrão ouro" .

                Existe equivalência no contrato da contratada? 

                • Formato dos relatórios de comparação

                        

            2. **Técnicas específicas que você gostaria de utilizar** 

                • Técnicas ou processos jurídicos específicos que gostaria de entender, ou que o chat considera-se na resposta / análise. 

                • O que é: Verificar se cláusulas essenciais estão presentes e em conformidade com o padrão interno da empresa. 

                • Exemplo de uso: Checar se a cláusula de confidencialidade atende ao modelo da área jurídica da contratante. 

                • **Métodos de processamento de texto:**

                Insira contexto específico, se for uma cláusula específica por exemplo trabalhista, trabalhe neste tópico com granularidade, e não misture muitas perguntas de outros assuntos.

                       

            3. **Conceitos que devem ser aplicados** 

                • Conceitos jurídicos relevantes 

                • Regras de negócio específicas 

                • Padrões de documentos a serem considerados 

              

            4. **Restrições técnicas** 

            • Se existirem restrições específicas do caso analisado é importante detalhar.

 

            """)       

    

    def display_feedback_interface(self, analysis_result):

        """Interface para coleta de feedback"""

        with st.expander("Fornecer Feedback"):

            feedback_type = st.selectbox(

                "Tipo de Feedback",

                ["Melhoria de Análise", "Correção de Erro", "Sugestão Geral"]

            )

           

            feedback = st.text_area("Seu feedback")

            improvements = st.text_area("Sugestões de melhoria (uma por linha)")

           

            if st.button("Enviar Feedback"):

                try:

                    feedback_data = {

                        "analysis_id": analysis_result["metadata"]["id"],

                        "feedback": feedback,

                        "feedback_type": feedback_type,

                        "improvements": [imp.strip() for imp in improvements.split("\n") if imp.strip()]

                    }

                   

                    feedback_id = self.hitl_system.save_feedback(feedback_data)

                    st.success(f"Feedback registrado com sucesso! ID: {feedback_id}")

               

                except Exception as e:

                    logger.error(f"Erro ao salvar feedback: {str(e)}")

                    st.error(f"Erro ao salvar feedback: {str(e)}")

 

    def test_comment_extraction(self, uploaded_file):
        import pandas as pd
        import re
        try:
            # Valida o arquivo antes de testar
            with st.spinner("Validando arquivo..."):
                is_valid, message = self.doc_processor.validate_file_format(uploaded_file)
                if not is_valid:
                    st.error(f"**Erro na validação do arquivo:**\n{message}")
                    return
            
            with st.spinner("Testando extração de comentários..."):
                full_text = self.doc_processor.extract_text(uploaded_file)
                st.write(f"📄 **Tamanho do texto extraído:** {len(full_text)} caracteres")
                if "COMENTÁRIOS:" in full_text:
                    st.success("✅ Comentários detectados no texto extraído!")
                    comments_section = full_text.split("COMENTÁRIOS:")[1]
                    if "REVISÕES:" in comments_section:
                        comments_section = comments_section.split("REVISÕES:")[0]
                    st.write(f"📝 **Seção de comentários:** {len(comments_section)} caracteres")
                    # Regex para encontrar todos os comentários
                    comment_pattern = re.compile(r"Comentário\s*\d+:(.*?)((?=Comentário\s*\d+:)|$)", re.DOTALL)
                    comment_blocks = comment_pattern.findall(comments_section)
                    table_data = []
                    for i, block_tuple in enumerate(comment_blocks):
                        block = block_tuple[0]
                        # Extrai campos usando regex
                        loc_match = re.search(r"Localização:\s*([^\n]*?)\s*Texto referenciado:", block)
                        ref_match = re.search(r"Texto referenciado:\s*\"([\s\S]*?)\"\s*Comentário:", block)
                        comm_match = re.search(r"Comentário:\s*([\s\S]*)", block)
                        loc = loc_match.group(1).strip() if loc_match else ""
                        ref = ref_match.group(1).strip() if ref_match else ""
                        comm = comm_match.group(1).strip() if comm_match else ""
                        table_data.append({
                            "Nº": i+1,
                            "Localização": loc,
                            "Texto Referenciado": ref,
                            "Comentário": comm
                        })
                    st.write(f"🔢 **Número de comentários encontrados:** {len(table_data)}")
                    with st.expander("📋 Comentários Extraídos (Tabela)", expanded=True):
                        if table_data:
                            df = pd.DataFrame(table_data)
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("Nenhum comentário encontrado no documento.")
                else:
                    st.warning("❌ Nenhum comentário detectado no texto extraído")
                if "REVISÕES:" in full_text:
                    st.success("✅ Revisões detectadas no texto extraído!")
                else:
                    st.info("ℹ️ Nenhuma revisão detectada")
        except Exception as e:
            st.error(f"❌ Erro durante o teste: {str(e)}")
            logger.error(f"Erro no teste de extração: {str(e)}")


# para teste local ##

# def main():

#     try:

#         app = ContractAnalysisApp()

#         app.run()

#     except Exception as e:

#         logger.error(f"Erro na aplicação: {str(e)}")

#         st.error("Ocorreu um erro na aplicação. Por favor, tente novamente.")

 

# if __name__ == "__main__":

#     main()

    # # para teste local ##

    # ------------------------#

    # main para deploy

    # ------------------------#

    def main():

        try:

            app = ContractAnalysisApp()

            app.run()

        except Exception as e:

            logger.error(f"Erro na aplicação: {str(e)}")

            st.error("Ocorreu um erro na aplicação. Por favor, tente novamente.")

 

def main():
    app = ContractAnalysisApp()
    app.run()

def build_page(is_authenticated: bool):
    if is_authenticated:
        main()

    else:

        st.error("Você não está autenticado. Por favor, faça login para acessar esta página.")
