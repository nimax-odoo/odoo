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
# from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class SdQuinielaData(models.Model):
    _name = 'sd.quiniela.data'
    _description = 'Quiniela Data'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Name')
    quiniela_pronostico_id = fields.Many2one('sd.quiniela.pronostico', string='Quiniela pronostico')
    equipo_a_id = fields.Many2one('sd.quiniela.partidos', string='Partidos')

    # ===== MINUTOS =====
    min_0_9_t1 = fields.Boolean(string='0-9 min T1')
    min_10_18_t1 = fields.Boolean(string='10-18 min T1')
    min_19_27_t1 = fields.Boolean(string='19-27 min T1')
    min_28_36_t1 = fields.Boolean(string='28-36 min T1')
    min_37_45_t1 = fields.Boolean(string='37-45 min T1')

    min_0_9_t2 = fields.Boolean(string='0-9 min T2')
    min_10_18_t2 = fields.Boolean(string='10-18 min T2')
    min_19_27_t2 = fields.Boolean(string='19-27 min T2')
    min_28_36_t2 = fields.Boolean(string='28-36 min T2')
    min_37_45_t2 = fields.Boolean(string='37-45 min T2')

    # ===== TIEMPO EXTRA =====
    tiempo_extra_1 = fields.Boolean(string='Tiempo Extra 1')
    tiempo_extra_2 = fields.Boolean(string='Tiempo Extra 2')

    # ===== GOLES TIEMPO EXTRA =====

    # ===== RESULTADO =====
    score_equipo_a = fields.Integer(string='Marcador Equipo A')
    score_equipo_b = fields.Integer(string='Marcador Equipo B')
    ganador = fields.Selection([
        ('equipo_a', 'Equipo A'),
        ('equipo_b', 'Equipo B'),
        ('empate', 'Empate')
    ], string='Ganador')

    # ===== PUNTAJE =====
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    puntaje = fields.Monetary(string='Puntaje', currency_field='currency_id')

    register_winner_id = fields.Many2one('sd.register.winner', string='Registro Ganador')
    is_winner = fields.Boolean(string='Es Ganador', default=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = str(vals.get('equipo_a_id')) if vals.get('equipo_a_id') else 'Pronóstico'

        res = super().create(vals_list)
        return res