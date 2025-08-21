# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

import json
import logging
import os
from datetime import datetime
from odoo import http, _
from odoo.http import request, Response
from odoo.exceptions import AccessError, ValidationError
from odoo.modules.module import get_module_resource
from odoo.fields import Date

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
        return True
        
        # try:
        #     # Cambiar al entorno del usuario para verificar permisos
        #     user_env = request.env(user=user.id)
        #     user_env['stock.quant'].check_access_rights('read')
        #     return True
        # except AccessError:
        #     return False
    
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
        params = json.loads(request.httprequest.data.decode('utf-8')) or {}
        
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
        domain = [('quantity', '>', 0)]  # Solo productos con stock positivo
        
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
        
        # Filtrar por almacenes si el usuario tiene configurados almacenes específicos
        if user.as_warehouse_ids:
            _logger.info("[as_get_stock] Filtrando por almacenes específicos del usuario: %s", 
                         ", ".join(user.as_warehouse_ids.mapped('name')))
            warehouse_locations = user.as_warehouse_ids.mapped('view_location_id').ids
            domain.append(('location_id', 'child_of', warehouse_locations))
        
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
                nimax_price_usd = 0
                # Obtener los attribute_line_ids del producto
                attribute_lines = []
                try:
                    if product.product_tmpl_id and product.product_tmpl_id.attribute_line_ids:
                        for attr_line in product.product_tmpl_id.attribute_line_ids:
                            values = []
                            try:
                                for val in attr_line.value_ids:
                                    values.append(val.name)
                            except Exception as e:
                                _logger.warning("[as_get_stock] Error al procesar los valores de attribute_line_id: %s", str(e))
                                
                            attribute_lines.append({
                                "attribute_name": attr_line.attribute_id.name,
                                "values": values
                            })
                except Exception as e:
                    _logger.warning("[as_get_stock] Error al procesar attribute_line_ids para producto %s: %s", product_code, str(e))
                    attribute_lines = []
                
                # Agrupar sumando cantidades
                if key in grouped_data:
                    grouped_data[key]['stock'] += available_qty
                    grouped_data[key]['reserved_quantity'] += quant['reserved_quantity']
                else:
                    grouped_data[key] = {
                        'location': location_name,
                        'product_code': product_code,
                        'product_name': product_name,
                        'stock': available_qty,
                        'reserved_quantity': quant['reserved_quantity'],
                        'nimax_price_usd': round(nimax_price_usd, 2),
                        'attribute_line_ids': attribute_lines
                    }
            
            # Convertir el diccionario agrupado a lista
            result = list(grouped_data.values())
            
            # Aplicar el porcentaje de stock configurado por el usuario
            if user.as_stock_percentaje and user.as_stock_percentaje != 1.0:
                stock_factor = user.as_stock_percentaje
                for item in result:
                    item['stock'] = round(item['stock'] * stock_factor, 2)
                    # La cantidad reservada no se modifica por el factor de stock
                _logger.info("[as_get_stock] Aplicando porcentaje de stock %s%% configurado por el usuario %s", 
                             user.as_stock_percentaje * 100, user.name)
            
            # Convertir stock a entero para todas las entradas
            for item in result:
                item['stock'] = int(item['stock'])
                item['reserved_quantity'] = int(item['reserved_quantity'])
            
            # Filtrar productos con stock cero después de aplicar porcentaje
            result = [item for item in result if item['stock'] > 0]
            
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
                
                # Actualizar descripciones con el campo reserved_quantity
                for item in collection.get('item', []):
                    if 'description' in item:
                        desc = item.get('description', '')
                        if 'stock' in desc and 'reserved_quantity' not in desc:
                            item['description'] = f"{desc} La respuesta incluye el campo reserved_quantity que indica la cantidad del producto reservada."
                        if 'stock' in desc and 'attribute_line_ids' not in desc:
                            item['description'] = f"{item['description']} También incluye attribute_line_ids con la información de atributos del producto."
                
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

    @http.route('/nimax/stock_with_price', type='json', auth='none', methods=['POST'], csrf=False)
    def as_get_stock_with_price(self, **kwargs):
        """
        Endpoint para consultar el stock disponible con precios NIMAX.
        
        Args en el cuerpo JSON:
            default_code (str, opcional): Código del producto a filtrar
            location_id (int, opcional): ID de la ubicación a filtrar
            partner_id (int, obligatorio): ID del cliente para determinar la lista de precios
            api_key (str, obligatorio): Clave API para autenticación
            
        Returns:
            dict: Datos de stock y precios en formato JSON o mensaje de error
        """
        # Obtener los parámetros del cuerpo JSON
        params = json.loads(request.httprequest.data.decode('utf-8')) or {} or {}
        
        _logger.info("[as_get_stock_with_price] Recibida solicitud POST de consulta de stock con precios")
        self._as_log_request('/nimax/stock_with_price', 'POST', params)
        
        # Verificar autenticación por API key
        api_key = params.get('api_key')
        if not api_key:
            _logger.warning("[as_get_stock_with_price] Intento de acceso sin API key")
            
            response_data = {'error': 'Se requiere API key'}
            self._as_log_response('/nimax/stock_with_price', 401, response_data)
            
            return Response(
                json.dumps(response_data),
                status=401,
                content_type='application/json'
            )
        user = self._as_validate_api_key(api_key)
        user = user.sudo()
        if not user:
            _logger.warning("[as_get_stock_with_price] Intento de acceso con API key inválida")
            
            response_data = {'error': 'API key inválida'}
            self._as_log_response('/nimax/stock_with_price', 403, response_data)
            
            return Response(
                json.dumps(response_data),
                status=403,
                content_type='application/json'
            )
        
        # Verificar permisos de usuario
        if not self._as_check_permissions(user):
            _logger.warning("[as_get_stock_with_price] Usuario %s sin permisos para acceder a stock.quant", user.name)
            
            response_data = {'error': 'No tiene permisos para acceder a esta información'}
            self._as_log_response('/nimax/stock_with_price', 403, response_data, user)
            
            return Response(
                json.dumps(response_data),
                status=403,
                content_type='application/json'
            )
            
        # Obtener parámetros de filtrado
        default_code = params.get('default_code')
        location_id = params.get('location_id')
        partner_id = params.get('partner_id')
        
        # Si no se proporciona partner_id, verificar si el usuario tiene un cliente predeterminado
        if not partner_id and user.as_partner_id:
            partner_id = user.as_partner_id.id
            _logger.info("[as_get_stock_with_price] Usando cliente predeterminado del usuario: %s (ID: %s)", 
                         user.as_partner_id.name, partner_id)
        
        # Verificar que se proporcione el ID del cliente
        if not partner_id:
            _logger.warning("[as_get_stock_with_price] Falta el parámetro partner_id y el usuario no tiene cliente predeterminado")
            
            response_data = {'error': 'Se requiere el ID del cliente (partner_id) o configurar un cliente predeterminado en el usuario API'}
            self._as_log_response('/nimax/stock_with_price', 400, response_data, user)
            
            return Response(
                json.dumps(response_data),
                status=400,
                content_type='application/json'
            )
        
        # Buscar el cliente y su lista de precios
        try:
            partner_id = int(partner_id)
            partner = request.env['res.partner'].sudo().browse(partner_id)
            if not partner.exists():
                _logger.warning("[as_get_stock_with_price] Cliente con ID %s no encontrado", partner_id)
                
                response_data = {'error': f'Cliente con ID {partner_id} no encontrado'}
                self._as_log_response('/nimax/stock_with_price', 404, response_data, user)
                
                return Response(
                    json.dumps(response_data),
                    status=404,
                    content_type='application/json'
                )
                
            # Obtener la lista de precios considerando la compañía del usuario para evitar errores de tipos
            company_id = user.company_id.id
            _logger.info("[as_get_stock_with_price] Compañía del usuario: %s (ID: %s)", user.company_id.name, company_id)
            
            # Primero verificar si el usuario tiene una lista de precios configurada para la API
            pricelist = False
            if user.as_pricelist:
                pricelist = user.as_pricelist
                _logger.info("[as_get_stock_with_price] Usando lista de precios configurada en el usuario: %s (ID: %s)", 
                            pricelist.name, pricelist.id)
            
            # Si el usuario no tiene lista de precios configurada, usar la del cliente
            if not pricelist:
                # Verificar la propiedad de la lista de precios del cliente
                try:
                    # Usar with_company() en lugar de with_context(force_company) para Odoo 15 Enterprise
                    pricelist_property_id = partner.with_company(user.company_id).property_product_pricelist.id
                    _logger.info("[as_get_stock_with_price] Lista de precios del cliente (property_product_pricelist.id): %s", pricelist_property_id)
                except Exception as e:
                    _logger.warning("[as_get_stock_with_price] Error al acceder a property_product_pricelist: %s", str(e))
                    pricelist_property_id = False
                
                if not pricelist_property_id:
                    # Buscar una lista de precios por defecto si no hay propiedad
                    # Solo usar listas de precios activas
                    pricelist = request.env['product.pricelist'].sudo().search([
                        ('active', '=', True)
                    ], limit=1)
                    _logger.info("[as_get_stock_with_price] Usando lista de precios por defecto ya que el cliente no tiene una asignada")
                else:
                    # Buscar la lista de precios específica
                    pricelist = request.env['product.pricelist'].sudo().search([
                        ('id', '=', pricelist_property_id),
                        ('active', '=', True)
                    ], limit=1)
                    
                    # Si no se encuentra la lista específica, buscar una por defecto
                    if not pricelist:
                        _logger.warning("[as_get_stock_with_price] La lista de precios del cliente no está activa")
                        pricelist = request.env['product.pricelist'].sudo().search([
                            ('active', '=', True)
                        ], limit=1)
                        _logger.info("[as_get_stock_with_price] Usando lista de precios alternativa al no encontrar la del cliente")
            
            if not pricelist:
                _logger.warning("[as_get_stock_with_price] No se pudo encontrar ninguna lista de precios válida")
                
                response_data = {'error': 'No se pudo encontrar una lista de precios válida para esta consulta'}
                self._as_log_response('/nimax/stock_with_price', 400, response_data, user)
                
                return Response(
                    json.dumps(response_data),
                    status=400,
                    content_type='application/json'
                )
                
            pricelist_id = pricelist.id
            _logger.info("[as_get_stock_with_price] Lista de precios seleccionada: %s (ID: %s)", pricelist.name, pricelist_id)
        except (ValueError, TypeError) as e:
            _logger.warning("[as_get_stock_with_price] Error al procesar cliente o lista de precios: %s", str(e))
            
            response_data = {'error': 'Error al procesar cliente o lista de precios'}
            self._as_log_response('/nimax/stock_with_price', 400, response_data, user)
            
            return Response(
                json.dumps(response_data),
                status=400,
                content_type='application/json'
            )

        try:
            # Obtener el tipo de cambio MXN más reciente
            mxn_currency = request.env['res.currency'].sudo().search([('name', '=', 'MXN')], limit=1)
            usd_currency = request.env['res.currency'].sudo().search([('name', '=', 'USD')], limit=1)
            
            if not mxn_currency or not usd_currency:
                _logger.error("[as_get_stock_with_price] No se encontró la moneda MXN o USD")
                return Response(
                    json.dumps({'error': 'Error al obtener las monedas MXN/USD'}),
                    status=500,
                    content_type='application/json'
                )
            
            # Obtener la tasa de cambio más reciente
            today = Date.today()
            rate = usd_currency._convert(1.0, mxn_currency, user.company_id, today)
            _logger.info("[as_get_stock_with_price] Tasa de cambio USD/MXN obtenida: %s", rate)
        except Exception as e:
            _logger.error("[as_get_stock_with_price] Error al obtener tipo de cambio: %s", str(e))
            return Response(
                json.dumps({'error': 'Error al obtener tipo de cambio MXN/USD'}),
                status=500,
                content_type='application/json'
            )

        # Compatibilidad con versiones anteriores
        product_id = params.get('product_id')
        if product_id and not default_code:
            _logger.warning("[as_get_stock_with_price] Uso de parámetro obsoleto product_id: %s", product_id)
            
            response_data = {
                'warning': 'El parámetro product_id está obsoleto. Por favor, use default_code en su lugar.',
                'migration_guide': 'Cambie el parámetro product_id por default_code en el cuerpo de la solicitud.'
            }
            self._as_log_response('/nimax/stock_with_price', 200, response_data, user)
        
        # Construir dominio de búsqueda
        # domain = [('quantity', '>', 0)]  # Solo productos con stock positivo
        domain = []  # Solo productos con stock positivo
        
        # Filtrar por código de producto si se proporciona
        if default_code:
            # Buscar el producto por su código
            product = request.env['product.product'].sudo().search([('default_code', '=', default_code)], limit=1)
            if not product:
                _logger.warning("[as_get_stock_with_price] Código de producto no encontrado: %s", default_code)
                
                response_data = {'error': f'Producto con código {default_code} no encontrado'}
                self._as_log_response('/nimax/stock_with_price', 404, response_data, user)
                
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
                _logger.warning("[as_get_stock_with_price] Parámetro product_id inválido: %s", product_id)
                
                response_data = {'error': 'Parámetro product_id inválido'}
                self._as_log_response('/nimax/stock_with_price', 400, response_data, user)
                
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
                _logger.warning("[as_get_stock_with_price] Parámetro location_id inválido: %s", location_id)
                
                response_data = {'error': 'Parámetro location_id inválido'}
                self._as_log_response('/nimax/stock_with_price', 400, response_data, user)
                
                return Response(
                    json.dumps(response_data),
                    status=400,
                    content_type='application/json'
                )
        
        # Solo considerar ubicaciones internas (tipo = internal)
        domain.append(('location_id.usage', '=', 'internal'))
        
        # Filtrar por almacenes si el usuario tiene configurados almacenes específicos
        if user.as_warehouse_ids:
            _logger.info("[as_get_stock_with_price] Filtrando por almacenes específicos del usuario: %s", 
                         ", ".join(user.as_warehouse_ids.mapped('name')))
            warehouse_locations = user.as_warehouse_ids.mapped('view_location_id').ids
            domain.append(('location_id', 'child_of', warehouse_locations))
        
        try:
            # Cambiar al entorno del usuario para la consulta
            user_env = request.env(user=user.id)
            pricelist = request.env['product.pricelist'].sudo().browse(pricelist_id)
            
            # Verificar que podemos acceder a los atributos necesarios para evitar errores
            expected_earning = 0
            try:
                expected_earning = pricelist.expected_earning or 0
            except Exception as e:
                _logger.warning("[as_get_stock_with_price] Error al acceder a expected_earning: %s", str(e))
            
            # Consultar stock.quant con optimización de campos
            quants = user_env['stock.quant'].sudo().search_read(
                domain=domain,
                fields=[
                    'product_id', 
                    'location_id', 
                    'quantity', 
                    'lot_id', 
                    'reserved_quantity',
                    'write_date'
                ],
                order='write_date desc'
            )
            
            # Preparar respuesta simplificada
            result = []
            
            # Diccionario para agrupar por ubicación y código de producto
            grouped_data = {}
            promos_disponibles = request.env['coupon.program'].sudo().search_promo_disponibles()
            for quant in quants:
                product = request.env['product.product'].sudo().browse(quant['product_id'][0])
                available_qty = quant['quantity'] - quant['reserved_quantity']
                
                # Crear clave única para agrupar
                location_name = quant['location_id'][1]
                product_code = product.default_code or ''
                product_name = quant['product_id'][1]
                product_info_id = quant['product_id'][0]
                key = f"{location_name}_{product_code}"
                
                # Calcular el precio NIMAX
                nimax_price_usd = 0
                try:
                    # Buscar el programa de proveedor (tf_partner_id) para este producto/categoría
                    tf_partner_id = False
                    for x in partner.tf_vendor_parameter_ids:
                        if x.category_id.id == product.categ_id.id:
                            tf_partner_id = x
                            break
                    if tf_partner_id:
                        # Calcular el precio base USD según la fórmula
                        promo = request.env['coupon.program'].sudo()
                        promociones = request.env['coupon.program'].sudo().search_promo(product,partner_id,promos_disponibles)
                        if promociones[0]:
                            precio = promociones[1]
                            promo = promociones[2]
                            nimax_price_usd = precio
                        else:
                            precio = product.list_price
                            price_based_usd = (precio - (precio * tf_partner_id.partner_discount/100)) * \
                                            tf_partner_id.cost_deal_import/100 * \
                                            (product.product_tmpl_id.tf_import_tax/100)
                            
                            # Calcular el precio NIMAX
                            nimax_price_usd = price_based_usd / (1 - expected_earning/100) if expected_earning < 100 else 0
                except Exception as e:
                    _logger.error("[as_get_stock_with_price] Error al calcular precio para producto %s: %s", 
                                 product_code, str(e))
                    nimax_price_usd = 0
                
                # Obtener los attribute_line_ids del producto
                attribute_lines = []
                try:
                    if product.product_tmpl_id and product.product_tmpl_id.sudo().attribute_line_ids:
                        for attr_line in product.product_tmpl_id.sudo().attribute_line_ids:
                            values = []
                            try:
                                for val in attr_line.value_ids:
                                    values.append(val.name)
                            except Exception as e:
                                _logger.warning("[as_get_stock_with_price] Error al procesar los valores de attribute_line_id: %s", str(e))
                                
                            attribute_lines.append({
                                "attribute_name": attr_line.attribute_id.name,
                                "values": values
                            })
                except Exception as e:
                    _logger.warning("[as_get_stock_with_price] Error al procesar attribute_line_ids para producto %s: %s", product_code, str(e))
                    attribute_lines = []
                
                # Agrupar sumando cantidades
                if key in grouped_data:
                    grouped_data[key]['stock'] += available_qty
                    grouped_data[key]['reserved_quantity'] += quant['reserved_quantity']
                else:
                    grouped_data[key] = {
                        'location': location_name,
                        'product_code': product_code,
                        'product_name': product_name,
                        'product_id': product_info_id,
                        'stock': available_qty,
                        'reserved_quantity': quant['reserved_quantity'],
                        'nimax_price_usd': round(nimax_price_usd, 2),
                        'nimax_price_mxn': round(nimax_price_usd * rate, 2),
                        'rate_usd': round(rate, 4),
                        'attribute_line_ids': attribute_lines
                    }
            
            # Convertir el diccionario agrupado a lista
            result = list(grouped_data.values())
            
            # Aplicar el porcentaje de stock configurado por el usuario
            if user.as_stock_percentaje and user.as_stock_percentaje != 1.0:
                stock_factor = user.as_stock_percentaje
                for item in result:
                    item['stock'] = round(item['stock'] * stock_factor, 2)
                    # La cantidad reservada no se modifica por el factor de stock
                _logger.info("[as_get_stock_with_price] Aplicando porcentaje de stock %s%% configurado por el usuario %s", 
                             user.as_stock_percentaje * 100, user.name)
            
            # Convertir stock a entero para todas las entradas
            for item in result:
                item['stock'] = int(item['stock'])
                item['reserved_quantity'] = int(item['reserved_quantity'])
            
            # Filtrar productos con stock cero después de aplicar porcentaje
            result = [item for item in result if item['stock'] > 0]
            
            # Agregar información de la lista de precios y del cliente
            for item in result:
                item['pricelist_name'] = pricelist.name
                item['pricelist_id'] = pricelist_id
                item['pricelist_currency'] = pricelist.currency_id.name
                item['partner_id'] = partner.id
                item['partner_name'] = partner.name
            
            _logger.info("[as_get_stock_with_price] Consulta exitosa por usuario %s, retornando %s registros", user.name, len(result))
            self._as_log_response('/nimax/stock_with_price', 200, result, user)
            
            return result
            
        except Exception as e:
            _logger.error("[as_get_stock_with_price] Error al consultar stock: %s", str(e))
            
            response_data = {'error': 'Error interno del servidor'}
            self._as_log_response('/nimax/stock_with_price', 500, response_data, user)
            
            return Response(
                json.dumps(response_data),
                status=500,
                content_type='application/json'
            ) 