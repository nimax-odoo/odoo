# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import _, api, fields, models


_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = 'stock.quant'


    @api.model
    def _get_inventory_fields_create(self):
        res = super()._get_inventory_fields_create()
        return ['sd_description'] + res