from typing import Dict, List
import logging  
from .utils import search_padrao_ouro_by_keyword, normalize_text
# from ..models import get_model 

from modelos_llm import get_model

logger = logging.getLogger(__name__)  

class ContractAnalyzer:  

    def __init__(self, model_name: str = "gpt-4-o3"):  

        """  

        Inicializa o ContractAnalyzer com um modelo específico.  

 

        Args:  

            model_name (str): Nome do modelo a ser utilizado. Padrão: "gpt-4-o3".  

        """  

        try:  

            self.model = get_model(model_name)  

            logger.info(f"Modelo {model_name} carregado com sucesso.")  

        except Exception as e:  

            logger.error(f"Erro ao carregar o modelo {model_name}: {str(e)}")  

            raise  

    def get_advogado_contratante_system_prompt(self) -> str:
        """
        Retorna o prompt do sistema para o agente atuar como advogado contratante.
        Foca na defesa dos interesses da contratante e identificação de potenciais riscos.
        """
        return """Você é um advogado especialista em contratos, representando exclusivamente os interesses da CONTRATANTE.
                    Apesar de mapear riscos, não utilize a palavra "risco" nos resumos gerados, no lugar utilize "ponto de atenção".

ROLE E RESPONSABILIDADES:
- Defender os interesses da contratante (nossa empresa)
- Identificar cláusulas que podem prejudicar a contratante
- Comparar com padrões de excelência (padrão ouro)
- Alertar sobre riscos e desvantagens
- Sugerir melhorias para proteger a contratante

PRINCÍPIOS DE ANÁLISE:
1. PRIMAZIA DA CONTRATANTE: Sempre priorize os interesses da contratante
2. IDENTIFICAÇÃO DOS PONTOS: Detecte cláusulas que podem prejudicar a contratante
3. COMPARAÇÃO COM PADRÃO OURO: Use o padrão ouro como referência de excelência
4. DETALHAMENTO DE IMPACTOS: Explique claramente os riscos e consequências
5. SUGESTÕES CONCRETAS: Proponha melhorias específicas e acionáveis

ASPECTOS CRÍTICOS A ANALISAR:
- Cláusulas de preço e pagamento
- Prazos e penalidades
- Responsabilidades e garantias
- Confidencialidade e propriedade intelectual
- Rescisão e multas
- Obrigações trabalhistas
- Limitações de responsabilidade
- Cláusulas de força maior

FORMATO DE RESPOSTA:
1. RESUMO: Principais riscos identificados
2. ANÁLISE DETALHADA: Comparação cláusula por cláusula
3. PONTOS DE ATENÇÃO: Impactos negativos para a contratante
4. RECOMENDAÇÕES: Sugestões específicas de melhoria
5. CLASSIFICAÇÃO DE RISCO: Alto/Médio/Baixo para cada ponto

LINGUAGEM:
- Clara e objetiva
- Focada em riscos e proteções
- Terminologia jurídica precisa
- Explicações acessíveis para não-juristas

Lembre-se: Você é o advogado da contratante. Sua missão é proteger seus interesses e identificar qualquer cláusula que possa prejudicá-la."""


    def get_chat_advogado_contratante_prompt(self) -> str:
        """
        Retorna o prompt do sistema para o chat atuar como advogado contratante de forma mais humana e natural.
        """
        return """Você é um advogado especialista em contratos, representando os interesses da CONTRATANTE. 

                COMO VOCÊ DEVE SE COMPORTAR:
                - Seja natural e conversacional, como um advogado experiente conversando com um cliente
                - Responda de forma clara e acessível, mas pode utilizar linguajar técnico jurídico
                - Use exemplos práticos e explique conceitos complexos de forma simples
                - Seja direto e honesto sobre riscos e problemas
                - Ofereça conselhos práticos e acionáveis

                SEU PAPEL:
                - Defender os interesses da contratante (nossa empresa)
                - Identificar problemas e riscos nos contratos
                - Comparar com padrões de excelência (padrão ouro)
                - Explicar situações de forma compreensível
                - Sugerir melhorias práticas

                LINGUAGEM E TOM:
                - Conversacional e natural
                - Clara e direta
                - Profissional mas acessível
                - Focada em proteger a contratante
                - Use "nós" quando se referir à contratante

                EXEMPLOS DE COMO RESPONDER:
                ❌ "Conforme análise estruturada, identificamos divergências..."
                ✅ "Encontrei alguns pontos que merecem atenção..."

                ❌ "A cláusula apresenta risco ALTO conforme classificação..."
                ✅ "Possível ponto de atenção. Essa cláusula pode nos prejudicar porque..."

                ❌ "RECOMENDAÇÕES: 1) Modificar cláusula..."
                ✅ "Sugiro que a gente peça para alterar essa parte porque..."

                Lembre-se: Você é o advogado da contratante. Responda de forma natural, como se estivesse conversando com um cliente sobre os riscos e oportunidades do contrato."""


    def get_comparison_prompt(self, contratada_text: str, padrao_ouro_clauses: List[Dict]) -> str:
        """
        Constrói o prompt para comparação entre contrato da contratada e padrão ouro.
        
        Args:
            contratada_text (str): Texto do contrato da contratada
            padrao_ouro_clauses (List[Dict]): Lista de cláusulas do padrão ouro
            
        Returns:
            str: Prompt formatado para análise
        """
        # Organiza as cláusulas do padrão ouro por categoria
        categorias = {
            'preço_pagamento': [],
            'prazos_penalidades': [],
            'responsabilidades': [],
            'confidencialidade': [],
            'rescisão': [],
            'trabalhista': [],
            'outros': []
        }
        
        for clause in padrao_ouro_clauses:
            titulo = normalize_text(clause.get('titulo', ''))
            texto = clause.get('texto', '')
            
            if any(term in titulo for term in ['preço', 'pagamento', 'valor', 'remuneração']):
                categorias['preço_pagamento'].append(clause)
            elif any(term in titulo for term in ['prazo', 'penalidade', 'multa', 'atraso']):
                categorias['prazos_penalidades'].append(clause)
            elif any(term in titulo for term in ['responsabilidade', 'garantia', 'obrigação']):
                categorias['responsabilidades'].append(clause)
            elif any(term in titulo for term in ['confidencialidade', 'sigilo', 'privacidade']):
                categorias['confidencialidade'].append(clause)
            elif any(term in titulo for term in ['rescisão', 'término', 'cancelamento']):
                categorias['rescisão'].append(clause)
            elif any(term in titulo for term in ['trabalhista', 'funcionário', 'colaborador']):
                categorias['trabalhista'].append(clause)
            else:
                categorias['outros'].append(clause)
        
        # Constrói o prompt
        prompt = f"""ANÁLISE COMPARATIVA: CONTRATO DA CONTRATADA vs PADRÃO OURO

                CONTRATO DA CONTRATADA:
                {contratada_text}

                PADRÃO OURO (REFERÊNCIA DE EXCELÊNCIA):
                """
        
        # Adiciona cláusulas do padrão ouro organizadas por categoria
        for categoria, clauses in categorias.items():
            if clauses:
                prompt += f"\n--- {categoria.upper().replace('_', ' ')} ---\n"
                for i, clause in enumerate(clauses, 1):
                    prompt += f"{i}. Título: {clause.get('titulo', 'N/A')}\n"
                    prompt += f"   Texto: {clause.get('texto', 'N/A')}\n\n"
        
        prompt += """
        INSTRUÇÕES DE ANÁLISE:

        1. COMPARAÇÃO SISTEMÁTICA:
        - Identifique cláusulas equivalentes entre o contrato da contratada e o padrão ouro
        - Compare cada cláusula em termos de proteção à contratante
        - Identifique desvios do padrão ouro que prejudicam a contratante

        2. IDENTIFICAÇÃO DE RISCOS:
        - Cláusulas que reduzem proteções da contratante
        - Obrigações excessivas ou desproporcionais
        - Limitações de responsabilidade da contratada
        - Penalidades inadequadas ou inexistentes

        3. ANÁLISE POR CATEGORIA:
        - Preço e Pagamento: Condições, prazos, reajustes
        - Prazos e Penalidades: Multas, atrasos, consequências
        - Responsabilidades: Garantias, obrigações, limitações
        - Confidencialidade: Proteção de informações
        - Rescisão: Condições de término, multas
        - Trabalhista: Responsabilidades com funcionários

        4. CLASSIFICAÇÃO DE RISCO:
        - ALTO: Prejuízo significativo à contratante
        - MÉDIO: Desvantagem moderada ou potencial ponto de atenção
        - BAIXO: Pequena desvantagem ou ponto de atenção mínimo

        5. RECOMENDAÇÕES:
        - Sugestões específicas de melhoria
        - Cláusulas que devem ser modificadas
        - Proteções que devem ser adicionadas

        FORMATO DA RESPOSTA:
        1. RESUMO (máximo 3 parágrafos)
        2. ANÁLISE POR CATEGORIA (detalhada)
        3. PONTOS DE ATENÇÃO (classificados por nível)
        4. RECOMENDAÇÕES ESPECÍFICAS
        5. CLASSIFICAÇÃO GERAL DO CONTRATO

        Lembre-se: Você é o advogado da contratante. Foque na proteção dos seus interesses."""
        
        return prompt

    def analyze_contracts_with_padrao_ouro(self, contratada_text: str, contratante_text: str, db) -> Dict:
        """
        Analisa o contrato da contratada comparando com o padrão ouro.
        
        Args:
            contratada_text (str): Texto do contrato da contratada
            contratante_text (str): Texto do contrato da contratante (para contexto)
            db: Instância do banco de dados MongoDB
            
        Returns:
            Dict: Análise detalhada com comparação ao padrão ouro
        """
        try:
            # Busca cláusulas do padrão ouro
            padrao_ouro_clauses = []
            
            # Busca por categorias principais
            categorias_busca = [
                'preço', 'pagamento', 'prazo', 'penalidade', 'responsabilidade',
                'garantia', 'confidencialidade', 'sigilo', 'rescisão', 'término',
                'trabalhista', 'funcionário', 'colaborador', 'obrigação', 'multa'
            ]
            
            for categoria in categorias_busca:
                clauses = search_padrao_ouro_by_keyword(categoria, db, top_n=3)
                padrao_ouro_clauses.extend(clauses)
            
            # Remove duplicatas baseado no ID
            seen_ids = set()
            unique_clauses = []
            for clause in padrao_ouro_clauses:
                clause_id = str(clause.get('_id', ''))
                if clause_id not in seen_ids:
                    seen_ids.add(clause_id)
                    unique_clauses.append(clause)
            
            padrao_ouro_clauses = unique_clauses[:10]  # Limita a 10 cláusulas mais relevantes
            
            # Constrói o prompt de comparação
            comparison_prompt = self.get_comparison_prompt(contratada_text, padrao_ouro_clauses)
            
            # Obtém o prompt do sistema para advogado contratante
            system_prompt = self.get_advogado_contratante_system_prompt()
            
            # Limpa histórico do modelo
            if hasattr(self.model, 'messages'):
                self.model.messages = []
            
            # Executa a análise
            if hasattr(self.model, 'add_message'):
                self.model.add_message("developer", system_prompt)
                self.model.add_message("user", comparison_prompt)
                response = self.model.send_chat()
            else:
                response = self.model.invoke([
                    {"role": "developer", "content": system_prompt},
                    {"role": "user", "content": comparison_prompt}
                ])
            
            # Retorna o resultado
            return {
                "analysis": response.content if hasattr(response, 'content') else str(response),
                "metadata": {
                    "padrao_ouro_clauses_count": len(padrao_ouro_clauses),
                    "contratada_text_length": len(contratada_text),
                    "contratante_text_length": len(contratante_text),
                    "analysis_type": "contratada_vs_padrao_ouro"
                }
            }
            
        except Exception as e:
            logger.error(f"Erro na análise com padrão ouro: {str(e)}")
            raise

    def analyze_contracts(self, contract1: str, contract2: str, system_prompt: str = None, user_prompt: str = None) -> Dict:  

        """  
        Analisa dois contratos fornecidos e retorna uma análise detalhada.  

        Args:  

            contract1 (str): Conteúdo do primeiro contrato.  

            contract2 (str): Conteúdo do segundo contrato.  

            system_prompt (str, opcional): Prompt do sistema para configurar o comportamento do modelo.  

            user_prompt (str, opcional): Prompt do usuário com instruções específicas. Se não fornecido, usa um padrão.  


        Returns:  

            Dict: Dicionário contendo a análise dos contratos e metadados da resposta do modelo.  

        """  

        try:  

            # Define o prompt do sistema padrão, se não fornecido  

            if system_prompt is None:  

                system_prompt = "Você é um especialista em análise jurídica de contratos."  

            # Define o prompt do usuário padrão, se não fornecido  

            if user_prompt is None:  

                user_prompt = (  

                    "Analise os contratos fornecidos considerando:\n"  

                    "1. Diferenças entre cláusulas equivalentes\n"  

                    "2. Pontos de atenção\n"  

                    "3. Sugestões de melhorias\n\n"  

                    f"CONTRATO 1:\n{contract1}\n\n"  

                    f"CONTRATO 2:\n{contract2}\n\n"  

                    "Faça uma análise detalhada seguindo os pontos solicitados."  

                )  

            # Limpa qualquer histórico de mensagens anterior no modelo, se aplicável  

            if hasattr(self.model, 'messages'):  

                self.model.messages = []  

                logger.info("Histórico de mensagens do modelo limpo.")  

 

            # Adiciona as mensagens ao histórico do modelo  

            if hasattr(self.model, 'add_message'):  

                self.model.add_message("developer", system_prompt)  

                self.model.add_message("user", user_prompt)  

                logger.info("Mensagens adicionadas ao histórico do modelo via 'add_message'.")  

            else:  

                logger.warning("Modelo não suporta 'add_message'. Usando invocação direta.")  

 

            # Envia as mensagens e obtém a resposta  

            if hasattr(self.model, 'send_chat'):  

                response = self.model.send_chat()  

                logger.info("Resposta obtida via 'send_chat'.")  

            else:  

                # Caso o modelo seja um AzureChatOpenAI diretamente, usa 'invoke'  

                response = self.model.invoke([  

                    {"role": "developer", "content": system_prompt},  

                    {"role": "user", "content": user_prompt}  

                ])  

                logger.info("Resposta obtida via 'invoke'.")  


            # Retorna a análise e os metadados  
            return {  

                "analysis": response.content if hasattr(response, 'content') else str(response),  

                "metadata": getattr(response, 'additional_kwargs', {})  

            }  

        except Exception as e:  

            logger.error(f"Erro na análise de contratos: {str(e)}")  

            raise
