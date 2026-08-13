# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, time
from odoo.tools.safe_eval import safe_eval
from datetime import date, datetime, time
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, is_html_empty
from odoo.tools.translate import html_translate
from odoo.http import request
from odoo.tools import format_amount
from odoo.tools.safe_eval import safe_eval
#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
class CouponProgram(models.Model):
    _inherit = 'coupon.program'
    
    sd_apply_toprunner_ecommerce = fields.Boolean('Aplicar automaticamente al E-commerce')

    def search_promo_ecommerce(self,product,partner,promos_disponibles):
        precio_usd = 0.0
        promo = self.env['coupon.program']
        for promo in promos_disponibles:
            cumple_producto = True
            cumple_cliente = True
            cumple = False
            producto = False
            if product._name == 'product.template':
                producto = product.product_variant_id
            else:
                producto = product
            if promo['productos'] and producto.id not in promo['productos']: 
                cumple_producto = False
            if not promo['productos']:
                cumple_producto = False
            if promo['clientes'] and partner not in promo['clientes']:
                cumple_cliente = False
            if not promo['clientes']:
                cumple_cliente = False
            if cumple_producto and cumple_cliente:
                cumple = True
                precio_usd = promo['price_unit_usd']
                promo_obj = promo['promo']
                return cumple, precio_usd, promo_obj
              
        return cumple,precio_usd,promo  
    
    def search_promo_disponibles_ecommerce(self):
        promos = []

        domain_promo = [
            ('sd_apply_toprunner_ecommerce', '=', True),
            ('active', '=', True)
        ]

        promociones = self.env['coupon.program'].sudo().search(domain_promo)

        # Cache para evitar repetir búsquedas
        cache_productos = {}
        cache_clientes = {}

        for promo in promociones:
            productos_ids = []
            clientes_ids = []

            # PRODUCTOS
            if promo.rule_products_domain:
                domain_str = promo.rule_products_domain

                if domain_str not in cache_productos:
                    domain = safe_eval(domain_str)
                    cache_productos[domain_str] = self.env['product.product'].sudo().search(domain).ids

                productos_ids = cache_productos[domain_str]

            # CLIENTES
            if promo.rule_partners_domain:
                domain_str = promo.rule_partners_domain

                if domain_str not in cache_clientes:
                    domain = safe_eval(domain_str)
                    cache_clientes[domain_str] = self.env['res.partner'].sudo().search(domain).ids

                clientes_ids = cache_clientes[domain_str]

            if productos_ids or clientes_ids:
                promos.append({
                    'promo': promo,
                    'productos': productos_ids,
                    'clientes': clientes_ids,
                    'price_unit_usd': promo.PRICE_UNIT_USD,
                })

        return promos
 
    # def search_promo_disponibles_ecommerce(self):
    #     promos = []
    #     vals = {}
    #     domain_promo = [('sd_apply_toprunner_ecommerce','=',True),('active','=',True)]
    #     promociones = self.env['coupon.program'].sudo().search(domain_promo)
    #     clientes = self.env['res.partner']
    #     productos = self.env['product.product']
    #     for promo in promociones:
    #         if promo.rule_products_domain:
    #             domain = safe_eval(promo.rule_products_domain)
    #             productos = self.env['product.product'].sudo().search(domain)
    #         if promo.rule_partners_domain:
    #             domain_partner = safe_eval(promo.rule_partners_domain)
    #             clientes = self.env['res.partner'].sudo().search(domain_partner)
    #         if productos or clientes:
    #             promos.append({
    #                 'promo': promo,
    #                 'productos': productos.ids,
    #                 'clientes': clientes.ids,
    #                 'price_unit_usd': promo.PRICE_UNIT_USD,
    #             })
    #     return promos
