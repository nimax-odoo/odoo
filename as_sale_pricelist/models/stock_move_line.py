# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
   
class StockMoveLine(models.Model):
    _inherit="stock.move.line"

    location_final_id = fields.Many2one(
        'stock.location', 'Final Location',related="move_id.location_final_id")