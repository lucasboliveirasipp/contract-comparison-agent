# document_processor.py
import PyPDF2
import docx
from typing import BinaryIO, Tuple
import logging
import re

from docx.document import Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

logger = logging.getLogger(__name__)

# Importações com fallback para compatibilidade entre ambientes (dev/prod)
try:
    from .config import Config
except ImportError:
    from config import Config



class DocumentProcessor:
    def validate_file_format(self, file: BinaryIO) -> Tuple[bool, str]:
        """
        Valida se o arquivo está no formato correto e dentro dos limites.
        
        Args:
            file (BinaryIO): Arquivo a ser validado
            
        Returns:
            Tuple[bool, str]: (é_válido, mensagem_erro)
        """
        try:
            filename = file.name.lower()
            
            # Volta o ponteiro do arquivo para o início
            file.seek(0)
            
            # Valida tamanho do arquivo
            file.seek(0, 2)  # Vai para o final
            file_size = file.tell()
            file.seek(0)  # Volta para o início
            
            max_size_bytes = Config.MAX_FILE_SIZE_MB * 1024 * 1024
            if file_size > max_size_bytes:
                return False, f"❌ **Arquivo muito grande**: {file_size / (1024*1024):.1f}MB. Limite máximo: {Config.MAX_FILE_SIZE_MB}MB."
            
            if filename.endswith('.pdf'):
                return self._validate_pdf_format(file)
            elif filename.endswith('.docx'):
                return self._validate_docx_format(file)
            else:
                return False, "❌ **Formato não suportado**: Use apenas arquivos PDF ou DOCX."
                
        except Exception as e:
            logger.error(f"Erro na validação do arquivo: {str(e)}")
            return False, f"❌ **Erro na validação**: {str(e)}"
    
    def _validate_pdf_format(self, file: BinaryIO) -> Tuple[bool, str]:
        """
        Valida se o arquivo é um PDF válido.
        
        Args:
            file (BinaryIO): Arquivo PDF a ser validado
            
        Returns:
            Tuple[bool, str]: (é_válido, mensagem_erro)
        """
        try:
            # Volta o ponteiro para o início
            file.seek(0)
            
            # Lê os primeiros bytes para verificar o cabeçalho PDF
            header = file.read(4)
            file.seek(0)
            
            # Verifica se começa com %PDF
            if not header.startswith(b'%PDF'):
                return False, "❌ **Arquivo PDF inválido**: Este arquivo não é um PDF válido. Verifique se não é uma imagem de PDF ou arquivo corrompido."
            
            # Tenta criar um leitor PDF
            try:
                reader = PyPDF2.PdfReader(file)
                
                # Verifica se tem páginas
                if len(reader.pages) == 0:
                    return False, "❌ **PDF vazio**: O arquivo PDF não contém páginas."
                
                # Verifica limite de páginas
                if len(reader.pages) > Config.MAX_PAGES_PDF:
                    return False, f"❌ **PDF muito extenso**: {len(reader.pages)} páginas. Limite máximo: {Config.MAX_PAGES_PDF} páginas."
                
                # Tenta extrair texto da primeira página para verificar se não é só imagem
                first_page = reader.pages[0]
                text = first_page.extract_text()
                
                if not text or len(text.strip()) < 10:
                    return False, "⚠️ **PDF com pouco texto**: Este PDF parece conter principalmente imagens. Para melhor análise, use um PDF com texto selecionável."
                
                return True, f"✅ **PDF válido**: {len(reader.pages)} páginas, {len(text)} caracteres na primeira página."
                
            except PyPDF2.errors.PdfReadError as e:
                if "EOF" in str(e):
                    return False, "❌ **Arquivo PDF corrompido**: O arquivo está incompleto ou corrompido. Verifique se o upload foi concluído corretamente."
                elif "Invalid PDF" in str(e):
                    return False, "❌ **Arquivo PDF inválido**: Este arquivo não é um PDF válido. Pode ser uma imagem de PDF ou arquivo corrompido."
                else:
                    return False, f"❌ **Erro no PDF**: {str(e)}"
            except Exception as e:
                return False, f"❌ **Erro ao processar PDF**: {str(e)}"
                
        except Exception as e:
            return False, f"❌ **Erro na validação**: {str(e)}"
    
    def _validate_docx_format(self, file: BinaryIO) -> Tuple[bool, str]:
        """
        Valida se o arquivo é um DOCX válido.
        
        Args:
            file (BinaryIO): Arquivo DOCX a ser validado
            
        Returns:
            Tuple[bool, str]: (é_válido, mensagem_erro)
        """
        try:
            # Volta o ponteiro para o início
            file.seek(0)
            
            # Tenta abrir o documento DOCX
            try:
                doc = docx.Document(file)
                
                # Verifica se tem parágrafos
                if len(doc.paragraphs) == 0:
                    return False, "❌ **DOCX vazio**: O arquivo DOCX não contém conteúdo."
                
                # Verifica se tem texto
                text_content = ""
                for paragraph in doc.paragraphs:
                    text_content += paragraph.text
                
                if not text_content or len(text_content.strip()) < 10:
                    return False, "⚠️ **DOCX com pouco texto**: Este documento parece estar vazio ou conter muito pouco texto."
                
                # Verifica limite baseado em tokens estimados
                estimated_tokens = len(text_content) // 4
                if estimated_tokens > Config.AVAILABLE_CONTEXT_TOKENS:
                    return False, f"❌ **DOCX muito extenso**: ~{estimated_tokens:,} tokens estimados. Limite máximo: ~{Config.AVAILABLE_CONTEXT_TOKENS:,} tokens."
                
                return True, f"✅ **DOCX válido**: {len(doc.paragraphs)} parágrafos, {len(text_content):,} caracteres (~{estimated_tokens:,} tokens)."
                
            except Exception as e:
                if "BadZipFile" in str(e):
                    return False, "❌ **Arquivo DOCX inválido**: Este arquivo não é um DOCX válido. Pode estar corrompido ou ser um arquivo de outro formato."
                elif "Invalid file" in str(e):
                    return False, "❌ **Arquivo DOCX corrompido**: O arquivo está corrompido ou incompleto."
                else:
                    return False, f"❌ **Erro no DOCX**: {str(e)}"
                    
        except Exception as e:
            return False, f"❌ **Erro na validação**: {str(e)}"

    def extract_text(self, file: BinaryIO) -> str:
        """Extrai texto de arquivos PDF ou DOCX com validação"""
        try:
            filename = file.name.lower()
            if filename.endswith('.pdf'):
                text = self._extract_from_pdf(file)
            elif filename.endswith('.docx'):
                text = self._extract_from_docx(file)
            else:
                raise ValueError("Formato de arquivo não suportado")
            
            # Valida tamanho do texto extraído baseado em tokens
            estimated_tokens = len(text) // 4  # Aproximação: 4 chars = 1 token
            if estimated_tokens > Config.AVAILABLE_CONTEXT_TOKENS:
                logger.warning(f"Texto extraído excede limite: ~{estimated_tokens} tokens estimados")
                max_chars = Config.AVAILABLE_CONTEXT_TOKENS * 4
                text = text[:max_chars] + "\n\n[TEXTO TRUNCADO - LIMITE DE TOKENS ATINGIDO]"
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text from file: {str(e)}")
            raise

    def _extract_from_pdf(self, file: BinaryIO) -> str:
        reader = PyPDF2.PdfReader(file)
        return " ".join(page.extract_text() for page in reader.pages)

    def _extract_from_docx(self, file: BinaryIO) -> str:
        """Extrai texto de arquivo DOCX incluindo comentários e revisões"""
        try:
            doc = docx.Document(file)
            
            # Extrai texto principal
            main_text = self._extract_main_text(doc)
            
            # Extrai comentários
            comments_text = self._extract_comments(doc)
            
            # Extrai revisões
            revisions_text = self._extract_revisions(doc)
            
            # Combina todos os textos
            full_text = main_text
            if comments_text:
                full_text += f"\n\nCOMENTÁRIOS:\n{comments_text}"
            if revisions_text:
                full_text += f"\n\nREVISÕES:\n{revisions_text}"
            
            # Limpa o texto final
            cleaned_text = self._clean_text(full_text)
            
            logger.info(f"Texto extraído: {len(cleaned_text)} caracteres")
            logger.debug(f"Primeiros 200 caracteres: {cleaned_text[:200]}")
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Erro ao extrair texto do DOCX: {str(e)}")
            raise

    def _extract_main_text(self, doc: Document) -> str:
        """Extrai o texto principal do documento"""
        text_parts = []
        
        for element in doc.element.body:
            if isinstance(element, CT_P):
                # Parágrafo
                paragraph = Paragraph(element, doc)
                text = paragraph.text.strip()
                if text:
                    text_parts.append(text)
            elif isinstance(element, CT_Tbl):
                # Tabela
                table = Table(element, doc)
                table_text = self._extract_table_text(table)
                if table_text:
                    text_parts.append(table_text)
        
        return "\n".join(text_parts)

    def _extract_table_text(self, table: Table) -> str:
        """Extrai texto de tabelas"""
        table_texts = []
        for row in table.rows:
            row_texts = []
            for cell in row.cells:
                cell_text = cell.text.strip()
                if cell_text:
                    row_texts.append(cell_text)
            if row_texts:
                table_texts.append(" | ".join(row_texts))
        return "\n".join(table_texts)

    def _extract_comments(self, doc: Document) -> str:
        """Extrai o texto real dos comentários do documento DOCX de forma completa."""
        try:
            comments = []
            
            # Acessa o XML dos comentários
            if hasattr(doc, 'part') and hasattr(doc.part, 'package'):
                # Busca o arquivo de comentários
                comments_part = None
                for rel in doc.part.rels.values():
                    if rel.reltype == 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments':
                        comments_part = rel.target_part
                        break
                
                if comments_part:
                    from xml.etree import ElementTree as ET
                    comments_xml = ET.fromstring(comments_part.blob)
                    
                    # Mapeia id -> texto do comentário
                    comment_map = {}
                    for c in comments_xml.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}comment'):
                        cid = c.attrib.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
                        texts = [t.text for t in c.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if t.text]
                        comment_map[cid] = ' '.join(texts)
                    
                    # Busca comentários em TODOS os elementos do documento
                    def find_comments_in_element(element, context=""):
                        """Busca comentários recursivamente em qualquer elemento"""
                        element_comments = []
                        
                        # Procura por referências de comentário
                        comment_refs = element.findall('.//w:commentReference', 
                            namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
                        
                        for cref in comment_refs:
                            cid = cref.attrib.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
                            if cid and cid in comment_map:
                                # Encontra o elemento pai mais próximo (run ou paragraph)
                                parent = cref.getparent()
                                referenced_text = ""
                                
                                # Busca o texto no elemento pai e irmãos próximos
                                if parent is not None:
                                    # Coleta texto do elemento pai e seus irmãos
                                    siblings = parent.getparent().getchildren() if parent.getparent() is not None else [parent]
                                    
                                    for sibling in siblings:
                                        if sibling.tag.endswith('}r'):  # Run element
                                            text_elements = sibling.findall('.//w:t', 
                                                namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
                                            sibling_text = ' '.join([t.text for t in text_elements if t.text])
                                            if sibling_text.strip():
                                                referenced_text += sibling_text + " "
                                
                                # Se não encontrou texto específico, pega o texto do elemento pai
                                if not referenced_text.strip():
                                    text_elements = element.findall('.//w:t', 
                                        namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
                                    referenced_text = ' '.join([t.text for t in text_elements if t.text])
                                
                                if referenced_text.strip():
                                    element_comments.append({
                                        'text': referenced_text.strip(),
                                        'comment': comment_map[cid],
                                        'context': context
                                    })
                        
                        return element_comments
                    
                    # Busca em parágrafos
                    for i, paragraph in enumerate(doc.paragraphs):
                        if hasattr(paragraph, '_element') and paragraph._element is not None:
                            comments.extend(find_comments_in_element(paragraph._element, f"Parágrafo {i+1}"))
                    
                    # Busca em tabelas
                    for i, table in enumerate(doc.tables):
                        if hasattr(table, '_element') and table._element is not None:
                            comments.extend(find_comments_in_element(table._element, f"Tabela {i+1}"))
                    
                    # Busca em cabeçalhos e rodapés
                    for section in doc.sections:
                        if hasattr(section, 'header') and section.header:
                            for i, paragraph in enumerate(section.header.paragraphs):
                                if hasattr(paragraph, '_element') and paragraph._element is not None:
                                    comments.extend(find_comments_in_element(paragraph._element, f"Cabeçalho - Parágrafo {i+1}"))
                    
                    # Busca em rodapés
                    for section in doc.sections:
                        if hasattr(section, 'footer') and section.footer:
                            for i, paragraph in enumerate(section.footer.paragraphs):
                                if hasattr(paragraph, '_element') and paragraph._element is not None:
                                    comments.extend(find_comments_in_element(paragraph._element, f"Rodapé - Parágrafo {i+1}"))
                    
                    # Formata os comentários encontrados
                    formatted_comments = []
                    for i, comment_data in enumerate(comments, 1):
                        formatted_comments.append(
                            f"Comentário {i}:\n"
                            f"Localização: {comment_data['context']}\n"
                            f"Texto referenciado: \"{comment_data['text'][:200]}{'...' if len(comment_data['text']) > 200 else ''}\"\n"
                            f"Comentário: {comment_data['comment']}\n"
                        )
                    
                    return "\n" + "─" * 50 + "\n".join(formatted_comments) if formatted_comments else ""
            
            return ""
        except Exception as e:
            logger.warning(f"Erro ao extrair comentários: {str(e)}")
            return ""

    def _extract_revisions(self, doc: Document) -> str:
        """Extrai revisões do documento"""
        try:
            revisions = []
            for paragraph in doc.paragraphs:
                # Verifica se há revisões no parágrafo
                if hasattr(paragraph, '_element') and paragraph._element is not None:
                    # Procura por elementos de revisão
                    revision_elements = paragraph._element.findall('.//w:del', 
                                                                  namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
                    if revision_elements:
                        revisions.append(f"Revisão removida: {paragraph.text[:100]}...")
            
            return "\n".join(revisions) if revisions else ""
        except Exception as e:
            logger.warning(f"Erro ao extrair revisões: {str(e)}")
            return ""

    def _clean_text(self, text: str) -> str:
        """Limpa o texto removendo elementos de controle e normalizando"""
        if not text:
            return ""
        
        # Remove caracteres de controle
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Remove múltiplos espaços em branco
        text = re.sub(r'\s+', ' ', text)
        
        # Remove quebras de linha desnecessárias
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # Remove espaços no início e fim
        text = text.strip()
        
        # Normaliza aspas
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Remove caracteres especiais do Word
        text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)  # Zero-width spaces
        
        return text

    def extract_text_with_metadata(self, file: BinaryIO) -> dict:
        """Extrai texto com metadados sobre o processo de extração"""
        try:
            filename = file.name.lower()
            if filename.endswith('.docx'):
                doc = docx.Document(file)
                
                # Extrai texto principal
                main_text = self._extract_main_text(doc)
                
                # Conta elementos
                paragraph_count = len(doc.paragraphs)
                table_count = len(doc.tables)
                
                # Verifica se há comentários ou revisões
                has_comments = bool(self._extract_comments(doc))
                has_revisions = bool(self._extract_revisions(doc))
                
                # Limpa o texto
                cleaned_text = self._clean_text(main_text)
                
                return {
                    'text': cleaned_text,
                    'metadata': {
                        'paragraphs': paragraph_count,
                        'tables': table_count,
                        'has_comments': has_comments,
                        'has_revisions': has_revisions,
                        'original_length': len(main_text),
                        'cleaned_length': len(cleaned_text)
                    }
                }
            else:
                # Para outros formatos, retorna apenas o texto
                text = self.extract_text(file)
                return {
                    'text': text,
                    'metadata': {
                        'original_length': len(text),
                        'cleaned_length': len(text)
                    }
                }
                
        except Exception as e:
            logger.error(f"Erro ao extrair texto com metadados: {str(e)}")
            raise
