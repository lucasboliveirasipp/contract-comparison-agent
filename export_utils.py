import os
import base64
from datetime import datetime
from typing import Dict, List, Any
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

def export_to_word(analysis_data: Dict, analysis_type: str = "contract_analysis") -> BytesIO:
    """
    Exporta análise para formato Word (.docx)
    
    Args:
        analysis_data: Dados da análise
        analysis_type: Tipo de análise ("contract_analysis" ou "smart_analysis")
    
    Returns:
        BytesIO: Arquivo Word em memória
    """
    try:
        from docx import Document
        from docx.shared import Inches, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        
        doc = Document()
        
        # Cabeçalho
        header = doc.sections[0].header
        header_para = header.paragraphs[0]
        header_para.text = "Consultoria Jurídica - Análise de Contratos"
        header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Título principal
        title = doc.add_heading('Relatório de Análise de Contratos', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Data e hora
        doc.add_paragraph(f"Data da análise: {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
        doc.add_paragraph("")
        
        if analysis_type == "smart_analysis":
            _add_smart_analysis_content(doc, analysis_data)
        else:
            _add_contract_analysis_content(doc, analysis_data)
        
        # Rodapé
        footer = doc.sections[0].footer
        footer_para = footer.paragraphs[0]
        footer_para.text = f"Gerado automaticamente em {datetime.now().strftime('%d/%m/%Y')}"
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Salva em memória
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        logger.error(f"Erro ao exportar para Word: {str(e)}")
        raise

def export_to_pdf(analysis_data: Dict, analysis_type: str = "contract_analysis") -> BytesIO:
    """
    Exporta análise para formato PDF
    
    Args:
        analysis_data: Dados da análise
        analysis_type: Tipo de análise
    
    Returns:
        BytesIO: Arquivo PDF em memória
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1E3A8A')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#1E3A8A')
        )
        
        # Conteúdo
        story = []
        
        # Título
        story.append(Paragraph("Relatório de Análise de Contratos", title_style))
        story.append(Spacer(1, 12))
        
        # Data
        story.append(Paragraph(f"Data da análise: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        if analysis_type == "smart_analysis":
            _add_smart_analysis_pdf_content(story, analysis_data, styles, heading_style)
        else:
            _add_contract_analysis_pdf_content(story, analysis_data, styles, heading_style)
        
        doc.build(story)
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        logger.error(f"Erro ao exportar para PDF: {str(e)}")
        raise

def _add_smart_analysis_content(doc, analysis_data):
    """Adiciona conteúdo de análise inteligente ao Word"""
    from docx.shared import RGBColor
    from docx.enum.table import WD_TABLE_ALIGNMENT
    
    # Resumo
    doc.add_heading('Resumo da Análise', level=1)
    summary = analysis_data.get('summary', {})
    
    # Tabela de métricas
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Métrica'
    hdr_cells[1].text = 'Valor'
    
    metrics = [
        ('Total de Modificações', summary.get('total_modifications', 0)),
        ('Riscos Altos', summary.get('high_risk_count', 0)),
        ('Riscos Médios', summary.get('medium_risk_count', 0)),
        ('Riscos Baixos', summary.get('low_risk_count', 0)),
        ('Risco Geral', summary.get('overall_risk', 'N/A'))
    ]
    
    for metric, value in metrics:
        row_cells = table.add_row().cells
        row_cells[0].text = metric
        row_cells[1].text = str(value)
    
    doc.add_paragraph("")
    
    # Modificações detalhadas
    modifications = analysis_data.get('modifications', [])
    if modifications:
        doc.add_heading('Modificações Identificadas', level=1)
        
        for i, mod in enumerate(modifications, 1):
            doc.add_heading(f'Modificação {i}', level=2)
            doc.add_paragraph(f"Tipo: {mod.type}")
            doc.add_paragraph(f"Contexto: {mod.context}")
            doc.add_paragraph(f"Texto Original: {mod.original_text}")
            doc.add_paragraph(f"Texto Modificado: {mod.modified_text}")
            doc.add_paragraph(f"Impacto: {mod.impact}")
            doc.add_paragraph(f"Nível de Risco: {mod.risk_level}")
            doc.add_paragraph(f"Sugestão: {mod.suggestion}")
            doc.add_paragraph("")

def _add_contract_analysis_content(doc, analysis_data):
    """Adiciona conteúdo de análise de contratos ao Word"""
    doc.add_heading('Análise Comparativa vs Padrão Ouro', level=1)
    
    # Metadados
    metadata = analysis_data.get('metadata', {})
    if metadata:
        doc.add_heading('Informações da Análise', level=2)
        doc.add_paragraph(f"Tipo de análise: {metadata.get('analysis_type', 'N/A')}")
        doc.add_paragraph(f"Cláusulas padrão ouro consultadas: {metadata.get('padrao_ouro_clauses_count', 0)}")
        doc.add_paragraph(f"Caracteres do contrato da contratada: {metadata.get('contratada_text_length', 0):,}")
        doc.add_paragraph("")
    
    # Análise detalhada
    doc.add_heading('Análise Detalhada', level=2)
    analysis_text = analysis_data.get('analysis', 'Análise não disponível')
    
    # Divide o texto em parágrafos
    paragraphs = analysis_text.split('\n\n')
    for para in paragraphs:
        if para.strip():
            doc.add_paragraph(para.strip())

def _add_smart_analysis_pdf_content(story, analysis_data, styles, heading_style):
    """Adiciona conteúdo de análise inteligente ao PDF"""
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    
    # Resumo
    story.append(Paragraph("Resumo da Análise", heading_style))
    summary = analysis_data.get('summary', {})
    
    # Tabela de métricas
    data = [
        ['Métrica', 'Valor'],
        ['Total de Modificações', str(summary.get('total_modifications', 0))],
        ['Riscos Altos', str(summary.get('high_risk_count', 0))],
        ['Riscos Médios', str(summary.get('medium_risk_count', 0))],
        ['Riscos Baixos', str(summary.get('low_risk_count', 0))],
        ['Risco Geral', str(summary.get('overall_risk', 'N/A'))]
    ]
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Modificações
    modifications = analysis_data.get('modifications', [])
    if modifications:
        story.append(Paragraph("Modificações Identificadas", heading_style))
        
        for i, mod in enumerate(modifications, 1):
            story.append(Paragraph(f"Modificação {i}", styles['Heading3']))
            story.append(Paragraph(f"<b>Tipo:</b> {mod.type}", styles['Normal']))
            story.append(Paragraph(f"<b>Contexto:</b> {mod.context}", styles['Normal']))
            story.append(Paragraph(f"<b>Impacto:</b> {mod.impact}", styles['Normal']))
            story.append(Paragraph(f"<b>Nível de Risco:</b> {mod.risk_level}", styles['Normal']))
            story.append(Spacer(1, 12))

def _add_contract_analysis_pdf_content(story, analysis_data, styles, heading_style):
    """Adiciona conteúdo de análise de contratos ao PDF"""
    story.append(Paragraph("Análise Comparativa vs Padrão Ouro", heading_style))
    
    # Análise detalhada
    analysis_text = analysis_data.get('analysis', 'Análise não disponível')
    paragraphs = analysis_text.split('\n\n')
    
    for para in paragraphs:
        if para.strip():
            story.append(Paragraph(para.strip(), styles['Normal']))
            story.append(Spacer(1, 12))

def get_export_filename(analysis_type: str, file_format: str) -> str:
    """
    Gera nome do arquivo para exportação
    
    Args:
        analysis_type: Tipo de análise
        file_format: Formato do arquivo (word ou pdf)
    
    Returns:
        str: Nome do arquivo
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    type_name = "analise_contratos" if analysis_type == "contract_analysis" else "analise_modificacoes"
    extension = "docx" if file_format == "word" else "pdf"
    
    return f"{type_name}_{timestamp}.{extension}"