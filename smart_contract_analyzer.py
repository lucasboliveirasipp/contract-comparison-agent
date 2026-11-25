import logging  
from typing import Dict, List, Any  
from dataclasses import dataclass  
from .config import Config  
from langchain_core.messages import AIMessage  
  
logger = logging.getLogger(__name__)  
  
from modelos_llm import get_model  

# from models import get_model  
  
@dataclass  
class Modification:  
    type: str  # 'addition', 'removal', 'change'  
    original_text: str  
    modified_text: str  
    impact: str  
    risk_level: str  # 'low', 'medium', 'high'  
    suggestion: str  
    context: str  # Contexto da modificação  
  
class SmartContractAnalyzer:  
    def __init__(self, model_name: str = "gpt-4-o3"):  
        """  
        Inicializa o SmartContractAnalyzer com um modelo específico.  
  
        Args:  
            model_name (str): Nome do modelo a ser utilizado. Padrão: "gpt-4-o3".  
        """  
        try:  
            self.model = get_model(model_name)  
            logger.info(f"Modelo {model_name} carregado com sucesso.")  
        except Exception as e:  
            logger.error(f"Erro ao carregar o modelo {model_name}: {str(e)}")  
            raise  
  
    def analyze_contracts(self, original_text: str, modified_text: str, system_prompt: str = None, user_prompt: str = None) -> Dict:  
        """  
        Analisa dois contratos (original e modificado) e retorna uma análise detalhada com modificações.  
  
        Args:  
            original_text (str): Conteúdo do contrato original.  
            modified_text (str): Conteúdo do contrato modificado.  
            system_prompt (str, opcional): Prompt do sistema para configurar o comportamento do modelo.  
            user_prompt (str, opcional): Prompt do usuário com instruções específicas. Se não fornecido, usa um padrão.  
  
        Returns:  
            Dict: Dicionário contendo as modificações identificadas, um resumo e metadados da resposta do modelo.  
        """  
        try:  
            # Define o prompt do sistema padrão, se não fornecido  
            if system_prompt is None:  
                system_prompt = "Você é um especialista em análise jurídica de contratos. Seja metódico e consistente em suas análises."  
  
            # Define o prompt do usuário padrão, se não fornecido  
            if user_prompt is None:  
                # user_prompt = (  
                #     "Você é um especialista em análise jurídica de contratos. Compare o contrato original com o contrato modificado abaixo.\n"  
                #     "IMPORTANTE: Siga estas regras estritamente:\n"  
                #     "1. Analise o documento por seções/cláusulas numeradas\n"  
                #     "2. Compare cada seção/cláusula sequencialmente\n"  
                #     "3. Identifique TODAS as modificações, mesmo as menores\n"  
                #     "4. Mantenha a ordem das seções/cláusulas\n"  
                #     "5. Não agrupe modificações diferentes na mesma entrada\n"  
                #     "Para cada modificação encontrada, preencha todos os campos obrigatórios: tipo (adição, remoção, alteração), texto original, texto modificado, impacto, nível de risco (alto, médio, baixo), sugestão e contexto (cláusula, seção, etc.).\n"  
                #     "Retorne o resultado em JSON, seguindo exatamente este exemplo:\n"  
                #     '{"modifications": [{"type": "alteração", "original_text": "O prazo é de 12 meses.", "modified_text": "O prazo é de 24 meses.", "impact": "Aumenta o compromisso da contratada.", "risk_level": "médio", "suggestion": "Avaliar se o novo prazo é aceitável.", "context": "Cláusula 5.1"}], "summary": {"total_modifications": 1, "high_risk_count": 0, "medium_risk_count": 1, "low_risk_count": 0, "overall_risk": "médio", "risk_factors": [{"factor": "Aumento de prazo", "impact": "Pode gerar custos adicionais.", "suggestion": "Negociar condições."}]}}\n'  
                #     f"CONTRATO ORIGINAL:\n{original_text}\n\nCONTRATO MODIFICADO:\n{modified_text}"  
                # )
                             

                user_prompt = (
                    "Você é um especialista em análise jurídica de contratos. Compare o contrato original com o contrato modificado abaixo.\n"
                    "IMPORTANTE: Siga estas regras estritamente:\n"
                    "1. Analise o documento por seções/cláusulas numeradas\n"
                    "2. Compare cada seção/cláusula sequencialmente\n"
                    "3. Identifique TODAS as modificações, mesmo as menores\n"
                    "4. Mantenha a ordem das seções/cláusulas\n"
                    "5. Não agrupe modificações diferentes na mesma entrada\n"
                    "6. Além do texto principal, analise também a seção de COMENTÁRIOS dos contratos. Se houver mudanças, adições ou remoções de comentários, destaque essas alterações e explique se elas indicam mudanças relevantes nas cláusulas ou obrigações.\n"
                    "7. Ao classificar o campo 'peso' (alto, médio, baixo) de cada modificação, siga estas regras:\n"
                    "   - Se a palavra 'limitação' aparecer em cláusulas de responsabilidade, atribua PESO ALTO à modificação.\n"
                    "   - Se a expressão 'dano direto' ou a palavra 'dano' estiver atrelada a 'direto' ou 'valor', atribua PESO ALTO à modificação.\n"
                    "   - Caso contrário, classifique o peso conforme o impacto jurídico da modificação.\n"
                    "Inclua o campo 'peso' (alto, médio, baixo) em cada modificação reportada.\n"
                    "Para cada modificação encontrada, preencha todos os campos obrigatórios: tipo (adição, remoção, alteração), texto original, texto modificado, impacto, nível de alteração (alto, médio, baixo), sugestão e contexto (cláusula, seção, etc.).\n"
                    "Retorne o resultado em JSON, seguindo exatamente este exemplo:\n"
                    '{"modifications": [{"type": "alteração", "original_text": "O prazo é de 12 meses.", "modified_text": "O prazo é de 24 meses.", "impact": "Aumenta o compromisso da contratada.", "risk_level": "médio", "suggestion": "Avaliar se o novo prazo é aceitável.", "context": "Cláusula 5.1", "peso": "alto"}], "summary": {"total_modifications": 1, "high_risk_count": 0, "medium_risk_count": 1, "low_risk_count": 0, "overall_risk": "médio", "risk_factors": [{"factor": "Aumento de prazo", "impact": "Pode gerar custos adicionais.", "suggestion": "Negociar condições."}]}}\n'
                    f"CONTRATO ORIGINAL:\n{original_text}\n\nCONTRATO MODIFICADO:\n{modified_text}"
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
                    {"role": "system", "content": system_prompt},  
                    {"role": "user", "content": user_prompt}  
                ])  
                logger.info("Resposta obtida via 'invoke'.")  
  
            # Processa a resposta do modelo  
            logger.info(f"Resposta bruta do modelo: {getattr(response, 'content', response)}")  
            import json  
            try:  
                result = json.loads(response.content if hasattr(response, 'content') else str(response))  
            except json.JSONDecodeError as e:  
                logger.error(f"Erro ao decodificar JSON da resposta: {str(e)}")  
                result = {}  
  
            # Garante que os campos esperados estejam presentes  
            if 'modifications' not in result:  
                result['modifications'] = []  
            if 'summary' not in result:  
                result['summary'] = {  
                    'total_modifications': 0,  
                    'high_risk_count': 0,  
                    'medium_risk_count': 0,  
                    'low_risk_count': 0,  
                    'overall_risk': 'unknown',  
                    'risk_factors': []  
                }  
  
            # Converte as modificações para o formato dataclass  
            modifications = []  
            for mod in result.get('modifications', []):  
                try:  
                    modifications.append(Modification(  
                        type=mod.get('type', 'change'),  
                        original_text=mod.get('original_text', ''),  
                        modified_text=mod.get('modified_text', ''),  
                        impact=mod.get('impact', ''),  
                        risk_level=mod.get('risk_level', 'unknown'),  
                        suggestion=mod.get('suggestion', ''),  
                        context=mod.get('context', '')  
                    ))  
                except Exception as e:  
                    logger.warning(f"Erro ao processar modificação: {str(e)}")  
                    continue  
  
            return {  
                "modifications": modifications,  
                "summary": result['summary'],  
                "metadata": getattr(response, 'additional_kwargs', {})  
            }  
  
        except Exception as e:  
            logger.error(f"Erro na análise inteligente: {str(e)}")  
            return {  
                "modifications": [],  
                "summary": {  
                    'total_modifications': 0,  
                    'high_risk_count': 0,  
                    'medium_risk_count': 0,  
                    'low_risk_count': 0,  
                    'overall_risk': 'unknown',  
                    'risk_factors': []  
                },  
                "metadata": {}  
            }  
  
    def format_modifications_for_display(self, modifications: List[Modification]) -> Dict:  
        """  
        Formata as modificações para exibição, agrupando por tipo.  
  
        Args:  
            modifications (List[Modification]): Lista de modificações a serem formatadas.  
  
        Returns:  
            Dict: Dicionário com modificações agrupadas por tipo (additions, removals, changes).  
        """  
        formatted = {'additions': [], 'removals': [], 'changes': []}  
        for mod in modifications:  
            mod_type = mod.type.lower()  
            if mod_type not in ['addition', 'removal', 'change', 'adição', 'remoção', 'alteração']:  
                logger.warning(f"Tipo de modificação desconhecido: {mod_type}. Convertendo para 'change'.")  
                mod_type = 'change'  
            # Suporte a português e inglês  
            if mod_type in ['adição', 'addition']:  
                key = 'additions'  
            elif mod_type in ['remoção', 'removal']:  
                key = 'removals'  
            elif mod_type in ['alteração', 'change']:  
                key = 'changes'  
            else:  
                key = 'changes'  
            formatted[key].append({  
                'original': mod.original_text,  
                'modified': mod.modified_text,  
                'impact': mod.impact,  
                'risk_level': mod.risk_level,  
                'suggestion': mod.suggestion,  
                'context': mod.context  
            })  
        return formatted  
  
    def get_risk_color(self, risk_level: str) -> str:  
        """  
        Retorna a cor associada ao nível de risco para exibição.  
  
        Args:  
            risk_level (str): Nível de alteração (high, medium, low, alto, médio, baixo).  
  
        Returns:  
            str: Cor associada ao nível de alteração.  
        """  
        colors = {'high': 'red', 
                  'medium': 'orange', 
                  'low': 'green', 
                  'alto': 'red', 
                  'médio': 'orange', 
                  'baixo': 'green'}  
        return colors.get(risk_level.lower(), 'gray')  

