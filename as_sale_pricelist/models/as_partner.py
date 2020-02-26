# -*- coding: utf-8 -*-

from odoo import models,fields,api
    
class as_res_partner(models.Model):
    _inherit="res.partner"
    
    as_partner_type = fields.Many2many('as.partner.type', string='Tipo de Cliente')