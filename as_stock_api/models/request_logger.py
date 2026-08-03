# -*- coding: utf-8 -*-
import logging
import uuid
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)

class RequestLogger(models.Model):
    _name = 'request.logger'
    _description = 'Request Logger'
    
    
    name = fields.Char('Request ID', default=lambda self: str(uuid.uuid4()), readonly=True)
    user_id = fields.Many2one('res.users', string='Usuario', readonly=True)
    date = fields.Datetime('Fecha', default=fields.Datetime.now, readonly=True)
    json = fields.Text('JSON', readonly=True)
    response = fields.Text('Response', readonly=True)