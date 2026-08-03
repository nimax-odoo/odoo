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
from odoo.modules.module import get_module_path
from odoo.fields import Date
import base64
_logger = logging.getLogger(__name__)

class ApiCyberpuerta(http.Controller):
    """
    API que permite gestionar la creacion de pedidos de venta, logistica y facturación 
    """
    def _validate_token(self):
        """CYBERPUERTA ya propoerciona un token que debe usarse por defecto, en caso de otra compañia colocar otro"""
        auth_header = request.httprequest.headers.get('Authorization')

        if not auth_header:
            return None

        try:
            token_type, token = auth_header.split(' ')
        except:
            return None

        if token_type != 'Bearer':
            return None

        user = request.env['res.users'].sudo().search([
            ('sd_cy_token', '=', token)
        ], limit=1)

        return user

    @http.route('/api/products/<string:sku>/pna', type='http', auth='public', methods=['GET'], csrf=False)
    def get_product_pna(self, sku):
        user = self._validate_token()
        if not user:
            return Response(
                json.dumps({"error": "Unauthorized"}),
                status=401,
                content_type='application/json'
            )
        request.env.user = user
        product = request.env['product.template'].sudo().search([
            ('default_code', '=', sku)
        ], limit=1)
        if not product:
            return Response(
                json.dumps({"error": "SKU not found"}),
                status=404,
                content_type='application/json'
            )

        # 💰 Precio calculado nimax
        produc_id = product.product_variant_id
        # price = product.compute_price_nimax(user.partner_id,user.as_pricelist)
        price = request.env['product.pricelist.promo.wizard'].sudo().calculate(user.as_pricelist, request.env.company.currency_id, user.partner_id, produc_id, 1.0)
        
        
        response = {
            "sku": product.default_code,
            "manufacturer_sku": product.default_code,
            "manufacturer": product.brand_id.name if hasattr(product, 'brand_id') else "",
            "ean": product.barcode or "",
            "title": product.name,
            "description": product.description_sale or "",
            "currency": request.env.company.currency_id.name, 
            "price": round(price,2),
        }
        stocks = product.get_in_store_product_available_qty(user.as_warehouse_ids, user)
        if stocks:
            response['warehouses'] = stocks

        return Response(
            json.dumps(response),
            status=200,
            content_type='application/json'
        )

    @http.route('/api/orders/create', type='http', auth='public', methods=['POST'], csrf=False)
    def create_order(self, **kwargs):
        # 🔐 1. Auth
        user = self._validate_token()
        if not user:
            self.create_log("create_order", str({"error": "Unauthorized"}), False, str(request.httprequest.data.decode('utf-8')))
            return Response(json.dumps({"error": "Unauthorized"}),status=401,content_type='application/json')
        env = request.env(
            user=user.id,
            context=dict(
                request.env.context,
                allowed_company_ids=user.company_ids.ids,
                force_company=user.company_id.id
            )
        )
        # 📥 2. Leer JSON
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
        except Exception:
            self.create_log("create_order", str({"error": "Invalid JSON"}), user.id,str(request.httprequest.data.decode('utf-8')))
            return Response(json.dumps({"error": "Invalid JSON"}),status=400,content_type='application/json')

        po_number = data.get('purchase_order_number')
        warehouse_id = int(data.get('warehouse'))
        products = data.get('products', [])
        if not po_number or not products:
            self.create_log("create_order", str({"error": "Missing data"}), user.id, str(data))
            return Response(json.dumps({"error": "Missing data"}),status=400,content_type='application/json')
        if not user.as_warehouse_ids:
            self.create_log("create_order", str({"error": "User has no assigned warehouses"}), user.id, str(data))
            return Response(json.dumps({"error": "User has no assigned warehouses"}),status=400,content_type='application/json')

        # 🚫 3. Evitar duplicados (CRÍTICO)
        existing_order = env['sale.order'].search([('client_order_ref', '=', po_number)], limit=1)

        if existing_order:
            return Response(json.dumps({
                    "subtotal": existing_order.amount_untaxed,
                    "total": existing_order.amount_total,
                    "currency": existing_order.currency_id.name,
                    "order_number": existing_order.name
                }),status=200,content_type='application/json')

        # 👤 4. Cliente
        partner = user.partner_id
        order_lines = []
        subtotal = 0.0
        # 🧾 5. Crear pedido
        location = env['stock.location'].sudo().search([('id', '=', warehouse_id)], limit=1)
        if not location:
            self.create_log("create_order", str({"error": f"Warehouse not found: {warehouse_id}"}), user.id, str(data))
            return Response(json.dumps({"error": f"Warehouse not found: {warehouse_id}"}),status=400,content_type='application/json')
        warehouse_locations = user.as_warehouse_ids.filtered(lambda x: x.company_id.id == location.company_id.id)
        if not warehouse_locations:
            self.create_log("create_order", str({"error": f"Warehouse not assigned to user: {warehouse_id}"}), user.id, str(data))
            return Response(json.dumps({"error": f"Warehouse not assigned to user: {warehouse_id}"}),status=400,content_type='application/json')
        else:
            warehouse_locations_id = warehouse_locations[0].id
        lineas = []
        for item in products:
            sku = item.get('sku')
            qty = item.get('quantity', 0)

            product = env['product.product'].sudo().search([('default_code', '=', sku)], limit=1)

            if not product:
                self.create_log("create_order", str({"error": f"SKU not found: {sku}"}), user.id, str(data))
                return Response(json.dumps({"error": f"SKU not found: {sku}"}),status=400,content_type='application/json')

            # 📦 Validar stock
            available_qty = product.sudo().product_variant_id.with_context(location=warehouse_id).free_qty

            if qty > available_qty:
                self.create_log("create_order", str({"error": f"Insufficient stock for {sku}"}), user.id, str(data))
                return Response(json.dumps({"error": f"Insufficient stock for {sku}","available": available_qty}),status=400,content_type='application/json')

            # 💰 Precio
            pricelist = user.sudo().as_pricelist
            price = product.sudo().product_tmpl_id.compute_price_nimax(user.partner_id,user.as_pricelist)

            subtotal += price * qty
            lineas.append((0, 0, {
                'product_id': product.id,
                'as_pricelist_id': pricelist.id,
                'product_uom_qty': qty,
                'price_unit': price
                }))
        if lineas:
            order = env['sale.order'].sudo().with_context(
                    force_company=user.company_id.id,
                    default_company_id=user.company_id.id,
                    default_company_ids=user.company_ids.ids,
                    default_company=user.company_id.id,
                    default_companies=user.company_ids.ids,
                    allowed_company_ids=user.company_ids.ids
                ).create({
                'x_studio_orden_de_compra': po_number,
                'partner_id': partner.id,
                'as_usuario_final': partner.name,
                'pricelist_id': user.sudo().as_pricelist.id,
                'warehouse_id': warehouse_locations_id,
                'client_order_ref': po_number,
                'company_id': location.company_id.id,
                'order_line': lineas,
            })
            seguidores = [order.partner_id.id, order.user_id.partner_id.id, order.partner_id.commercial_partner_id.id]
            order.message_subscribe(seguidores)  
            for line in order.order_line:
                action = line.pricelist_apply()
                ctx = action['context']
                wizard = self.env['sale.order.pricelist.wizard']\
                    .sudo().with_context(ctx)\
                    .create({})
                for line_wiz in wizard.pricelist_line:
                    if line_wiz.sh_pricelist_id == user.as_pricelist:
                        line_wiz.update_sale_line_unit_price()
                action_promo = line.promo_apply()
                ctxpromo = {
                    'active_ids': [line.id],
                    'active_model': 'sale.order.line',
                    'active_id': line.id,
                }
                wiz_promo = self.env['as.sale.order.promo.wizard']\
                    .sudo().with_context(ctxpromo)\
                    .create({})
                    
                if wiz_promo.promo_line:
                    wiz_promo.promo_line[0].update_sale_line_unit_price_promo()
                    
            order._amount_all_marigin()
            for line in order.order_line:
                line.get_margin_porcentaje()

        
            # 🔄 Confirmar pedido (opcional)
            order.sudo().action_confirm()
            for picking in order.picking_ids:
                picking.sudo().location_id = warehouse_id

            # 💰 6. Totales
            subtotal = order.amount_untaxed
            total = order.amount_total
            self.create_log("create_order", str({"create_order": f"Venta Creada: {order.name}"}), user.id, str(data))
            return Response(
                json.dumps({
                    "subtotal": round(subtotal, 2),
                    "total": round(total, 2),
                    "currency": order.currency_id.name,
                    "order_number": order.name
                }),
                status=200,
                content_type='application/json'
            )
        else:
            self.create_log("create_order", str({"create_order": f"Venta No Creada no hay lineas"}), user.id, str(data))
    
    @http.route('/api/orders/waybills', type='http', auth='public', methods=['POST'], csrf=False)
    def waybills(self, **kwargs):
        # 🔐 1. Auth
        user = self._validate_token()
        if not user:
            return Response(json.dumps({"result": 0}),status=401,content_type='application/json')
        env = request.env(
            user=user.id,
            context=dict(
                request.env.context,
                allowed_company_ids=user.company_ids.ids,
                force_company=user.company_id.id
            )
        )
        # 📥 2. Leer JSON
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
        except Exception:
            return Response(json.dumps({"result": 0}),status=400,content_type='application/json')

        order_number = data.get('order_number')
        waybills = data.get('waybills')
        carrier = data.get('carrier')
        
        file = data.get('file').encode()
        file_base64 = data.get('file')

        if not file_base64:
            return Response(json.dumps({"result": 0}), status=400, content_type='application/json')

        try:
            file = file_base64.encode()
        except Exception:
            return Response(json.dumps({"result": 0}), status=400, content_type='application/json')
        
        #buscamos la venta para agregar informacion 
        order = env['sale.order'].sudo().search([('name', '=', order_number)], limit=1)
        if not order:
            return Response(json.dumps({"result": 0}),status=400,content_type='application/json')
        order.sd_waybills = waybills
        carrier_id = env['delivery.carrier'].sudo().search([('name','=',carrier)])
        if not carrier_id:
            delivery_product = self.env['product.product'].sudo().create({'name': carrier})
            carrier_id = env['delivery.carrier'].sudo().create({'name':carrier,'product_id':delivery_product.id})
        order.carrier_id = carrier_id
        order.sd_carrier_id = carrier_id
        attach_name = waybills
        file_test = file_base64.encode()
        for pick in order.picking_ids:
            pick.carrier_id = carrier_id
            pick.carrier_tracking_ref = waybills
            picking = self.env['ir.attachment'].sudo().create({
                'datas': file_test,
                'name': attach_name,
                'mimetype': 'application/pdf',
                'res_model': 'stock.picking',
                'res_id': pick.id,
            })
        #adjuntar en la venta y en el picking
        venta = self.env['ir.attachment'].sudo().create({
            'datas': file_test,
            'name': attach_name,
            'mimetype': 'application/pdf',
            'res_model': 'sale.order',
            'res_id': order.id,
        })
        return Response(json.dumps({"result": 1}),status=200,content_type='application/json')

    @http.route('/api/provider/order/cfdi', type='http', auth='public', methods=['POST'], csrf=False)
    def cfdi(self, **kwargs):
        # 🔐 1. Auth
        user = self._validate_token()
        if not user:
            return Response(json.dumps({"result": 0}),status=401,content_type='application/json')
        env = request.env(user=user.id,context=dict(request.env.context,allowed_company_ids=user.company_ids.ids,force_company=user.company_id.id))
        # 📥 2. Leer JSON
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
        except Exception:
            return Response(json.dumps({"result": 0}),status=400,content_type='application/json')

        order_number = data.get('order_number')
        waybills = data.get('waybills')
        carrier = data.get('carrier')
    
    def create_log(self, name, json, user_id, response):
        try:
            log = request.env['request.logger'].sudo().create({
                'name': name,
                'user_id': user_id,
                'json': json,
                'response': response,
            })
            return log
        except Exception as e:
            _logger.error(f"Error creating log: {e}")
            return None