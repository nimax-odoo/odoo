# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from functools import lru_cache
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_round, float_compare, OrderedSet,float_repr
from collections import defaultdict
from datetime import datetime, timedelta

class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'
    
    def sd_update_pedimentos_a_lotes(self):
        """"
        Función para actualizar los pedimentos a los lotes relacionados a los costos de importación
        """
        for cost in self:
            if cost.state != 'done' or cost.company_id.country_id.code != 'MX':
                continue

            lots = cost.picking_ids.move_line_ids.filtered(
                lambda ml: (
                    ml.product_id.l10n_mx_edi_can_use_customs_invoicing
                    and ml.state == 'done'
                    and not ml.lot_id.l10n_mx_edi_landed_cost_id
                )
            ).mapped("lot_id")
            cost.message_post(
                body=_(
                    "Actualizando pedimentos a los lotes relacionados a los costos de importación: %s",
                    ", ".join(lots.mapped("name")),
                )
            )
            if lots:
                lots.l10n_mx_edi_landed_cost_id = cost

