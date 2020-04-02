# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models,fields,api
    
class SaleOrderLine(models.Model):
    _inherit="sale.order.line"
    
    margin2 = fields.Float('Margen 2', digits='Product Price', default=0)
    as_pricelist_id = fields.Many2one('product.pricelist', string='Lista de Precios')

    RECALCULATED_PRICE_UNIT = fields.Float('RECALCULATED PRICE UNIT')
    NIMAX_PRICE_MXP = fields.Float('NIMAX PRICE MXP')
    COST_NIMAX_USD = fields.Float('COST NIMAX USD')
    COST_NIMAX_MXP = fields.Float('COST NIMAX MXP')
    MARGIN_MXP = fields.Float('MARGIN MXP')
    MARGIN_USD = fields.Float('MARGIN USD')
    TOTAL_USD = fields.Float('TOTAL USD')
    TOTAL_MXP = fields.Float('TOTAL MXP')

    coupon_ids = fields.Many2many('sale.coupon.program', string='Coupons')
    RECALCULATED_COST_NIMAX_USD = fields.Float('RECALCULATED COST NIMAX USD')
        
    # apply pricelist
    def pricelist_apply(self):
        return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.order.pricelist.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
            }
        
    # apply promo
    def promo_apply(self):
        return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'as.sale.order.promo.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'promo_apply_dis_per': 'promo_apply_dis_per'},
            }
    
class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()

        for rec in self:
            for line in rec.order_line:
                for promo in line.coupon_ids:
                    promo.rule_min_quantity -= 1

        return res