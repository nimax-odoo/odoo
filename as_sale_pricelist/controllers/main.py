#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import logging
from datetime import datetime
from odoo import http
from odoo.modules.module import get_module_path

_logger = logging.getLogger(__name__)

class AsSalePricelistController(http.Controller):
    """
    Controlador para el módulo as_sale_pricelist que proporciona
    rutas públicas para documentación y recursos.
    """
    
    def _as_log_request(self, endpoint, method, params):
        """
        Registra detalles de la solicitud entrante.
        
        Args:
            endpoint (str): URL del endpoint solicitado
            method (str): Método HTTP utilizado (GET, POST, etc.)
            params (dict): Parámetros de la solicitud
        """
        _logger.info(
            "[_as_log_request] Solicitud recibida - Endpoint: %s, Método: %s, Parámetros: %s",
            endpoint, method, params
        )
    
    def _as_log_response(self, endpoint, status_code, data):
        """
        Registra detalles de la respuesta enviada.
        
        Args:
            endpoint (str): URL del endpoint solicitado
            status_code (int): Código de estado HTTP
            data (dict): Datos de la respuesta
        """
        _logger.info(
            "[_as_log_response] Respuesta enviada - Endpoint: %s, Código: %s, Datos: %s",
            endpoint, status_code, data
        )
    
    @http.route('/nimax/as_sale_pricelist/pruebas', type='http', auth='public', methods=['GET'], website=True)
    def as_view_pruebas(self, **kwargs):
        """
        Endpoint público para visualizar la documentación de pruebas.
        
        Returns:
            Response: Página HTML con la documentación de pruebas formateada
        """
        _logger.info("[as_view_pruebas] Solicitud de visualización de la documentación de pruebas")
        self._as_log_request('/nimax/as_sale_pricelist/pruebas', 'GET', kwargs)
        
        try:
            # Obtener la ruta del archivo
            file_path = get_module_path('as_sale_pricelist', 'pruebas.md')
            
            if not file_path or not os.path.exists(file_path):
                _logger.error("[as_view_pruebas] Archivo de pruebas no encontrado: %s", file_path)
                
                return "<h1>Error</h1><p>Documentación de pruebas no encontrada.</p>"
                
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
                
                # Procesamiento adicional para mejorar las tablas y listas
                html_content = self._enhance_html_content(html_content)
                
            except ImportError as e:
                _logger.error("[as_view_pruebas] Error importando markdown: %s", str(e))
                # Si markdown no está instalado, mostrar texto plano con formato básico
                html_content = f"<pre>{markdown_content}</pre>"
                
            # Crear una página HTML completa con estilos
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Documentación de Pruebas - Módulo Listas de Precios</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    h1, h2, h3, h4, h5, h6 {{
                        color: #2c3e50;
                        margin-top: 24px;
                        margin-bottom: 16px;
                        font-weight: 600;
                    }}
                    h1 {{
                        font-size: 2em;
                        border-bottom: 1px solid #eaecef;
                        padding-bottom: .3em;
                    }}
                    h2 {{
                        font-size: 1.5em;
                        border-bottom: 1px solid #eaecef;
                        padding-bottom: .3em;
                    }}
                    a {{
                        color: #0366d6;
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
                    }}
                    code {{
                        background-color: rgba(27, 31, 35, .05);
                        border-radius: 3px;
                        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
                        padding: 0.2em 0.4em;
                        font-size: 85%;
                    }}
                    pre code {{
                        background-color: transparent;
                        padding: 0;
                    }}
                    blockquote {{
                        margin: 0;
                        padding: 0 1em;
                        color: #6a737d;
                        border-left: 0.25em solid #dfe2e5;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin-bottom: 20px;
                        font-size: 14px;
                        box-shadow: 0 2px 3px rgba(0,0,0,0.1);
                    }}
                    table th, table td {{
                        padding: 12px 15px;
                        border: 1px solid #dfe2e5;
                        text-align: left;
                        vertical-align: top;
                    }}
                    table th {{
                        background-color: #f2f2f2;
                        font-weight: bold;
                        color: #333;
                        position: sticky;
                        top: 0;
                        box-shadow: 0 1px 0 rgba(0,0,0,0.1);
                    }}
                    table tr {{
                        background-color: #fff;
                        border-top: 1px solid #c6cbd1;
                    }}
                    table tr:nth-child(2n) {{
                        background-color: #f8f8f8;
                    }}
                    table tr:hover {{
                        background-color: #f1f8ff;
                    }}
                    table td:nth-child(2):contains("Sí") {{
                        color: #d73a49;
                        font-weight: bold;
                    }}
                    table td:nth-child(2):contains("No") {{
                        color: #28a745;
                        font-weight: bold;
                    }}
                    img {{
                        max-width: 100%;
                    }}
                    hr {{
                        height: 0.25em;
                        padding: 0;
                        margin: 24px 0;
                        background-color: #e1e4e8;
                        border: 0;
                    }}
                    .header {{
                        background-color: #2c3e50;
                        color: white;
                        padding: 20px;
                        margin-bottom: 20px;
                        border-radius: 5px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    }}
                    .footer {{
                        margin-top: 50px;
                        padding-top: 20px;
                        border-top: 1px solid #eaecef;
                        text-align: center;
                        font-size: 0.8em;
                        color: #6a737d;
                    }}
                    /* Estilos específicos para tablas responsivas */
                    @media screen and (max-width: 768px) {{
                        table {{
                            display: block;
                            overflow-x: auto;
                            white-space: nowrap;
                        }}
                    }}
                    /* Estilo para pasos numerados */
                    ol {{
                        margin: 0;
                        padding-left: 20px;
                    }}
                    ol li {{
                        margin-bottom: 4px;
                    }}
                    strong {{
                        color: #0366d6;
                    }}
                    /* Tarjetas para problemas conocidos */
                    .problem-card {{
                        border-left: 4px solid #d73a49;
                        background-color: #fff8f8;
                        padding: 10px 15px;
                        margin-bottom: 10px;
                        border-radius: 0 3px 3px 0;
                    }}
                    .problem-card strong {{
                        color: #d73a49;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1 style="color: white; border-bottom: none; margin: 0;">Documentación de Pruebas - Módulo Listas de Precios</h1>
                    <p style="margin: 0; margin-top: 10px;">Ahorasoft - Documentación oficial</p>
                </div>
                
                {html_content}
                
                <div class="footer">
                    <p>© {datetime.now().year} Ahorasoft. Todos los derechos reservados.</p>
                    <p>http://www.ahorasoft.com</p>
                </div>
            </body>
            </html>
            """
            
            _logger.info("[as_view_pruebas] Documentación de pruebas servida correctamente")
            self._as_log_response('/nimax/as_sale_pricelist/pruebas', 200, {'status': 'success'})
            
            return html
            
        except Exception as e:
            _logger.error("[as_view_pruebas] Error al servir la documentación: %s", str(e))
            
            return f"<h1>Error</h1><p>No se pudo cargar la documentación de pruebas: {str(e)}</p>"
            
    def _enhance_html_content(self, html_content):
        """
        Mejora el contenido HTML generado para hacerlo más atractivo y funcional.
        
        Args:
            html_content (str): Contenido HTML generado por markdown
            
        Returns:
            str: Contenido HTML mejorado
        """
        import re
        
        # Mejorar los elementos numerados en las celdas de tabla
        for i in range(1, 10):
            html_content = html_content.replace(f"{i}. ", f"<strong>{i}.</strong> ")
        
        # Crear tarjetas para los problemas conocidos
        pattern = r'<li><p><strong>(Problema.+?)</strong>:(.*?)</p></li>'
        replacement = r'<li><div class="problem-card"><strong>\1</strong>:\2</div></li>'
        html_content = re.sub(pattern, replacement, html_content, flags=re.DOTALL)
        
        # Resaltar los "Sí" y "No" en la columna de sospecha
        html_content = html_content.replace('>Sí<', '><span style="color: #d73a49; font-weight: bold;">Sí</span><')
        html_content = html_content.replace('>No<', '><span style="color: #28a745; font-weight: bold;">No</span><')
        
        # Mejorar la visibilidad de las tablas
        html_content = html_content.replace('<table>', '<table class="enhanced-table">')
        
        # Convertir todos los nombres de funcionalidades a negrita y color
        pattern = r'<td><strong>(.+?)</strong></td>'
        replacement = r'<td><strong style="color: #0366d6;">\1</strong></td>'
        html_content = re.sub(pattern, replacement, html_content)
        
        return html_content 