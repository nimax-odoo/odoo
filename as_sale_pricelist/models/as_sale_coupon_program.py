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
    COSTO = fields.Float('% COSTO')

    # PROMO_count = fields.Float('PROMO', help='number of times, this promo can be applied')
    # PROMO_countdown = fields.Float('PROMO COUNTDOWN', help='a countdown field ', readonly=True)
    # PROMO_show = fields.Float('No Of Times Coupon Applied', help='show the numbers of time applied', readonly=True)

    # for gift
    tf_max_gifted_qty = fields.Float('MAX GIFT QTY')
    tf_gifted_qty = fields.Float('Gifted', readonly=True)
    tf_balance = fields.Float('Balance', compute='_compute_balance')

    def _compute_balance(self):
        for rec in self:
            rec.tf_balance = rec.tf_max_gifted_qty - rec.tf_gifted_qty
    # end