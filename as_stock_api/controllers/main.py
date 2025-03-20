# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

import json
import logging
import os
from datetime import datetime
from odoo import http, _
from odoo.http import request, Response
from odoo.exceptions import AccessError, ValidationError
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)

class AsStockAPI(http.Controller):
    """
    Controlador para la API de consulta de stock.
    Proporciona un endpoint REST para consultar la disponibilidad de stock
    de manera segura y optimizada.
    """

    def _as_validate_api_key(self, api_key):
        """
        Valida la clave API proporcionada contra las almacenadas en los usuarios.
        
        Args:
            api_key (str): Clave API a validar
            
        Returns:
            res.users: Usuario asociado a la clave API, False si no es válida
        """
        if not api_key:
            return False
            
        user = request.env['res.users'].sudo().search([
            ('as_api_key', '=', api_key),
            ('as_api_enabled', '=', True),
            ('active', '=', True)
        ], limit=1)
        
        return user if user else False
        
    def _as_check_permissions(self, user):
        """
        Verifica que el usuario tenga permisos para leer el modelo stock.quant.
        
        Args:
            user (res.users): Usuario a verificar
            
        Returns:
            bool: True si tiene permisos, False en caso contrario
        """
        try:
            # Cambiar al entorno del usuario para verificar permisos
            user_env = request.env(user=user.id)
            user_env['stock.quant'].check_access_rights('read')
            return True
        except AccessError:
            return False
    
    def _as_log_request(self, endpoint, method, params, user=None):
        """
        Registra los detalles de una solicitud entrante.
        
        Args:
            endpoint (str): Endpoint solicitado
            method (str): Método HTTP
            params (dict): Parámetros de la solicitud
            user (res.users, opcional): Usuario autenticado
        """
        # Crear una copia de los parámetros para no modificar el original
        safe_params = params.copy() if params else {}
        
        # Ocultar la API key en los logs por seguridad
        if 'api_key' in safe_params:
            safe_params['api_key'] = '***HIDDEN***'
            
        log_data = {
            'endpoint': endpoint,
            'method': method,
            'params': safe_params,
            'user_id': user.id if user else None,
            'user_name': user.name if user else None,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ip': request.httprequest.remote_addr,
            'user_agent': request.httprequest.user_agent.string if request.httprequest.user_agent else None
        }
        
        _logger.info("[as_log_request] Solicitud recibida: %s", json.dumps(log_data, default=str))
        
    def _as_log_response(self, endpoint, status_code, response_data, user=None):
        """
        Registra los detalles de una respuesta saliente.
        
        Args:
            endpoint (str): Endpoint solicitado
            status_code (int): Código de estado HTTP
            response_data (dict/list): Datos de la respuesta
            user (res.users, opcional): Usuario autenticado
        """
        # Limitar el tamaño de los datos de respuesta en el log
        if isinstance(response_data, list) and len(response_data) > 5:
            log_response = response_data[:5]
            log_response.append(f"... y {len(response_data) - 5} registros más")
        else:
            log_response = response_data
            
        log_data = {
            'endpoint': endpoint,
            'status_code': status_code,
            'response': log_response,
            'user_id': user.id if user else None,
            'user_name': user.name if user else None,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        _logger.info("[as_log_response] Respuesta enviada: %s", json.dumps(log_data, default=str))
            
    # Mantener el endpoint GET por compatibilidad, pero marcarlo como obsoleto
    @http.route('/nimax/stock', type='http', auth='none', methods=['GET'], csrf=False)
    def as_get_stock_deprecated(self, **kwargs):
        """
        Endpoint obsoleto para consultar el stock disponible.
        Se mantiene por compatibilidad pero se recomienda usar el método POST.
        
        Returns:
            Response: Respuesta HTTP con mensaje de advertencia
        """
        _logger.warning("[as_get_stock_deprecated] Uso de método GET obsoleto para consultar stock")
        
        self._as_log_request('/nimax/stock', 'GET', kwargs)
        
        response_data = {
            'warning': 'El método GET está obsoleto para este endpoint. Por favor, use POST para mayor seguridad.',
            'migration_guide': 'Cambie el método HTTP a POST y envíe los parámetros en el cuerpo de la solicitud.'
        }
        
        self._as_log_response('/nimax/stock', 200, response_data)
        
        return Response(
            json.dumps(response_data),
            status=200,
            content_type='application/json'
        )
            
    @http.route('/nimax/stock', type='json', auth='none', methods=['POST'], csrf=False)
    def as_get_stock(self, **kwargs):
        """
        Endpoint para consultar el stock disponible.
        
        Args en el cuerpo JSON:
            default_code (str, opcional): Código del producto a filtrar
            location_id (int, opcional): ID de la ubicación a filtrar
            api_key (str, obligatorio): Clave API para autenticación
            
        Returns:
            dict: Datos de stock en formato JSON o mensaje de error
        """
        # Obtener los parámetros del cuerpo JSON
        params = request.jsonrequest or {}
        
        _logger.info("[as_get_stock] Recibida solicitud POST de consulta de stock")
        self._as_log_request('/nimax/stock', 'POST', params)
        
        # Verificar autenticación por API key
        api_key = params.get('api_key')
        if not api_key:
            _logger.warning("[as_get_stock] Intento de acceso sin API key")
            
            response_data = {'error': 'Se requiere API key'}
            self._as_log_response('/nimax/stock', 401, response_data)
            
            return Response(
                json.dumps(response_data),
                status=401,
                content_type='application/json'
            )
            
        user = self._as_validate_api_key(api_key)
        if not user:
            _logger.warning("[as_get_stock] Intento de acceso con API key inválida")
            
            response_data = {'error': 'API key inválida'}
            self._as_log_response('/nimax/stock', 403, response_data)
            
            return Response(
                json.dumps(response_data),
                status=403,
                content_type='application/json'
            )
        
        # Verificar permisos de usuario
        if not self._as_check_permissions(user):
            _logger.warning("[as_get_stock] Usuario %s sin permisos para acceder a stock.quant", user.name)
            
            response_data = {'error': 'No tiene permisos para acceder a esta información'}
            self._as_log_response('/nimax/stock', 403, response_data, user)
            
            return Response(
                json.dumps(response_data),
                status=403,
                content_type='application/json'
            )
            
        # Obtener parámetros de filtrado
        default_code = params.get('default_code')
        location_id = params.get('location_id')
        
        # Compatibilidad con versiones anteriores
        product_id = params.get('product_id')
        if product_id and not default_code:
            _logger.warning("[as_get_stock] Uso de parámetro obsoleto product_id: %s", product_id)
            
            response_data = {
                'warning': 'El parámetro product_id está obsoleto. Por favor, use default_code en su lugar.',
                'migration_guide': 'Cambie el parámetro product_id por default_code en el cuerpo de la solicitud.'
            }
            self._as_log_response('/nimax/stock', 200, response_data, user)
        
        # Construir dominio de búsqueda
        domain = []
        
        # Filtrar por código de producto si se proporciona
        if default_code:
            # Buscar el producto por su código
            product = request.env['product.product'].sudo().search([('default_code', '=', default_code)], limit=1)
            if not product:
                _logger.warning("[as_get_stock] Código de producto no encontrado: %s", default_code)
                
                response_data = {'error': f'Producto con código {default_code} no encontrado'}
                self._as_log_response('/nimax/stock', 404, response_data, user)
                
                return Response(
                    json.dumps(response_data),
                    status=404,
                    content_type='application/json'
                )
                
            domain.append(('product_id', '=', product.id))
        # Compatibilidad con versiones anteriores
        elif product_id:
            try:
                product_id = int(product_id)
                domain.append(('product_id', '=', product_id))
            except (ValueError, TypeError):
                _logger.warning("[as_get_stock] Parámetro product_id inválido: %s", product_id)
                
                response_data = {'error': 'Parámetro product_id inválido'}
                self._as_log_response('/nimax/stock', 400, response_data, user)
                
                return Response(
                    json.dumps(response_data),
                    status=400,
                    content_type='application/json'
                )
                
        if location_id:
            try:
                location_id = int(location_id)
                domain.append(('location_id', '=', location_id))
            except (ValueError, TypeError):
                _logger.warning("[as_get_stock] Parámetro location_id inválido: %s", location_id)
                
                response_data = {'error': 'Parámetro location_id inválido'}
                self._as_log_response('/nimax/stock', 400, response_data, user)
                
                return Response(
                    json.dumps(response_data),
                    status=400,
                    content_type='application/json'
                )
        
        # Solo considerar ubicaciones internas (tipo = internal)
        domain.append(('location_id.usage', '=', 'internal'))
        
        try:
            # Cambiar al entorno del usuario para la consulta
            user_env = request.env(user=user.id)
            
            # Consultar stock.quant con optimización de campos
            quants = user_env['stock.quant'].search_read(
                domain=domain,
                fields=[
                    'product_id', 
                    'location_id', 
                    'quantity', 
                    'reserved_quantity',
                    'write_date'
                ],
                order='write_date desc'
            )
            
            # Preparar respuesta simplificada
            result = []
            
            # Diccionario para agrupar por ubicación y código de producto
            grouped_data = {}
            
            for quant in quants:
                product = request.env['product.product'].sudo().browse(quant['product_id'][0])
                available_qty = quant['quantity'] - quant['reserved_quantity']
                
                # Crear clave única para agrupar
                location_name = quant['location_id'][1]
                product_code = product.default_code or ''
                product_name = quant['product_id'][1]
                key = f"{location_name}_{product_code}"
                
                # Agrupar sumando cantidades
                if key in grouped_data:
                    grouped_data[key]['stock'] += available_qty
                else:
                    grouped_data[key] = {
                        'location': location_name,
                        'product_code': product_code,
                        'product_name': product_name,
                        'stock': available_qty,
                    }
            
            # Convertir el diccionario agrupado a lista
            result = list(grouped_data.values())
            
            # Aplicar el porcentaje de stock configurado por el usuario
            if user.as_stock_percentaje and user.as_stock_percentaje != 1.0:
                stock_factor = user.as_stock_percentaje
                for item in result:
                    item['stock'] = round(item['stock'] * stock_factor, 2)
                _logger.info("[as_get_stock] Aplicando porcentaje de stock %s%% configurado por el usuario %s", 
                             user.as_stock_percentaje * 100, user.name)
                
            _logger.info("[as_get_stock] Consulta exitosa por usuario %s, retornando %s registros", user.name, len(result))
            self._as_log_response('/nimax/stock', 200, result, user)
            
            return result
            
        except Exception as e:
            _logger.error("[as_get_stock] Error al consultar stock: %s", str(e))
            
            response_data = {'error': 'Error interno del servidor'}
            self._as_log_response('/nimax/stock', 500, response_data, user)
            
            return Response(
                json.dumps(response_data),
                status=500,
                content_type='application/json'
            )
            
    @http.route('/nimax/stock/postman_collection', type='http', auth='user', methods=['GET'])
    def as_download_postman_collection(self, **kwargs):
        """
        Endpoint para descargar la colección de Postman.
        
        Returns:
            Response: Respuesta HTTP con el archivo JSON de la colección de Postman
        """
        _logger.info("[as_download_postman_collection] Solicitud de descarga de colección Postman")
        self._as_log_request('/nimax/stock/postman_collection', 'GET', kwargs, request.env.user)
        
        # Verificar que el usuario tenga permisos
        if not request.env.user:
            response_data = {'error': 'No autorizado'}
            self._as_log_response('/nimax/stock/postman_collection', 401, response_data)
            
            return Response(
                json.dumps(response_data),
                status=401,
                content_type='application/json'
            )
            
        try:
            # Obtener la ruta del archivo
            file_path = get_module_resource('as_stock_api', 'static/postman', 'as_stock_api_collection.json')
            
            if not file_path or not os.path.exists(file_path):
                _logger.error("[as_download_postman_collection] Archivo no encontrado: %s", file_path)
                
                response_data = {'error': 'Archivo no encontrado'}
                self._as_log_response('/nimax/stock/postman_collection', 404, response_data, request.env.user)
                
                return Response(
                    json.dumps(response_data),
                    status=404,
                    content_type='application/json'
                )
                
            # Leer el contenido del archivo
            with open(file_path, 'r') as file:
                file_content = file.read()
                
            # Personalizar la colección con la API key del usuario
            if request.env.user.as_api_key and request.env.user.as_api_enabled:
                collection = json.loads(file_content)
                # Actualizar la variable api_key con la clave del usuario
                for variable in collection.get('variable', []):
                    if variable.get('key') == 'api_key':
                        variable['value'] = request.env.user.as_api_key
                
                # Actualizar los métodos de las solicitudes a POST
                for item in collection.get('item', []):
                    if 'request' in item and 'method' in item['request']:
                        # Solo cambiar los métodos GET que acceden al endpoint de stock
                        if item['request']['method'] == 'GET' and 'url' in item['request']:
                            url = item['request']['url']
                            if isinstance(url, dict) and 'path' in url and 'stock' in url.get('path', []):
                                item['request']['method'] = 'POST'
                                
                                # Mover los parámetros de la URL al cuerpo
                                if 'query' in url:
                                    body_params = {}
                                    for param in url.get('query', []):
                                        if 'key' in param and 'value' in param:
                                            body_params[param['key']] = param['value']
                                    
                                    # Eliminar los parámetros de la URL
                                    url['query'] = []
                                    
                                    # Agregar el cuerpo JSON
                                    item['request']['body'] = {
                                        'mode': 'raw',
                                        'raw': json.dumps(body_params, indent=2),
                                        'options': {
                                            'raw': {
                                                'language': 'json'
                                            }
                                        }
                                    }
                
                file_content = json.dumps(collection, indent=2)
                
            _logger.info("[as_download_postman_collection] Colección personalizada generada para el usuario %s", request.env.user.name)
            self._as_log_response('/nimax/stock/postman_collection', 200, {'status': 'success'}, request.env.user)
                
            # Devolver el archivo como descarga
            return Response(
                file_content,
                headers=[
                    ('Content-Type', 'application/json'),
                    ('Content-Disposition', 'attachment; filename=as_stock_api_collection.json')
                ]
            )
            
        except Exception as e:
            _logger.error("[as_download_postman_collection] Error al descargar colección: %s", str(e))
            
            response_data = {'error': 'Error interno del servidor'}
            self._as_log_response('/nimax/stock/postman_collection', 500, response_data, request.env.user)
            
            return Response(
                json.dumps(response_data),
                status=500,
                content_type='application/json'
            )
            
    @http.route('/nimax/stock/manual', type='http', auth='public', methods=['GET'], website=True)
    def as_view_manual(self, **kwargs):
        """
        Endpoint público para visualizar el manual de usuario.
        
        Returns:
            Response: Página HTML con el manual de usuario formateado
        """
        _logger.info("[as_view_manual] Solicitud de visualización del manual de usuario")
        self._as_log_request('/nimax/stock/manual', 'GET', kwargs)
        
        try:
            # Obtener la ruta del archivo
            file_path = get_module_resource('as_stock_api', 'MANUAL_USUARIO.md')
            
            if not file_path or not os.path.exists(file_path):
                _logger.error("[as_view_manual] Archivo de manual no encontrado: %s", file_path)
                
                return "<h1>Error</h1><p>Manual de usuario no encontrado.</p>"
                
            # Leer el contenido del archivo
            with open(file_path, 'r', encoding='utf-8') as file:
                markdown_content = file.read()
                
            # Convertir Markdown a HTML
            try:
                import markdown
                html_content = markdown.markdown(
                    markdown_content, 
                    extensions=['tables', 'fenced_code', 'codehilite']
                )
            except ImportError:
                # Si markdown no está instalado, mostrar texto plano con formato básico
                html_content = f"<pre>{markdown_content}</pre>"
                
            # Crear una página HTML completa con estilos
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Manual de Usuario - API de Stock</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 900px;
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
                        margin-bottom: 16px;
                    }}
                    table th, table td {{
                        padding: 6px 13px;
                        border: 1px solid #dfe2e5;
                    }}
                    table tr {{
                        background-color: #fff;
                        border-top: 1px solid #c6cbd1;
                    }}
                    table tr:nth-child(2n) {{
                        background-color: #f6f8fa;
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
                    }}
                    .footer {{
                        margin-top: 50px;
                        padding-top: 20px;
                        border-top: 1px solid #eaecef;
                        text-align: center;
                        font-size: 0.8em;
                        color: #6a737d;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1 style="color: white; border-bottom: none; margin: 0;">Manual de Usuario - API de Stock</h1>
                    <p style="margin: 0; margin-top: 10px;">Ahorasoft - Documentación oficial</p>
                </div>
                
                {html_content}
                
                <div class="footer">
                    <p>© {datetime.now().year} Ahorasoft. Todos los derechos reservados.</p>
                    <p>Versión 1.0.17</p>
                </div>
            </body>
            </html>
            """
            
            _logger.info("[as_view_manual] Manual de usuario servido correctamente")
            self._as_log_response('/nimax/stock/manual', 200, {'status': 'success'})
            
            return html
            
        except Exception as e:
            _logger.error("[as_view_manual] Error al servir el manual: %s", str(e))
            
            return f"<h1>Error</h1><p>No se pudo cargar el manual de usuario: {str(e)}</p>" 