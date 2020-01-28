# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models,fields,api
    
class SaleOrderLine(models.Model):
    _inherit="product.pricelist.item"
    
    as_utilidad = fields.Float(string='Utilidad esperada') # Utilidad esperada
