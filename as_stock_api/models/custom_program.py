# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, time
from odoo.tools.safe_eval import safe_eval
from datetime import date, datetime, time
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError

#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
class CouponProgram(models.Model):
    _inherit = 'coupon.program'
    
    sd_apply_toprunner_api = fields.Boolean('Aplicar automaticamente al API')

    def search_promo(self,product,partner,promos_disponibles):
        precio_usd = 0.0
        cumple = False
        promo = self.env['coupon.program']
        for promo in promos_disponibles:
            if product.id in promo['productos'] or partner in promo['clientes']:
                cumple = True
                precio_usd = promo['price_unit_usd']
                promo_obj = promo['promo']
                return cumple, precio_usd, promo_obj
              
        return cumple,precio_usd,promo   
    
    def search_promo_disponibles(self):
        promos = []
        vals = {}
        domain_promo = [('sd_apply_toprunner_api','=',True),('active','=',True)]
        promociones = self.env['coupon.program'].sudo().search(domain_promo)
        clientes = self.env['res.partner']
        productos = self.env['product.product']
        for promo in promociones:
            if promo.rule_products_domain:
                domain = safe_eval(promo.rule_products_domain)
                productos = self.env['product.product'].sudo().search(domain)
            if promo.rule_partners_domain:
                domain_partner = safe_eval(promo.rule_partners_domain)
                clientes = self.env['res.partner'].sudo().search(domain_partner)
            if productos or clientes:
                promos.append({
                    'promo': promo,
                    'productos': productos.ids,
                    'clientes': clientes.ids,
                    'price_unit_usd': promo.PRICE_UNIT_USD,
                })
        return promos