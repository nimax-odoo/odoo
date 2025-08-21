# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from functools import lru_cache
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_round, float_compare, OrderedSet,float_repr
from collections import defaultdict


class InheritProductTemplate(models.Model):
    _inherit = 'product.template'
    
    list_price_mx = fields.Float('Precio de Venta MX', digits='Product Price', default=0.0)
    
   