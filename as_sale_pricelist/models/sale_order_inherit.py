# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models,fields,api
    
class SaleOrderLine(models.Model):
    _inherit="sale.order.line"
    
    margin2 = fields.Float('Margen 2', digits='Product Price', default=0)
    as_pricelist_id = fields.Many2one('product.pricelist', string='Lista de Precios')
        
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

    def product_promo_apply_dis_value(self):
        return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'as.sale.order.promo.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'product_promo_apply_dis_value':'product_promo_apply_dis_value'},
            }

    def prduct_promo_apply_dis_per(self):
        return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'as.sale.order.promo.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'prduct_promo_apply_dis_per':'prduct_promo_apply_dis_per'},
            }