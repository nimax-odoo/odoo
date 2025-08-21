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

    def search_promo(self,product,partner):
        domain_promo = [('sd_apply_toprunner_api','=',True),('active','=',True)]
        promociones = self.env['coupon.program'].sudo().search(domain_promo)
        precio_usd = 0.0
        cumple = False
        promo = self.env['coupon.program']
        for promo in promociones:
            domain = safe_eval(promo.rule_products_domain)
            productos = self.env['product.product'].sudo().search(domain)
            if product in productos:
                cumple = True
            domain_partner = safe_eval(promo.rule_partners_domain)
            clientes = self.env['res.partner'].sudo().search(domain_partner)
            if partner in clientes.ids:        
                cumple = True
            if cumple:
                precio_usd = promo.PRICE_UNIT_USD
                
        return cumple,precio_usd,promo   
                