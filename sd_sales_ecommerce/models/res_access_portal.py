# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, time
from odoo.tools.safe_eval import safe_eval
from datetime import date, datetime, time
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.tools import format_amount
import operator as py_operator
import time
#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class ResAccessPortal(models.Model):
    _name = "res.access.portal"
    _description = "Access Portal"
    
    name = fields.Char(string="Name")
    vat = fields.Char(string="VAT")
    email = fields.Char(string="Email")
    notas = fields.Char(string="Notas")
    partner_id = fields.Many2one('res.partner', string='Customer')
 