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
    
    @api.model
    @api.readonly
    def web_name_search(self, name, specification, domain=None, operator='ilike', limit=100):
        id_name_pairs = self.name_search(name, domain, operator, limit)
        if len(specification) == 1 and 'display_name' in specification:
            return [{'id': id, 'display_name': name, '__formatted_display_name': self.with_context(formatted_display_name=False).browse(id).display_name} for id, name in id_name_pairs]
        records = self.browse([id for id, _ in id_name_pairs])
        return records.web_read(specification)

class InheritProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    @api.readonly
    def web_name_search(self, name, specification, domain=None, operator='ilike', limit=100):
        id_name_pairs = self.name_search(name, domain, operator, limit)
        if len(specification) == 1 and 'display_name' in specification:
            return [{'id': id, 'display_name': name, '__formatted_display_name': self.with_context(formatted_display_name=False).browse(id).display_name} for id, name in id_name_pairs]
        records = self.browse([id for id, _ in id_name_pairs])
        return records.web_read(specification)