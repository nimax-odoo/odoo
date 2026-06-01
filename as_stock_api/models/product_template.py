# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, time
from odoo.tools.safe_eval import safe_eval
from datetime import date, datetime, time
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError

#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_location_alternative(self, location_id):
        self.ensure_one()
        location_id = self.env['stock.location'].sudo().browse(location_id)
        company_id = location_id.company_id.id
        match = self.env['match.locations'].search([
            ('name', '=', company_id),
            ('location_id', '=', location_id.id)
        ], limit=1)
        return match.location_dest_id
    
    def compute_locations_adicionals(self, location_id):
        self.ensure_one()
        location_id = self.env['stock.location'].sudo().browse(location_id)
        company_id = location_id.company_id.id
        match = self.env['match.locations'].search([
            ('name_to', '=', company_id),
            ('location_dest_id', '=', location_id)
        ], limit=1)

        if not match:
            return 0.0

        product = self.with_context(location=match.location_id.id)

        return product.free_qty