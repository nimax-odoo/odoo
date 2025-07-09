# -*- coding: utf-8 -*-

from odoo import models,fields,api
    
class as_marca(models.Model):
    _name = 'as.marca'
    _description = "Marca"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Marca", tracking=True)
    active = fields.Boolean(default=True, tracking=True)    

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
     
    def _prepare_new_lot_vals(self):
        vals = super()._prepare_new_lot_vals()
        vals['company_id'] = self.company_id.id
        return vals