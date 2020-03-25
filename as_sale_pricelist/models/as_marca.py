# -*- coding: utf-8 -*-

from odoo import models,fields,api
    
class as_marca(models.Model):
    _name = 'as.marca'
    _description = "Marca"

    name = fields.Char(string="Marca")    