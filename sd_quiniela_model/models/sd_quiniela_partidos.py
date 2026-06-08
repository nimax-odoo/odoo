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

class SdQuinielaEquipo(models.Model):
    _name = 'sd.quiniela.partidos'
    _description = 'Quiniela partidos'

    name = fields.Char(string='Name')
    equipo_a_name = fields.Char(string='Equipo A')
    equipo_b_name = fields.Char(string='Equipo B')
    image_equipo_a = fields.Binary(string='Image Equipo A')
    image_equipo_b = fields.Binary(string='Image Equipo B')
    monto_minute = fields.Float(string='Monto por minuto')
    monto_marcador = fields.Float(string='Monto por marcador')
    monto_ganador = fields.Float(string='Monto por ganador')
    active = fields.Boolean(string='Active', default=False)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for vals in vals_list:
            vals['name'] = str(vals.get('equipo_a_name')) + ' vs ' + str(vals.get('equipo_b_name')) if vals.get('equipo_a_name') and vals.get('equipo_b_name') else 'Partido'
        return res