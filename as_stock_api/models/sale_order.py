# -*- coding: utf-8 -*-
import logging
import uuid
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    sd_waybills = fields.Char('Seguimiento Guia Remisión')
    sd_carrier_id = fields.Many2one('delivery.carrier',string='Seguimiento Guia Remisión')