# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


as_type = ([
    ('Normal','Normal'),
    ('Promo Remate','Promo Remate'),
    ('Promo Demo','Promo Demo'),
    ('Promo Carnavalero','Promo Carnavalero')
    ])

class as_SaleCouponProgram(models.Model):
    _inherit = 'sale.coupon.program'
    
    as_price_list = fields.Many2one('product.pricelist', string='Lista de Precios')
    as_type = fields.Selection(as_type, string='Tipo de Promocion',default='Normal',required=True)
    