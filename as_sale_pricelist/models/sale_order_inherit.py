# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models,fields,api
    
class SaleOrderLine(models.Model):
    _inherit="sale.order.line"
    
    margin2 = fields.Float('Margen 2', digits='Product Price', default=0)
        
    def pricelist_apply(self):
        return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.order.pricelist.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
            }

        