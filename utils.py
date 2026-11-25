import unicodedata
import logging

logger = logging.getLogger(__name__)

THEME_SYNONYMS = {
    'preço': ['preço', 'pagamento', 'remuneração', 'valor', 'condições de pagamento', 'pagamentos', 'preco'],
    'pagamento': ['pagamento', 'preço', 'remuneração', 'valor', 'condições de pagamento', 'pagamentos', 'preco'],
    'remuneração': ['remuneração', 'pagamento', 'preço', 'valor'],
    'trabalhista': ['trabalhista', 'emprego', 'mão de obra', 'funcionário', 'colaborador', 'trabalho'],
    'confidencialidade': ['confidencialidade', 'sigilo', 'privacidade', 'informação confidencial', 'informações confidenciais'],
    'garantia': ['garantia', 'assegurar', 'seguro', 'responsabilidade'],
    'rescisão': ['rescisão', 'rescisao', 'término', 'termino', 'cancelamento', 'rompimento'],
    'responsabilidade': ['responsabilidade', 'obrigação', 'dever', 'responsavel'],
    
}

def create_text_index(db):
    """
    Cria o índice de texto necessário para a busca.
    Deve ser chamado uma única vez ao iniciar a aplicação.
    """
    try:
        # Cria índice de texto nos campos titulo e texto
        db.padrao_ouro.create_index([
            ("titulo", "text"),
            ("texto", "text")
        ])
        print("Índice de texto criado com sucesso")
    except Exception as e:
        print(f"Erro ao criar índice: {str(e)}")

def normalize_text(text):
    """Remove acentuação e normaliza para comparação insensível a maiúsculas/minúsculas."""
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    return text.lower().strip()

def get_theme_terms(query):
    """Retorna uma lista de termos relacionados ao tema identificado na query."""
    query_norm = normalize_text(query)
    terms = set()
    for theme, synonyms in THEME_SYNONYMS.items():
        if theme in query_norm or any(s in query_norm for s in synonyms):
            terms.update(synonyms)
    # Se não encontrar tema, retorna palavras da query
    if not terms:
        terms.update(query_norm.split())
    return list(terms)

def search_padrao_ouro_by_keyword(query, db, top_n=3):
    """
    Busca cláusulas no padrão ouro usando palavras-chave ou tema de forma robusta e rankeada.
    Prioriza match exato no título, depois parcial, depois busca no texto, usando também termos relacionados ao tema.
    """
    try:
        query_norm = normalize_text(query)
        theme_terms = get_theme_terms(query)
        logger.info(f"[PADRAO OURO] Buscando por: {query_norm} | termos: {theme_terms}")
        all_results = []
        seen_ids = set()
        # 1. Busca exata no título (normalizado)
        for doc in db.padrao_ouro.find():
            titulo_norm = normalize_text(doc.get('titulo', ''))
            if query_norm == titulo_norm or any(term == titulo_norm for term in theme_terms):
                doc['search_score'] = 100
                all_results.append(doc)
                seen_ids.add(str(doc.get('_id')))
        # 2. Busca parcial no título (contém termo relacionado)
        for doc in db.padrao_ouro.find():
            if str(doc.get('_id')) in seen_ids:
                continue
            titulo_norm = normalize_text(doc.get('titulo', ''))
            if any(term in titulo_norm for term in theme_terms):
                doc['search_score'] = 80
                all_results.append(doc)
                seen_ids.add(str(doc.get('_id')))
        # 3. Busca no texto (contém termo relacionado)
        for doc in db.padrao_ouro.find():
            if str(doc.get('_id')) in seen_ids:
                continue
            texto_norm = normalize_text(doc.get('texto', ''))
            if any(term in texto_norm for term in theme_terms):
                doc['search_score'] = 60
                all_results.append(doc)
                seen_ids.add(str(doc.get('_id')))
        # 4. Busca fallback: $text se houver índice
        try:
            text_results = list(db.padrao_ouro.find({"$text": {"$search": ' '.join(theme_terms)}}))
            for doc in text_results:
                if str(doc.get('_id')) not in seen_ids:
                    doc['search_score'] = 40
                    all_results.append(doc)
                    seen_ids.add(str(doc.get('_id')))
        except Exception as e:
            logger.warning(f"[PADRAO OURO] Falha ao buscar com $text: {str(e)}")
        # Ordena por score
        all_results.sort(key=lambda x: x.get('search_score', 0), reverse=True)
        # Remove campo auxiliar
        for doc in all_results:
            if 'search_score' in doc:
                del doc['search_score']
        logger.info(f"[PADRAO OURO] {len(all_results)} resultados encontrados para '{query}' com termos {theme_terms}")
        return all_results[:top_n]
    except Exception as e:
        logger.error(f"Erro na busca padrao_ouro: {str(e)}")
        return []

def build_comparison_prompt(user_question, contract_clause, padrao_ouro_clause):
    """
    Constrói o prompt para comparação de cláusulas de forma mais humana e natural.
    
    Args:
        user_question (str): Pergunta do usuário
        contract_clause (dict): Cláusula do contrato
        padrao_ouro_clause (dict): Cláusula do padrão ouro
    
    Returns:
        str: Prompt formatado de forma natural
    """
    prompt = (
        f"O usuário fez a seguinte pergunta: \"{user_question}\"\n\n"
        f"Vou analisar duas cláusulas para você:\n\n"
        f"**Cláusula do contrato atual:**\n"
        f"Título: {contract_clause.get('titulo', 'N/A')}\n"
        f"Conteúdo: {contract_clause.get('texto', 'N/A')}\n\n"
        f"**Cláusula do padrão ouro (referência):**\n"
        f"Título: {padrao_ouro_clause.get('titulo', 'N/A')}\n"
        f"Conteúdo: {padrao_ouro_clause.get('texto', 'N/A')}\n\n"
        f"Por favor, analise essas duas cláusulas e responda de forma clara e natural:\n"
        f"- As cláusulas estão alinhadas ou há divergências importantes?\n"
        f"- Quais são as principais diferenças que você identifica?\n"
        f"- Existem pontos que merecem atenção especial ou podem representar riscos?\n"
        f"- Que sugestões você faria para adequar a cláusula do contrato ao padrão ouro?"
    )
    return prompt

def search_clausulas_by_recomendacao(recomendacao, db, top_n=10):
    """
    Busca cláusulas justificadas por recomendação.
    Args:
        recomendacao (str): Texto da recomendação a buscar (ex: 'não acatar')
        db: Instância da classe MongoDB
        top_n (int): Número máximo de resultados
    Returns:
        list: Lista dos textos das cláusulas encontradas
    """
    try:
        # Busca na collection clausulas_justificadas
        results = list(db.clausulas_justificadas.find(
            {"recomendacao": {"$regex": recomendacao, "$options": "i"}}
        ).limit(top_n))
        # Retorna apenas o texto da cláusula
        return [doc.get("clausula_texto", "") for doc in results]
    except Exception as e:
        print(f"Erro na busca: {str(e)}")
        return []
