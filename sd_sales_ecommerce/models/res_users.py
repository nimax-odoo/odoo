# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, time
from odoo.tools.safe_eval import safe_eval
from datetime import date, datetime, time
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, is_html_empty
from odoo.tools.translate import html_translate
from odoo.http import request
from odoo.tools import format_amount
#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class AsResUsers(models.Model):
    _inherit = 'res.users'

    sd_desc_percentaje = fields.Float(
        string='Porcentaje de Stock a Mostrar',
        default=1.0, related='partner_id.sd_desc_percentaje',  readonly=False,
        help='Porcentaje del stock real que se mostrará en la ecommerce. Si es 0.8, se mostrará el 80% del stock real. Si está vacío o es 1, se mostrará el 100%.'
    )
    
    sd_pricelist = fields.Many2one(
        'product.pricelist',
        string='Lista de Precios ecommerce', related='partner_id.sd_pricelist',readonly=False,
        help='Lista de precios que se utilizará por defecto en la API de Stock con precios. Si se deja vacío, se usará la lista de precios del cliente.'
    )

class AsResPartner(models.Model):
    _inherit = 'res.partner'

    sd_desc_percentaje = fields.Float(
        string='Porcentaje de Stock a Mostrar',
        default=1.0,
        help='Porcentaje del stock real que se mostrará en la ecommerce. Si es 0.8, se mostrará el 80% del stock real. Si está vacío o es 1, se mostrará el 100%.'
    )
    
    sd_pricelist = fields.Many2one(
        'product.pricelist',
        string='Lista de Precios ecommerce',
        help='Lista de precios que se utilizará por defecto en la API de Stock con precios. Si se deja vacío, se usará la lista de precios del cliente.'
    )