# -*- coding: utf-8 -*-

import base64
import binascii
import json
import logging
from datetime import datetime, timezone

from odoo import http
from odoo.http import request


_logger = logging.getLogger(__name__)

API_BASE = '/apinimaxfront/v1'
TOKEN_FIELD = 'sd_cy_token'  # Mantener temporalmente si este es el campo existente en res.users.


class ApiNimaxFront(http.Controller):
    """API de integración Nimax para productos, pedidos y logística."""

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _json(self, payload, status=200):
        """Devuelve un JSON HTTP usando el helper nativo de Odoo."""
        return request.make_json_response(payload, status=status)

    def _success(self, message, data=None, status=200, code=None):
        """Respuesta JSON homogénea para operaciones correctas."""
        payload = {
            'success': True,
            'message': message,
            'timestamp': datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }
        if code:
            payload['code'] = code
        if data is not None:
            payload['data'] = data
        return self._json(payload, status=status)

    def _error(self, code, message, status=400, errors=None):
        """Respuesta JSON homogénea para errores funcionales o de validación."""
        payload = {
            'success': False,
            'timestamp': datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            'error': {
                'code': code,
                'message': message,
            },
        }
        if errors is not None:
            payload['error']['details'] = errors
        return self._json(payload, status=status)

    def _request_body(self):
        """Devuelve el body como texto sin lanzar error por caracteres inválidos."""
        return request.httprequest.data.decode('utf-8', errors='replace')

    def _read_json(self):
        """Lee y valida que el body sea un objeto JSON."""
        raw_body = self._request_body()

        if not raw_body.strip():
            return None, self._error('EMPTY_BODY','El cuerpo de la solicitud no puede estar vacío.',status=400,)
        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            return None, self._error(
                'INVALID_JSON',
                'El cuerpo de la solicitud no contiene un JSON válido.',
                status=400,
                errors={
                    'line': exc.lineno,
                    'column': exc.colno,
                },
            )

        if not isinstance(data, dict):
            return None, self._error('INVALID_JSON_OBJECT','El cuerpo JSON debe ser un objeto.',status=400,)
        return data, None

    def _validate_token(self):
        """Valida el token Bearer y devuelve el usuario asociado."""
        auth_header = request.httprequest.headers.get('Authorization', '').strip()
        if not auth_header:
            return None

        parts = auth_header.split(None, 1)
        if len(parts) != 2:
            return None

        token_type, token = parts
        if token_type.lower() != 'bearer' or not token.strip():
            return None

        users = request.env['res.users'].sudo()
        if TOKEN_FIELD not in users._fields:
            _logger.error('El campo de token configurado no existe en res.users: %s', TOKEN_FIELD)
            return None

        return users.search([(TOKEN_FIELD, '=', token.strip())], limit=1)

    def _user_env(self, user):
        """Crea un Environment respetando usuario y compañías permitidas."""
        return request.env(
            user=user.id,
            context=dict(
                request.env.context,
                allowed_company_ids=user.company_ids.ids,
                force_company=user.company_id.id,
            ),
        )

    def _create_log(self, name, response_payload, user_id=False, request_payload=None):
        """Registra solicitud y respuesta sin interrumpir el endpoint si falla el log."""
        try:
            return request.env['request.logger'].sudo().create({
                'name': name,
                'user_id': user_id or False,
                'json': json.dumps(response_payload, ensure_ascii=False, default=str),
                'response': request_payload or '',
            })
        except Exception:
            _logger.exception('No se pudo crear el log de API: %s', name)
            return None

    def _unauthorized(self, endpoint_name):
        response_payload = {
            'success': False,
            'error': {
                'code': 'UNAUTHORIZED',
                'message': 'Token de autenticación ausente o inválido.',
            },
        }
        self._create_log(
            endpoint_name,
            response_payload,
            user_id=False,
            request_payload=self._request_body(),
        )
        return self._error(
            'UNAUTHORIZED',
            'Token de autenticación ausente o inválido.',
            status=401,
        )

    # -------------------------------------------------------------------------
    # Productos
    # -------------------------------------------------------------------------
    @http.route(f'{API_BASE}/products/<string:sku>/pna',type='http',auth='public',methods=['GET'],csrf=False,)
    def get_product_pna_nimax(self, sku):
        user = self._validate_token()
        if not user:
            return self._unauthorized('get_product_pna')

        env = self._user_env(user)

        product = env['product.template'].sudo().search([
            ('default_code', '=', sku)
        ], limit=1)

        if not product:
            return self._error(
                'PRODUCT_NOT_FOUND',
                f'No se encontró un producto con el SKU {sku}.',
                status=404,
                errors={'sku': sku},
            )

        if not user.as_pricelist:
            return self._error('PRICELIST_NOT_CONFIGURED','El usuario no tiene una lista de precios configurada.',status=422,)

        product_variant = product.product_variant_id
        price = env['product.pricelist.promo.wizard'].sudo().calculate(
            user.as_pricelist,
            env.company.currency_id,
            user.partner_id,
            product_variant,
            1.0,
        )

        product_data = {
            'sku': product.default_code,
            'manufacturer_sku': product.default_code,
            'manufacturer': product.brand_id.name if hasattr(product, 'brand_id') and product.brand_id else '',
            'ean': product.barcode or '',
            'title': product.name,
            'description': product.description_sale or '',
            'currency': env.company.currency_id.name,
            'price': round(price or 0.0, 2),
            'warehouses': product.get_in_store_product_available_qty(user.as_warehouse_ids, user) or [],
        }

        return self._success('Producto consultado correctamente.',data=product_data,code='PRODUCT_FOUND',)

    # -------------------------------------------------------------------------
    # Pedidos
    # -------------------------------------------------------------------------
    @http.route(
        f'{API_BASE}/orders/create',
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    def create_order(self, **kwargs):
        endpoint_name = 'create_order'
        user = self._validate_token()
        if not user:
            return self._unauthorized(endpoint_name)

        env = self._user_env(user)
        data, error_response = self._read_json()
        if error_response:
            self._create_log(
                endpoint_name,
                {'success': False, 'error': {'code': 'INVALID_JSON'}},
                user_id=user.id,
                request_payload=self._request_body(),
            )
            return error_response

        po_number = data.get('purchase_order_number')
        warehouse_value = data.get('warehouse')
        products = data.get('products')

        missing_fields = []
        if not po_number:
            missing_fields.append('purchase_order_number')
        if warehouse_value in (None, ''):
            missing_fields.append('warehouse')
        if not products:
            missing_fields.append('products')

        if missing_fields:
            response_payload = {
                'success': False,
                'error': {
                    'code': 'MISSING_REQUIRED_FIELDS',
                    'message': 'Faltan campos obligatorios en la solicitud.',
                    'details': {'missing_fields': missing_fields},
                },
            }
            self._create_log(endpoint_name, response_payload, user.id, self._request_body())
            return self._error(
                'MISSING_REQUIRED_FIELDS',
                'Faltan campos obligatorios en la solicitud.',
                status=400,
                errors={'missing_fields': missing_fields},
            )

        try:
            warehouse_id = int(warehouse_value)
        except (TypeError, ValueError):
            return self._error(
                'INVALID_WAREHOUSE_ID',
                'El campo warehouse debe contener un identificador numérico válido.',
                status=400,
                errors={'warehouse': warehouse_value},
            )

        if not isinstance(products, list):
            return self._error(
                'INVALID_PRODUCTS',
                'El campo products debe ser una lista.',
                status=400,
            )

        if not user.as_warehouse_ids:
            return self._error(
                'WAREHOUSE_NOT_CONFIGURED',
                'El usuario no tiene almacenes asignados.',
                status=403,
            )

        if not user.as_pricelist:
            return self._error(
                'PRICELIST_NOT_CONFIGURED',
                'El usuario no tiene una lista de precios configurada.',
                status=422,
            )

        # Idempotencia: si ya existe la orden de compra, devolvemos el pedido existente.
        existing_order = env['sale.order'].sudo().search([
            ('client_order_ref', '=', po_number)
        ], limit=1)

        if existing_order:
            return self._success(
                'La orden de compra ya había sido registrada. Se devuelve el pedido existente.',
                code='ORDER_ALREADY_EXISTS',
                data={
                    'already_exists': True,
                    'subtotal': round(existing_order.amount_untaxed, 2),
                    'total': round(existing_order.amount_total, 2),
                    'currency': existing_order.currency_id.name,
                    'order_number': existing_order.name,
                    'purchase_order_number': po_number,
                },
            )

        location = env['stock.location'].sudo().search([
            ('id', '=', warehouse_id)
        ], limit=1)

        if not location:
            return self._error(
                'WAREHOUSE_NOT_FOUND',
                f'No se encontró la ubicación de almacén {warehouse_id}.',
                status=404,
                errors={'warehouse': warehouse_id},
            )

        warehouse_locations = user.as_warehouse_ids.filtered(
            lambda warehouse: warehouse.company_id.id == location.company_id.id
        )
        if not warehouse_locations:
            return self._error(
                'WAREHOUSE_NOT_ALLOWED',
                'El almacén indicado no está permitido para este usuario.',
                status=403,
                errors={'warehouse': warehouse_id},
            )

        sale_warehouse_id = warehouse_locations[0].id
        pricelist = user.sudo().as_pricelist
        lines = []

        for index, item in enumerate(products, start=1):
            if not isinstance(item, dict):
                return self._error(
                    'INVALID_PRODUCT_LINE',
                    f'La línea {index} de products no es válida.',
                    status=400,
                    errors={'line': index},
                )

            sku = (item.get('sku') or '').strip()
            quantity_value = item.get('quantity')

            if not sku:
                return self._error(
                    'MISSING_SKU',
                    f'La línea {index} no contiene un SKU.',
                    status=400,
                    errors={'line': index},
                )

            try:
                quantity = float(quantity_value)
            except (TypeError, ValueError):
                return self._error(
                    'INVALID_QUANTITY',
                    f'La cantidad del SKU {sku} no es válida.',
                    status=400,
                    errors={'sku': sku, 'quantity': quantity_value},
                )

            if quantity <= 0:
                return self._error(
                    'INVALID_QUANTITY',
                    f'La cantidad del SKU {sku} debe ser mayor que cero.',
                    status=400,
                    errors={'sku': sku, 'quantity': quantity},
                )

            product = env['product.product'].sudo().search([
                ('default_code', '=', sku)
            ], limit=1)

            if not product:
                return self._error(
                    'PRODUCT_NOT_FOUND',
                    f'No se encontró el SKU {sku}.',
                    status=404,
                    errors={'sku': sku, 'line': index},
                )

            available_qty = product.with_context(location=warehouse_id).free_qty
            if quantity > available_qty:
                return self._error(
                    'INSUFFICIENT_STOCK',
                    f'No hay stock suficiente para el SKU {sku}.',
                    status=409,
                    errors={
                        'sku': sku,
                        'requested': quantity,
                        'available': available_qty,
                        'warehouse': warehouse_id,
                    },
                )

            price = product.product_tmpl_id.compute_price_nimax(
                user.partner_id,
                pricelist,
            )

            lines.append((0, 0, {
                'product_id': product.id,
                'as_pricelist_id': pricelist.id,
                'product_uom_qty': quantity,
                'price_unit': price,
            }))

        if not lines:
            return self._error(
                'EMPTY_ORDER',
                'No se generaron líneas válidas para crear el pedido.',
                status=400,
            )

        try:
            order = env['sale.order'].sudo().with_context(
                force_company=user.company_id.id,
                default_company_id=user.company_id.id,
                default_company_ids=user.company_ids.ids,
                default_company=user.company_id.id,
                default_companies=user.company_ids.ids,
                allowed_company_ids=user.company_ids.ids,
            ).create({
                'x_studio_orden_de_compra': po_number,
                'partner_id': user.partner_id.id,
                'as_usuario_final': user.partner_id.name,
                'pricelist_id': pricelist.id,
                'warehouse_id': sale_warehouse_id,
                'client_order_ref': po_number,
                'company_id': location.company_id.id,
                'order_line': lines,
            })

            follower_ids = {
                order.partner_id.id,
                order.user_id.partner_id.id,
                order.partner_id.commercial_partner_id.id,
            }
            order.message_subscribe(partner_ids=[partner_id for partner_id in follower_ids if partner_id])

            for line in order.order_line:
                action = line.pricelist_apply() or {}
                ctx = action.get('context', {})
                wizard = env['sale.order.pricelist.wizard'].sudo().with_context(ctx).create({})

                for line_wizard in wizard.pricelist_line:
                    if line_wizard.sh_pricelist_id == pricelist:
                        line_wizard.update_sale_line_unit_price()

                line.promo_apply()
                promo_context = {
                    'active_ids': [line.id],
                    'active_model': 'sale.order.line',
                    'active_id': line.id,
                }
                promo_wizard = env['as.sale.order.promo.wizard'].sudo().with_context(
                    promo_context
                ).create({})

                if promo_wizard.promo_line:
                    promo_wizard.promo_line[0].update_sale_line_unit_price_promo()

            order._amount_all_marigin()
            for line in order.order_line:
                line.get_margin_porcentaje()

            order.sudo().action_confirm()
            for picking in order.picking_ids:
                picking.sudo().location_id = warehouse_id

        except Exception:
            _logger.exception('Error al crear el pedido Nimax. PO: %s', po_number)
            self._create_log(
                endpoint_name,
                {'success': False, 'error': {'code': 'ORDER_CREATION_ERROR'}},
                user.id,
                self._request_body(),
            )
            return self._error(
                'ORDER_CREATION_ERROR',
                'No fue posible crear el pedido por un error interno.',
                status=500,
            )

        response_data = {
            'already_exists': False,
            'subtotal': round(order.amount_untaxed, 2),
            'total': round(order.amount_total, 2),
            'currency': order.currency_id.name,
            'order_number': order.name,
            'purchase_order_number': po_number,
        }

        self._create_log(
            endpoint_name,
            {
                'success': True,
                'code': 'ORDER_CREATED',
                'data': response_data,
            },
            user.id,
            self._request_body(),
        )

        return self._success(
            'Pedido creado y confirmado correctamente.',
            data=response_data,
            status=201,
            code='ORDER_CREATED',
        )

    # -------------------------------------------------------------------------
    # Guías / logística
    # -------------------------------------------------------------------------
    @http.route(
        f'{API_BASE}/orders/waybills',
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    def waybills(self, **kwargs):
        endpoint_name = 'waybills'
        user = self._validate_token()
        if not user:
            return self._unauthorized(endpoint_name)

        env = self._user_env(user)
        data, error_response = self._read_json()
        if error_response:
            return error_response

        order_number = (data.get('order_number') or '').strip()
        waybill_number = (data.get('waybills') or '').strip()
        carrier_name = (data.get('carrier') or '').strip()
        file_base64 = data.get('file')

        missing_fields = [
            field_name
            for field_name, field_value in {
                'order_number': order_number,
                'waybills': waybill_number,
                'carrier': carrier_name,
                'file': file_base64,
            }.items()
            if not field_value
        ]

        if missing_fields:
            return self._error(
                'MISSING_REQUIRED_FIELDS',
                'Faltan campos obligatorios para registrar la guía.',
                status=400,
                errors={'missing_fields': missing_fields},
            )

        if not isinstance(file_base64, str):
            return self._error(
                'INVALID_FILE',
                'El campo file debe contener un archivo PDF codificado en Base64.',
                status=400,
            )

        # Acepta tanto Base64 puro como data URI.
        if file_base64.startswith('data:'):
            try:
                _, file_base64 = file_base64.split(',', 1)
            except ValueError:
                return self._error(
                    'INVALID_FILE',
                    'El formato data URI del archivo no es válido.',
                    status=400,
                )

        try:
            decoded_file = base64.b64decode(file_base64, validate=True)
        except (binascii.Error, ValueError):
            return self._error(
                'INVALID_BASE64_FILE',
                'El archivo enviado no contiene un Base64 válido.',
                status=400,
            )

        if not decoded_file.startswith(b'%PDF-'):
            return self._error(
                'INVALID_PDF_FILE',
                'El archivo enviado no parece ser un PDF válido.',
                status=400,
            )

        order = env['sale.order'].sudo().search([
            ('name', '=', order_number)
        ], limit=1)

        if not order:
            return self._error(
                'ORDER_NOT_FOUND',
                f'No se encontró el pedido {order_number}.',
                status=404,
                errors={'order_number': order_number},
            )

        try:
            order.sd_waybills = waybill_number

            carrier = env['delivery.carrier'].sudo().search([
                ('name', '=', carrier_name)
            ], limit=1)

            if not carrier:
                delivery_product = env['product.product'].sudo().create({
                    'name': carrier_name,
                    'type': 'service',
                })
                carrier = env['delivery.carrier'].sudo().create({
                    'name': carrier_name,
                    'product_id': delivery_product.id,
                })

            order.carrier_id = carrier
            order.sd_carrier_id = carrier

            attachment_values = {
                'datas': file_base64.encode(),
                'name': waybill_number,
                'mimetype': 'application/pdf',
            }

            for picking in order.picking_ids:
                picking.carrier_id = carrier
                picking.carrier_tracking_ref = waybill_number
                env['ir.attachment'].sudo().create({
                    **attachment_values,
                    'res_model': 'stock.picking',
                    'res_id': picking.id,
                })

            env['ir.attachment'].sudo().create({
                **attachment_values,
                'res_model': 'sale.order',
                'res_id': order.id,
            })

        except Exception:
            _logger.exception('Error al registrar la guía del pedido %s', order_number)
            return self._error(
                'WAYBILL_PROCESSING_ERROR',
                'No fue posible registrar la guía por un error interno.',
                status=500,
            )

        response_data = {
            'result': 1,
            'order_number': order.name,
            'waybill': waybill_number,
            'carrier': carrier.name,
            'pickings_updated': len(order.picking_ids),
        }

        self._create_log(
            endpoint_name,
            {'success': True, 'code': 'WAYBILL_REGISTERED', 'data': response_data},
            user.id,
            self._request_body(),
        )

        return self._success(
            'Guía registrada correctamente.',
            data=response_data,
            code='WAYBILL_REGISTERED',
        )

    # -------------------------------------------------------------------------
    # CFDI
    # -------------------------------------------------------------------------
    @http.route(
        f'{API_BASE}/provider/order/cfdi',
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    def cfdi(self, **kwargs):
        user = self._validate_token()
        if not user:
            return self._unauthorized('cfdi')

        data, error_response = self._read_json()
        if error_response:
            return error_response

        return self._error(
            'NOT_IMPLEMENTED',
            'El endpoint CFDI todavía no está implementado.',
            status=501,
        )
