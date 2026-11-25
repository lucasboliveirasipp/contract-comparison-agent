"""
Script de teste para verificar extração de comentários de arquivos DOCX
"""
import pytest
import sys
import os
from document_processor import DocumentProcessor

# Cria uma fixture que fornece o caminho do arquivo para o teste
@pytest.fixture
def file_path():
    # Cria um arquivo dummy ou retorna o caminho de um PDF de teste existente
    # Se você tiver um PDF de teste na pasta, coloque o nome dele aqui
    return "contrato_teste.pdf"

def test_comment_extraction(file_path):
    """Testa a extração de comentários de um arquivo DOCX"""
    print(f"🔍 Testando extração de comentários: {file_path}")
    print("=" * 60)
    
    try:
        # Inicializa o processador
        processor = DocumentProcessor()
        
        # Abre o arquivo
        with open(file_path, 'rb') as file:
            # Extrai texto completo (incluindo comentários)
            full_text = processor.extract_text(file)
            
            # Extrai apenas comentários
            file.seek(0)  # Volta ao início do arquivo
            doc = processor._extract_from_docx(file)
            
            # Análise do resultado
            print(f"📄 Tamanho do texto extraído: {len(full_text)} caracteres")
            
            # Verifica se há comentários
            if "COMENTÁRIOS:" in full_text:
                print("✅ Comentários detectados no texto extraído!")
                
                # Extrai seção de comentários
                comments_section = full_text.split("COMENTÁRIOS:")[1]
                if "REVISÕES:" in comments_section:
                    comments_section = comments_section.split("REVISÕES:")[0]
                
                print(f"📝 Seção de comentários encontrada ({len(comments_section)} caracteres)")
                print("\n--- COMENTÁRIOS EXTRAÍDOS ---")
                print(comments_section.strip())
                print("--- FIM DOS COMENTÁRIOS ---")
                
                # Conta comentários
                comment_count = comments_section.count("Comentário em:")
                print(f"🔢 Número de comentários encontrados: {comment_count}")
                
            else:
                print("❌ Nenhum comentário detectado no texto extraído")
            
            # Verifica se há revisões
            if "REVISÕES:" in full_text:
                print("✅ Revisões detectadas no texto extraído!")
            else:
                print("ℹ️  Nenhuma revisão detectada")
                
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()

def test_with_sample_files():
    """Testa com arquivos de exemplo"""
    print(" Resumo dos Comentários ")
    print("=" * 60)
    
    # Lista arquivos DOCX no diretório atual
    docx_files = [f for f in os.listdir('.') if f.endswith('.docx')]
    
    if not docx_files:
        print("❌ Nenhum arquivo .docx encontrado no diretório atual")
        print("💡 Dica: Coloque um arquivo .docx com comentários no mesmo diretório deste script")
        return
    
    print(f"📁 Arquivos .docx encontrados: {docx_files}")
    
    for file_path in docx_files:
        test_comment_extraction(file_path)
        print("\n" + "=" * 60 + "\n")

def create_test_document():
    """Cria um documento de teste com comentários (se python-docx estiver disponível)"""
    try:
        import docx
        from docx import Document
        
        print("📝 Criando documento de teste com comentários...")
        
        # Cria documento
        doc = Document()
        
        # Adiciona parágrafo
        p = doc.add_paragraph("Este é um parágrafo de teste.")
        
        # Adiciona comentário (simulado)
        comment = doc.add_comment("Este é um comentário de teste!", author="Teste")
        
        # Salva documento
        test_file = "teste_comentarios.docx"
        doc.save(test_file)
        
        print(f"✅ Documento de teste criado: {test_file}")
        print("💡 Nota: Comentários podem não aparecer devido a limitações da biblioteca python-docx")
        
        return test_file
        
    except ImportError:
        print("❌ python-docx não disponível para criar documento de teste")
        return None
    except Exception as e:
        print(f"❌ Erro ao criar documento de teste: {str(e)}")
        return None

if __name__ == "__main__":
    print("🚀 INICIANDO TESTES DE EXTRAÇÃO DE COMENTÁRIOS")
    print("=" * 60)
    
    # Testa com arquivos existentes
    test_with_sample_files()
    
    # Se não houver arquivos, tenta criar um de teste
    if not any(f.endswith('.docx') for f in os.listdir('.')):
        print("📝 Criando documento de teste...")
        test_file = create_test_document()
        if test_file:
            test_comment_extraction(test_file)
    
    print("✅ Testes concluídos!") 


    