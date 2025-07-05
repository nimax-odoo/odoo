# -*- coding: utf-8 -*-

from odoo import models,fields,api
    
class as_marca(models.Model):
    _name = 'as.marca'
    _description = "Marca"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Marca", tracking=True)
    active = fields.Boolean(default=True, tracking=True)    