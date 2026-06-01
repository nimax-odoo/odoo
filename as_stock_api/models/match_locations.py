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
class MatchLocations(models.Model):
    _name = 'match.locations'
    _description = 'Match Locations'
    
    name = fields.Many2one('res.company', string='Compañia Origen')
    name_to = fields.Many2one('res.company', string='Compañia Destino')
    location_id = fields.Many2one('stock.location', string='Location', domain="[('company_id', '=', name)]")
    location_dest_id = fields.Many2one('stock.location', string='Destination Location', domain="[('company_id', '=', name_to)]")