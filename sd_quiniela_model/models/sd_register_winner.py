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


class SdRegisterWinner(models.Model):
    _name = 'sd.register.winner'
    _description = 'Registrar Ganador'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Many2one('sd.quiniela.partidos', string='Partido')
    sequence = fields.Integer(string='Secuencia', default=1)

    proposticos_winner_ids = fields.One2many(
        'sd.quiniela.data',
        'register_winner_id',
        string='Pronósticos Ganadores'
    )

    # =========================
    # MINUTOS TIEMPO 1
    # =========================
    min_0_9_t1 = fields.Boolean(string='0-9 min T1')
    min_10_18_t1 = fields.Boolean(string='10-18 min T1')
    min_19_27_t1 = fields.Boolean(string='19-27 min T1')
    min_28_36_t1 = fields.Boolean(string='28-36 min T1')
    min_37_45_t1 = fields.Boolean(string='37-45 min T1')

    # =========================
    # MINUTOS TIEMPO 2
    # =========================
    min_0_9_t2 = fields.Boolean(string='0-9 min T2')
    min_10_18_t2 = fields.Boolean(string='10-18 min T2')
    min_19_27_t2 = fields.Boolean(string='19-27 min T2')
    min_28_36_t2 = fields.Boolean(string='28-36 min T2')
    min_37_45_t2 = fields.Boolean(string='37-45 min T2')

    # =========================
    # TIEMPO EXTRA
    # =========================
    tiempo_extra_1 = fields.Boolean(string='Tiempo Extra 1')
    tiempo_extra_2 = fields.Boolean(string='Tiempo Extra 2')

    # =========================
    # MARCADOR Y GANADOR
    # =========================
    score_equipo_a = fields.Integer(string='Marcador Equipo A')
    score_equipo_b = fields.Integer(string='Marcador Equipo B')

    ganador = fields.Selection([
        ('equipo_a', 'Equipo A'),
        ('equipo_b', 'Equipo B'),
        ('empate', 'Empate')
    ], string='Ganador')

    winner_count = fields.Integer('Contactos', compute='_get_winner_count')

    # =========================
    # CANTIDAD DE GOLES POR MINUTO
    # =========================
    min_0_9_t1_cant = fields.Integer(string='Goles 0-9 min T1')
    min_10_18_t1_cant = fields.Integer(string='Goles 10-18 min T1')
    min_19_27_t1_cant = fields.Integer(string='Goles 19-27 min T1')
    min_28_36_t1_cant = fields.Integer(string='Goles 28-36 min T1')
    min_37_45_t1_cant = fields.Integer(string='Goles 37-45 min T1')

    min_0_9_t2_cant = fields.Integer(string='Goles 0-9 min T2')
    min_10_18_t2_cant = fields.Integer(string='Goles 10-18 min T2')
    min_19_27_t2_cant = fields.Integer(string='Goles 19-27 min T2')
    min_28_36_t2_cant = fields.Integer(string='Goles 28-36 min T2')
    min_37_45_t2_cant = fields.Integer(string='Goles 37-45 min T2')

    # =========================
    # GOLES TIEMPO EXTRA
    # SOLO AQUÍ, EN REGISTRO GANADOR.
    # EL USUARIO NO CAPTURA ESTOS GOLES.
    # =========================
    tiempo_extra_1_cant = fields.Integer(string='Goles Tiempo Extra 1')
    tiempo_extra_2_cant = fields.Integer(string='Goles Tiempo Extra 2')
    
    def _get_winner_count(self):
        for record in self:
            record.winner_count = len(record.proposticos_winner_ids)
  
    def action_open_ganadores(self):
        self.ensure_one()
        pronosticos = self.proposticos_winner_ids

        action = {
            'res_model': 'sd.quiniela.data',
            'type': 'ir.actions.act_window',
            'name': _("Ganadores"),
        }

        action.update({
            'view_mode': 'list,form',
            'domain': [('id', 'in', pronosticos.ids)]
        })

        return action
    
    def action_extract_winner(self):    
        for record in self:
            ganadores = record.compute_winner()

            message = 'Ganadores extraídos para el partido {}: {}'.format(
                record.name.name,
                ', '.join([g.name for g in ganadores])
            )

            record.message_post(body=message)

    def compute_winner(self):
        for record in self:
            if not record.name:
                raise UserError(_('Debe seleccionar un partido.'))

            # Buscar TODOS los pronósticos del partido.
            # Se calcula TODO: minutos + tiempo extra + ganador + marcador.
            pronosticos = self.env['sd.quiniela.data'].sudo().search([
                ('equipo_a_id', '=', record.name.id)
            ])

            # Limpiar resultados anteriores del mismo partido
            pronosticos.write({
                'is_winner': False,
                'register_winner_id': False,
                'puntaje': 0,
            })

            # Calcular puntaje de todos los pronósticos
            record.compute_puntaje_winner(pronosticos)

            # Ganadores son los que obtuvieron puntaje mayor a 0
            ganadores = pronosticos.filtered(lambda p: p.puntaje > 0)

            ganadores.write({
                'is_winner': True,
                'register_winner_id': record.id,
            })

            return ganadores

    def compute_puntaje_winner(self, ganadores):
        for record in self:
            for winner in ganadores:
                winner.puntaje = 0

                cantidad_minutos = 0
                cantidad_extra = 0

                # =========================
                # MARCADOR EXACTO
                # =========================
                if (
                    winner.score_equipo_a == record.score_equipo_a
                    and winner.score_equipo_b == record.score_equipo_b
                ):
                    winner.puntaje += record.name.monto_marcador

                # =========================
                # GANADOR
                # =========================
                if winner.ganador == record.ganador and record.ganador:
                    winner.puntaje += record.name.monto_ganador

                # =========================
                # MINUTOS TIEMPO 1
                # =========================
                if winner.min_0_9_t1 == record.min_0_9_t1 and record.min_0_9_t1 == True:
                    cantidad_minutos += record.min_0_9_t1_cant
                    if record.min_0_9_t1_cant == 0:
                        cantidad_minutos += 1

                if winner.min_10_18_t1 == record.min_10_18_t1 and record.min_10_18_t1 == True:
                    cantidad_minutos += record.min_10_18_t1_cant
                    if record.min_10_18_t1_cant == 0:
                        cantidad_minutos += 1

                if winner.min_19_27_t1 == record.min_19_27_t1 and record.min_19_27_t1 == True:
                    cantidad_minutos += record.min_19_27_t1_cant
                    if record.min_19_27_t1_cant == 0:
                        cantidad_minutos += 1

                if winner.min_28_36_t1 == record.min_28_36_t1 and record.min_28_36_t1 == True:
                    cantidad_minutos += record.min_28_36_t1_cant
                    if record.min_28_36_t1_cant == 0:
                        cantidad_minutos += 1

                if winner.min_37_45_t1 == record.min_37_45_t1 and record.min_37_45_t1 == True:
                    cantidad_minutos += record.min_37_45_t1_cant
                    if record.min_37_45_t1_cant == 0:
                        cantidad_minutos += 1

                # =========================
                # MINUTOS TIEMPO 2
                # =========================
                if winner.min_0_9_t2 == record.min_0_9_t2 and record.min_0_9_t2 == True:
                    cantidad_minutos += record.min_0_9_t2_cant
                    if record.min_0_9_t2_cant == 0:
                        cantidad_minutos += 1

                if winner.min_10_18_t2 == record.min_10_18_t2 and record.min_10_18_t2 == True:
                    cantidad_minutos += record.min_10_18_t2_cant
                    if record.min_10_18_t2_cant == 0:
                        cantidad_minutos += 1

                if winner.min_19_27_t2 == record.min_19_27_t2 and record.min_19_27_t2 == True:
                    cantidad_minutos += record.min_19_27_t2_cant
                    if record.min_19_27_t2_cant == 0:
                        cantidad_minutos += 1

                if winner.min_28_36_t2 == record.min_28_36_t2 and record.min_28_36_t2 == True:
                    cantidad_minutos += record.min_28_36_t2_cant
                    if record.min_28_36_t2_cant == 0:
                        cantidad_minutos += 1

                if winner.min_37_45_t2 == record.min_37_45_t2 and record.min_37_45_t2 == True:
                    cantidad_minutos += record.min_37_45_t2_cant
                    if record.min_37_45_t2_cant == 0:
                        cantidad_minutos += 1

                # =========================
                # SUMAR PUNTAJE POR MINUTOS NORMALES
                # =========================
                if cantidad_minutos:
                    winner.puntaje += record.name.monto_minute * cantidad_minutos

                # =========================
                # TIEMPO EXTRA 1
                # El usuario solo marca TE1.
                # Los goles se toman del Registro Ganador.
                # =========================
                if winner.tiempo_extra_1 == record.tiempo_extra_1 and record.tiempo_extra_1 == True:
                    cantidad_extra += record.tiempo_extra_1_cant

                # =========================
                # TIEMPO EXTRA 2
                # El usuario solo marca TE2.
                # Los goles se toman del Registro Ganador.
                # =========================
                if winner.tiempo_extra_2 == record.tiempo_extra_2 and record.tiempo_extra_2 == True:
                    cantidad_extra += record.tiempo_extra_2_cant

                # =========================
                # SUMAR PUNTAJE POR TIEMPO EXTRA
                # =========================
                if cantidad_extra:
                    winner.puntaje += record.name.monto_tiempo_extra * cantidad_extra