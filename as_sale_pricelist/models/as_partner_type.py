# -*- coding: utf-8 -*-

from odoo import models,fields,api
    
class as_partner_type(models.Model):
    _name="as.partner.type"
    _description = "Tipo de Clientes"
    
    name = fields.Char(string='Tipo')
    # as_marca = fields.Many2one('as.marca', string='Marca')
    # as_proveedor = fields.Many2one('res.partner', string='Proveedor')
