# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class AsProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    as_active_promotion = fields.Boolean('Promoción Activa', default=False)
    as_date_start = fields.Date('Fecha Inicio')
    as_date_end = fields.Date('Fecha Fin') 