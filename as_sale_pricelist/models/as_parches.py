# -*- coding: utf-8 -*-
# Part of Ahorasoft.

from odoo import models, fields, api

class as_res_partner_patch(models.Model):
    """
    Parche para añadir campos faltantes a res.partner
    
    Propósito: Solucionar error de campo faltante en la interfaz
    """
    _inherit = "res.partner"
    
    partner_company_registry_placeholder = fields.Char(
        string="Placeholder para Registro de Compañía",
        help="Campo placeholder para evitar errores en la interfaz"
    )
