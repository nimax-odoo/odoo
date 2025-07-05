#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import logging
from datetime import datetime
from odoo import http
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)

class AsMxInvoiceController(http.Controller):
    """
    Controlador para el módulo as_mx_invoice que proporciona
    rutas públicas para documentación de cancelación SAT.
    """
    
    def _as_log_request(self, endpoint, method, params):
        """
        Propósito: Registra detalles de la solicitud entrante
        Parámetros: endpoint (URL), method (HTTP), params (solicitud)
        Retorno: Log de información de la solicitud
        """
        _logger.info(
            "[_as_log_request] Solicitud recibida - Endpoint: %s, Método: %s, Parámetros: %s",
            endpoint, method, params
        )
    
    def _as_log_response(self, endpoint, status_code, data):
        """
        Propósito: Registra detalles de la respuesta enviada
        Parámetros: endpoint (URL), status_code (HTTP), data (respuesta)
        Retorno: Log de información de la respuesta
        """
        _logger.info(
            "[_as_log_response] Respuesta enviada - Endpoint: %s, Código: %s, Datos: %s",
            endpoint, status_code, data
        )
    
    @http.route('/nimax/as_mx_invoice/cancelacion_sat', type='http', auth='public', methods=['GET'], website=True)
    def as_view_cancelacion_sat(self, **kwargs):
        """
        Propósito: Endpoint público para visualizar la guía de motivos de cancelación SAT
        Parámetros: kwargs (parámetros de la URL)
        Retorno: Página HTML con la guía de cancelación SAT formateada
        """
        _logger.info("[as_view_cancelacion_sat] Solicitud de visualización de la guía de cancelación SAT")
        self._as_log_request('/nimax/as_mx_invoice/cancelacion_sat', 'GET', kwargs)
        
        try:
            # Obtener la ruta del archivo
            file_path = get_module_resource('as_mx_invoice', 'cancelacion_SAT.md')
            
            if not file_path or not os.path.exists(file_path):
                _logger.error("[as_view_cancelacion_sat] Archivo de cancelación SAT no encontrado: %s", file_path)
                
                return "<h1>Error</h1><p>Guía de cancelación SAT no encontrada.</p>"
                
            # Leer el contenido del archivo
            with open(file_path, 'r', encoding='utf-8') as file:
                markdown_content = file.read()
                
            # Convertir Markdown a HTML
            try:
                import markdown
                from markdown.extensions.tables import TableExtension
                
                # Usar la extensión específica para tablas con opciones avanzadas
                html_content = markdown.markdown(
                    markdown_content, 
                    extensions=[
                        TableExtension(use_align_attribute=True),
                        'fenced_code', 
                        'codehilite',
                        'nl2br'  # Convertir saltos de línea en <br>
                    ]
                )
                
                # Procesamiento adicional para mejorar las tablas y contenido fiscal
                html_content = self._enhance_sat_content(html_content)
                
            except ImportError as e:
                _logger.error("[as_view_cancelacion_sat] Error importando markdown: %s", str(e))
                # Si markdown no está instalado, mostrar texto plano con formato básico
                html_content = f"<pre>{markdown_content}</pre>"
                
            # Crear una página HTML completa con estilos específicos para SAT
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Guía de Motivos de Cancelación SAT - CFDI México</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f8f9fa;
                        text-align: left;
                    }}
                    h1, h2, h3, h4, h5, h6 {{
                        color: #006400;
                        margin-top: 24px;
                        margin-bottom: 16px;
                        font-weight: 600;
                    }}
                    
                    /* Títulos con texto blanco para fondos oscuros */
                    .titulo-blanco {{
                        color: #FFFFFF !important;
                        background: linear-gradient(135deg, #006400, #228B22);
                        padding: 15px 20px;
                        border-radius: 8px;
                        box-shadow: 0 3px 10px rgba(0,100,0,0.3);
                        margin: 20px 0;
                        font-weight: bold;
                        text-align: center !important;
                        border: none;
                        display: block;
                    }}
                    
                    .titulo-blanco h1, .titulo-blanco h2, .titulo-blanco h3, 
                    .titulo-blanco h4, .titulo-blanco h5, .titulo-blanco h6 {{
                        color: #FFFFFF !important;
                        margin: 0;
                        padding: 0;
                        border: none;
                        background: none;
                    }}
                    
                    /* Variantes de títulos */
                    .titulo-verde-oscuro {{
                        color: #FFFFFF !important;
                        background: linear-gradient(135deg, #2F4F2F, #006400);
                        padding: 12px 18px;
                        border-radius: 6px;
                        margin: 15px 0;
                        font-weight: 600;
                        text-align: center !important;
                    }}
                    
                    .titulo-destacado {{
                        color: #FFFFFF !important;
                        background: linear-gradient(135deg, #228B22, #32CD32);
                        padding: 10px 15px;
                        border-radius: 5px;
                        margin: 10px 0;
                        font-weight: 500;
                        text-align: center !important;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    }}
                    h1 {{
                        font-size: 2em;
                        border-bottom: 2px solid #006400;
                        padding-bottom: .3em;
                    }}
                    h2 {{
                        font-size: 1.5em;
                        border-bottom: 1px solid #006400;
                        padding-bottom: .3em;
                        background: linear-gradient(135deg, #006400, #228B22);
                        color: white;
                        padding: 15px;
                        border-radius: 5px;
                        margin-top: 30px;
                    }}
                    a {{
                        color: #006400;
                        text-decoration: none;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                    pre {{
                        background-color: #f6f8fa;
                        border-radius: 3px;
                        padding: 16px;
                        overflow: auto;
                        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
                        border-left: 4px solid #006400;
                    }}
                    code {{
                        background-color: rgba(0, 100, 0, .1);
                        border-radius: 3px;
                        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
                        padding: 0.2em 0.4em;
                        font-size: 85%;
                        color: #006400;
                    }}
                    pre code {{
                        background-color: transparent;
                        padding: 0;
                    }}
                    blockquote {{
                        margin: 0;
                        padding: 0 1em;
                        color: #6a737d;
                        border-left: 0.25em solid #006400;
                        background-color: #f0fff0;
                        border-radius: 0 5px 5px 0;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin-bottom: 20px;
                        font-size: 14px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        background-color: white;
                        border-radius: 8px;
                        overflow: hidden;
                    }}
                    table th, table td {{
                        padding: 12px 15px;
                        border: 1px solid #dfe2e5;
                        text-align: left !important;
                        vertical-align: top;
                    }}
                    table th {{
                        background: linear-gradient(135deg, #006400, #228B22);
                        color: white;
                        font-weight: bold;
                        position: sticky;
                        top: 0;
                        box-shadow: 0 2px 2px rgba(0,0,0,0.1);
                    }}
                    table tr {{
                        background-color: #fff;
                        border-top: 1px solid #c6cbd1;
                    }}
                    table tr:nth-child(2n) {{
                        background-color: #f8f8f8;
                    }}
                    table tr:hover {{
                        background-color: #f0fff0;
                        transform: scale(1.01);
                        transition: all 0.2s ease;
                    }}
                    img {{
                        max-width: 100%;
                    }}
                    hr {{
                        height: 0.25em;
                        padding: 0;
                        margin: 24px 0;
                        background: linear-gradient(135deg, #006400, #228B22);
                        border: 0;
                        border-radius: 2px;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #006400, #228B22);
                        color: white;
                        padding: 30px;
                        margin-bottom: 30px;
                        border-radius: 10px;
                        box-shadow: 0 4px 15px rgba(0,100,0,0.3);
                        text-align: center;
                    }}
                    .header * {{
                        text-align: center;
                    }}
                    .footer {{
                        margin-top: 50px;
                        padding-top: 20px;
                        border-top: 2px solid #006400;
                        text-align: center;
                        font-size: 0.9em;
                        color: #6a737d;
                        background-color: white;
                        border-radius: 10px;
                        padding: 20px;
                    }}
                    .footer * {{
                        text-align: center;
                    }}
                    /* Tarjetas para motivos SAT */
                    .motivo-card {{
                        border-left: 6px solid #006400;
                        background: linear-gradient(135deg, #fff, #f0fff0);
                        padding: 20px;
                        margin: 20px 0;
                        border-radius: 0 10px 10px 0;
                        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                    }}
                    .motivo-01 {{ border-left-color: #228B22; }}
                    .motivo-02 {{ border-left-color: #32CD32; }}
                    .motivo-03 {{ border-left-color: #006400; }}
                    .motivo-04 {{ border-left-color: #2E8B57; }}
                    
                    .alert-box {{
                        background-color: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-left: 4px solid #f39c12;
                        color: #856404;
                        padding: 15px;
                        margin: 15px 0;
                        border-radius: 5px;
                    }}
                    
                    .risk-high {{
                        background-color: #f8d7da;
                        border-left: 4px solid #dc3545;
                        color: #721c24;
                    }}
                    
                    .risk-low {{
                        background-color: #d4edda;
                        border-left: 4px solid #28a745;
                        color: #155724;
                    }}
                    
                    /* Alineación de listas y párrafos */
                    ul, ol {{
                        text-align: left !important;
                        padding-left: 20px;
                        margin-left: 0;
                        list-style-position: outside;
                    }}
                    
                    li {{
                        text-align: left !important;
                        margin-bottom: 5px;
                        display: list-item;
                    }}
                    
                    p {{
                        text-align: left !important;
                        margin: 10px 0;
                    }}
                    
                    div {{
                        text-align: left !important;
                    }}
                    
                    .content {{
                        text-align: left !important;
                    }}
                    
                    * {{
                        text-align: left !important;
                    }}
                    
                    .header, .header *, .footer, .footer * {{
                        text-align: center !important;
                    }}
                    
                    /* Estilos responsivos */
                    @media screen and (max-width: 768px) {{
                        body {{ padding: 10px; }}
                        table {{ font-size: 12px; }}
                        .header {{ padding: 20px; }}
                        h2 {{ font-size: 1.3em; }}
                        ul, ol {{ padding-left: 15px; }}
                    }}
                    
                    /* Iconos SAT */
                    .sat-icon {{
                        display: inline-block;
                        width: 20px;
                        height: 20px;
                        margin-right: 8px;
                        vertical-align: middle;
                    }}
                    
                    strong {{
                        color: #000000;
                        font-weight: 600;
                    }}
                    
                    /* Highlighting para proceso fiscal */
                    .proceso-fiscal {{
                        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                        border: 2px solid #006400;
                        border-radius: 10px;
                        padding: 20px;
                        margin: 20px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1 style="color: white; border-bottom: none; margin: 0; font-size: 2.5em;">🇲🇽 GUÍA OFICIAL SAT</h1>
                    <h2 style="color: white; border-bottom: none; margin: 10px 0 0 0; background: none; padding: 0; font-size: 1.5em;">Motivos de Cancelación de CFDI</h2>
                    <p style="margin: 15px 0 0 0; font-size: 1.1em; opacity: 0.9;">Ahorasoft - Documentación Contable Especializada</p>
                </div>
                
                <div class="content">
                {html_content}
                </div>
                
                <div class="footer">
                    <p><strong>© {datetime.now().year} Ahorasoft</strong></p>
                    <p>Documentación Contable Especializada | Compatible SAT {datetime.now().year}</p>
                    <p style="font-size: 0.8em; margin-top: 10px;">
                        📋 Esta documentación cumple con las disposiciones fiscales vigentes del SAT<br>
                        ⚖️ Información actualizada conforme a la normatividad mexicana
                    </p>
                </div>
            </body>
            </html>
            """
            
            _logger.info("[as_view_cancelacion_sat] Guía de cancelación SAT servida correctamente")
            self._as_log_response('/nimax/as_mx_invoice/cancelacion_sat', 200, {'status': 'success'})
            
            return html
            
        except Exception as e:
            _logger.error("[as_view_cancelacion_sat] Error al servir la guía de cancelación SAT: %s", str(e))
            
            return f"""
            <h1>Error del Sistema</h1>
            <p>No se pudo cargar la guía de cancelación SAT: {str(e)}</p>
            <p>Por favor contacte al administrador del sistema.</p>
            """
            
    def _enhance_sat_content(self, html_content):
        """
        Propósito: Mejora el contenido HTML para hacerlo más específico para documentación SAT
        Parámetros: html_content (contenido HTML generado por markdown)
        Retorno: Contenido HTML mejorado con estilos SAT específicos
        """
        import re
        
        # Resaltar motivos SAT específicos
        html_content = html_content.replace('**01**', '<span style="background-color: #228B22; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;">01</span>')
        html_content = html_content.replace('**02**', '<span style="background-color: #32CD32; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;">02</span>')
        html_content = html_content.replace('**03**', '<span style="background-color: #006400; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;">03</span>')
        html_content = html_content.replace('**04**', '<span style="background-color: #2E8B57; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;">04</span>')
        
        # Agregar iconos a elementos específicos
        html_content = html_content.replace('✅', '<span style="color: #28a745; font-size: 1.2em;">✅</span>')
        html_content = html_content.replace('❌', '<span style="color: #dc3545; font-size: 1.2em;">❌</span>')
        html_content = html_content.replace('⚠️', '<span style="color: #ffc107; font-size: 1.2em;">⚠️</span>')
        html_content = html_content.replace('🔍', '<span style="color: #6f42c1; font-size: 1.2em;">🔍</span>')
        html_content = html_content.replace('📋', '<span style="color: #007bff; font-size: 1.2em;">📋</span>')
        html_content = html_content.replace('💼', '<span style="color: #6c757d; font-size: 1.2em;">💼</span>')
        html_content = html_content.replace('📊', '<span style="color: #20c997; font-size: 1.2em;">📊</span>')
        html_content = html_content.replace('🚀', '<span style="color: #fd7e14; font-size: 1.2em;">🚀</span>')
        html_content = html_content.replace('💰', '<span style="color: #ffc107; font-size: 1.2em;">💰</span>')
        html_content = html_content.replace('🎯', '<span style="color: #e83e8c; font-size: 1.2em;">🎯</span>')
        
        # Resaltar términos fiscales importantes
        fiscal_terms = [
            'CFDI', 'SAT', 'RFC', 'UUID', 'Folio Fiscal', 'PAC', 'IVA', 'ISR', 'IEPS'
        ]
        
        for term in fiscal_terms:
            pattern = f'\\b{re.escape(term)}\\b'
            replacement = f'<strong style="color: #006400; background-color: #f0fff0; padding: 1px 3px; border-radius: 2px;">{term}</strong>'
            html_content = re.sub(pattern, replacement, html_content)
        
        # Envolver alertas importantes en cajas especiales
        html_content = html_content.replace('<p><strong>⚠️ IMPORTANTE', '<div class="alert-box risk-high"><strong>⚠️ IMPORTANTE')
        html_content = html_content.replace('</strong></p>', '</strong></div>')
        
        # Crear tarjetas para cada motivo
        html_content = re.sub(
            r'<h2>([^<]*MOTIVO 0[1-4][^<]*)</h2>',
            r'<h2 class="motivo-card">\1</h2>',
            html_content
        )
        
        # Aplicar estilos de títulos blancos a secciones importantes
        html_content = re.sub(
            r'<h2>([^<]*MEJORES PRÁCTICAS[^<]*)</h2>',
            r'<div class="titulo-blanco"><h2>\1</h2></div>',
            html_content
        )
        
        html_content = re.sub(
            r'<h3>([^<]*IMPORTANTE[^<]*)</h3>',
            r'<div class="titulo-verde-oscuro"><h3>\1</h3></div>',
            html_content
        )
        
        html_content = re.sub(
            r'<h3>([^<]*RECOMENDACIONES[^<]*)</h3>',
            r'<div class="titulo-destacado"><h3>\1</h3></div>',
            html_content
        )
        
        # Aplicar estilo blanco a títulos que contengan ciertas palabras clave
        keywords_titulo_blanco = ['CONTABLES', 'FISCALES', 'PROCESO', 'PROCEDIMIENTO']
        for keyword in keywords_titulo_blanco:
            pattern = f'<h([1-6])>([^<]*{keyword}[^<]*)</h[1-6]>'
            replacement = r'<div class="titulo-blanco"><h\1>\2</h\1></div>'
            html_content = re.sub(pattern, replacement, html_content, flags=re.IGNORECASE)
        
        return html_content 