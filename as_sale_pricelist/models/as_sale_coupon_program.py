# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


as_type = ([
    ('NORMAL','Normal'),
    ('DEAL','Oportunidad'),
    ('DEMO','Demo'),
    ('ESPECIAL','Especial'),
    ('FABRICANTE','Fabricante'),
    ])

class as_SaleCouponProgram(models.Model):
    _inherit = 'sale.coupon.program'
    
    as_price_list = fields.Many2one('product.pricelist', string='Lista de Precios')
    as_type = fields.Selection(as_type, string='Tipo de Promocion',default='NORMAL',required=True)

    PRICE_UNIT_USD = fields.Float('PRICE UNIT USD')
    COST_NIMAX_USD = fields.Float('COST NIMAX USD')
    DISCOUNT_AMOUNT_USD = fields.Float('DISCOUNT AMOUNT USD')