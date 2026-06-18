# -*- coding: utf-8 -*-
import logging
import uuid
import requests
from odoo import api, fields, models, _
import json
_logger = logging.getLogger(__name__)
from datetime import date

class ProductTemplate(models.Model):
    _inherit = 'product.template'


    def compute_price_nimax(self,partner,pricelist):
        # Calcular el precio NIMAX
        for product in self:
            expected_earning = 0
            nimax_price_usd = 0
            expected_earning = pricelist.expected_earning or 0
            product_code = product.default_code
            price_unit = 0.0
            price_based_usd = 0.0
            try:
                promos_disponibles = self.env['coupon.program'].sudo().search_promo_disponibles()
                # Buscar el programa de proveedor (tf_partner_id) para este producto/categoría
                tf_partner_id = False
                tf_partner_id = self.env['tf.res.partner']
                for x in partner.tf_vendor_parameter_ids:
                    if x.category_id.id == product.categ_id.id:
                        tf_partner_id = x
                if tf_partner_id:
                    # Calcular el precio base USD según la fórmula
                    promo = self.env['coupon.program'].sudo()
                    promociones = self.env['coupon.program'].sudo().search_promo(product,partner.id,promos_disponibles)
                    if promociones[0]:
                        precio = promociones[1]
                        promo = promociones[2]
                        nimax_price_usd = precio
                    else:
                        precio = product.list_price
                        item_pricelist = False
                        for item in pricelist.item_ids:
                            if item.categ_id == product.categ_id:
                                item_pricelist = item
                        ################################################################
                        try:
                            price_result = pricelist._compute_price_rule(
                                products=product,
                                quantity=1,
                                currency=pricelist.currency_id,
                                uom=product.uom_id,
                                date=date.today()
                            )
                            price_unit = price_result[product.id][0]
                        except Exception as e:
                            price_unit = product.list_price
                        #################################################################
                        if price_unit:
                            
                            if item_pricelist and item_pricelist.as_utilidad > 0:
                                last_purchase_price = 0.0
                                if hasattr(product, 'as_last_purchase_price'):
                                    last_purchase_price = product.as_last_purchase_price
                                else:
                                    # Si no existe, usamos el standard_price como alternativa
                                    _logger.warning(f"[default_get] Campo as_last_purchase_price no existe, usando standard_price")
                                    last_purchase_price = product.standard_price
                                
                                if last_purchase_price and (1-item_pricelist.as_utilidad/100) != 0:
                                    descuento = (1-(last_purchase_price/(1-item_pricelist.as_utilidad/100)))*100
                                    price_unit = product.list_price * (1-descuento/100)
                                else:
                                    _logger.warning(f"[default_get] Precio de compra es 0 o división por cero, saltando cálculo de descuento")
                                
                            price_based_usd = (product.list_price - (product.list_price * tf_partner_id[0].partner_discount/100))*tf_partner_id[0].cost_deal_import/100*(product.tf_import_tax/100)

                        price_based_usd = self.env.company.currency_id._convert(price_based_usd,pricelist.currency_id,self.env.company,date.today())
                        price_based_usd = (price_based_usd)/(1-pricelist.expected_earning/100) if pricelist.expected_earning else price_based_usd
                        
            except Exception as e:
                _logger.error("[as_get_stock_with_price] Error al calcular precio para producto %s: %s", 
                                product_code, str(e))
                price_based_usd = 0
            return price_based_usd

    def get_in_store_product_available_qty(self, as_warehouse_ids, user):
        """ Return warehouses with stock formatted for API """
        warehouses = []
        warehouse_locations = user.as_warehouse_ids.mapped('view_location_id').ids
        domain = [('usage', '=', 'internal'), ('location_id', 'child_of', warehouse_locations)]
        locations = self.env['stock.location'].sudo().search(domain)
        for wh in locations:
            qty = self.product_variant_id.with_context(location=wh.id).free_qty
            warehouses.append({
                "id": str(wh.id),  # usa código si existe
                "name": str(wh.complete_name),  # usa nombre si existe
                "stock": max(0, int(qty))
            })
        return warehouses
    
    @api.model
    def send_full_catalog_cyberpuerta(self, user_id):
        """
        Envia el catalogo completo a Cyberpuerta
        """

        users = self.env['res.users'].sudo().search([('sd_cy_webhook_active','=',True)])
        for user in users:
            if not user or not user.sd_cy_token:
                raise Exception("Usuario sin token")

            url = str(user.sd_cy_url)+"/api/provider/articles/full-catalog"

            headers = {
                "Authorization": f"Bearer {user.sd_cy_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            products = self.sudo().search([
                ('sale_ok', '=', True),
                ('default_code', '!=', False)
            ],limit=20)

            payload = []

            for product in products:

                try:
                    # 💰 Precio
                    price = product.compute_price_nimax(
                        user.partner_id,
                        user.as_pricelist
                    )

                    # 📦 Warehouses (IMPORTANTE: convertir a dict)
                    warehouses_list = product.get_in_store_product_available_qty(
                        user.as_warehouse_ids, user
                    )

                    warehouses_dict = {}

                    for wh in warehouses_list:
                        warehouses_dict[str(wh['id'])] = {
                            "stock": int(wh['stock'])
                        }

                    # 💱 Moneda válida
                    currency = self.env.company.currency_id.name
                    if currency not in ['USD', 'MXN']:
                        currency = 'USD'

                    item = {
                        "sku": product.default_code,
                        "manufacturer_sku": product.default_code,
                        "manufacturer": product.brand_id.name if hasattr(product, 'brand_id') else "",
                        "ean": int(product.barcode) if product.barcode and product.barcode.isdigit() else None,
                        "title": product.name,
                        "description": product.description_sale or None,
                        "currency": currency,
                        "price": float(round(price, 2)),
                        "warehouses": warehouses_dict
                    }

                    payload.append(item)

                except Exception as e:
                    _logger.error(f"[Cyberpuerta] Error producto {product.default_code}: {str(e)}")

            if not payload:
                raise Exception("No hay productos para enviar")

            _logger.info(f"[Cyberpuerta] Catalogo enviado correctamente ({len(payload)} productos)")
            # 🚀 ENVÍO
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=120
                )

                if response.status_code != 200:
                    _logger.error(f"[Cyberpuerta] Error HTTP {response.status_code}: {response.text}")
                    raise Exception(f"Error enviando catalogo: {response.text}")
                return response.json() 
            except Exception as e:
                _logger.error(f"[Cyberpuerta] Error HTTP {e}")

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_location_alternative(self, location_id):
        self.ensure_one()
        location_id = self.env['stock.location'].sudo().browse(location_id)
        company_id = location_id.company_id.id
        match = self.env['match.locations'].search([
            ('name', '=', company_id),
            ('location_id', '=', location_id.id)
        ], limit=1)
        return match.location_dest_id

    def compute_locations_adicionals(self, location_id):
        self.ensure_one()
        location_id = self.env['stock.location'].sudo().browse(location_id)
        company_id = location_id.company_id.id
        match = self.env['match.locations'].search([
            ('name_to', '=', company_id),
            ('location_dest_id', '=', location_id)
        ], limit=1)

        if not match:
            return 0.0

        product = self.with_context(location=match.location_id.id)

        return product.free_qty