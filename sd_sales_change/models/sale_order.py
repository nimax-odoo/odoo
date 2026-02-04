# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from functools import lru_cache
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_round, float_compare, OrderedSet,float_repr
from collections import defaultdict


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    is_picking_assigned = fields.Boolean('Picking Asignado', default=False)

    def action_cancel(self):
        """ Heredada para evitar que impida cancelar la orden si esta bloqueado. """
        # if any(order.locked for order in self):
        #     raise UserError(_("You cannot cancel a locked order. Please unlock it first."))
        return self._action_cancel()