# -*- coding: utf-8 -*-

from odoo import models,fields,api
    
class as_partner_type(models.Model):
    _name="as.partner.type"
    _description = "Tipo de Clientes"
    
    name = fields.Char(string='Tipo')
