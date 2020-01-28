# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class as_product_template(models.Model):
    _inherit = 'product.template'
   
    as_proveedor = fields.Many2one(comodel_name='res.partner', string='Cliente - Proveedor')
    