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

class SdRegisterWinner(models.Model):
    _name = 'sd.register.winner'
    _description = 'Registrar Ganador'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Many2one('sd.quiniela.partidos', string='Partido')
    sequence = fields.Integer(string='Secuencia',default=1)
    proposticos_winner_ids = fields.One2many('sd.quiniela.data', 'register_winner_id', string='Pronósticos Ganadores')
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
    score_equipo_a = fields.Integer(string='Marcador Equipo A')
    score_equipo_b = fields.Integer(string='Marcador Equipo B')
    ganador = fields.Selection([('equipo_a', 'Equipo A'), ('equipo_b', 'Equipo B'), ('empate', 'Empate')], string='Ganador')
    winner_count = fields.Integer('Contactos', compute='_get_winner_count')
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
    
    def _get_winner_count(self):
        self.winner_count = len(self.proposticos_winner_ids)    
  
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
            'domain': [('id','in',pronosticos.ids)]
        })
        return action   
    
    def action_extract_winner(self):    
        for record in self:
            ganadores = record.compute_winner()
            # if not ganadores:
            #     raise UserError(_('No se encontraron ganadores para el partido seleccionado.'))
            message = 'Ganadores extraídos para el partido {}: {}'.format(record.name.name, ', '.join([g.name for g in ganadores]))
            record.message_post(body=message)

    
    def compute_winner(self):
        for record in self:
            for pronostico in record.proposticos_winner_ids:
                pronostico.is_winner = False
                pronostico.register_winner_id = False
            condiciones_or = []
            domain = []

            if record.min_0_9_t1:
                condiciones_or.append(('min_0_9_t1', '=', True))

            if record.min_10_18_t1:
                condiciones_or.append(('min_10_18_t1', '=', True))

            if record.min_19_27_t1:
                condiciones_or.append(('min_19_27_t1', '=', True))

            if record.min_28_36_t1:
                condiciones_or.append(('min_28_36_t1', '=', True))

            if record.min_37_45_t1:
                condiciones_or.append(('min_37_45_t1', '=', True))

            if record.min_0_9_t2:
                condiciones_or.append(('min_0_9_t2', '=', True))

            if record.min_10_18_t2:
                condiciones_or.append(('min_10_18_t2', '=', True))

            if record.min_19_27_t2:
                condiciones_or.append(('min_19_27_t2', '=', True))

            if record.min_28_36_t2:
                condiciones_or.append(('min_28_36_t2', '=', True))

            if record.min_37_45_t2:
                condiciones_or.append(('min_37_45_t2', '=', True))

            # Agregar los OR
            if len(condiciones_or) > 1:
                domain.extend(['|'] * (len(condiciones_or)-1))

            domain.extend(condiciones_or)
            domain.append(('equipo_a_id', '=', record.name.id))
            minutes_row = self.env['sd.quiniela.data'].sudo().search(domain)
            # ganador
            ganador = []
            if record.ganador:
                ganador.append(('ganador', '=', record.ganador))
            ganador.append(('equipo_a_id', '=', record.name.id))
            ganador_row = self.env['sd.quiniela.data'].sudo().search(ganador)

            score = []
            score.append(('score_equipo_a', '=', record.score_equipo_a))
            score.append(('score_equipo_b', '=', record.score_equipo_b))
            score.append(('equipo_a_id', '=', record.name.id))
                
            # ----------------------------------------------------------------------------
            score_row = self.env['sd.quiniela.data'].sudo().search(score)
            ganadores = (minutes_row | ganador_row | score_row)
            for ganador in ganadores:
                pronostico = ganador
                pronostico.is_winner = True
                pronostico.register_winner_id = record.id
            record.compute_puntaje_winner(ganadores)
            return ganadores

    def compute_puntaje_winner(self, ganadores):
        for record in self:
            for winner in ganadores:
                winner.puntaje = 0
                cantidad = 0
                ganador = False
                marcador = False
                minuto = False
                if winner.score_equipo_a == record.score_equipo_a and winner.score_equipo_b == record.score_equipo_b:
                    marcador = True
                if winner.ganador == record.ganador:
                    ganador = True
                if winner.min_0_9_t1 == record.min_0_9_t1 and record.min_0_9_t1 == True:
                    minuto = True
                    cantidad += record.min_0_9_t1_cant
                    if record.min_0_9_t1_cant == 0:
                        cantidad = 1
                if winner.min_10_18_t1 == record.min_10_18_t1 and record.min_10_18_t1 == True:
                    minuto = True
                    cantidad += record.min_10_18_t1_cant
                    if record.min_10_18_t1_cant == 0:
                        cantidad = 1
                if winner.min_19_27_t1 == record.min_19_27_t1 and record.min_19_27_t1 == True:
                    minuto = True
                    cantidad += record.min_19_27_t1_cant
                    if record.min_19_27_t1_cant == 0:
                        cantidad = 1
                if winner.min_28_36_t1 == record.min_28_36_t1 and record.min_28_36_t1 == True:
                    minuto = True
                    cantidad += record.min_28_36_t1_cant
                    if record.min_28_36_t1_cant == 0:
                        cantidad = 1
                if winner.min_37_45_t1 == record.min_37_45_t1 and record.min_37_45_t1 == True:
                    minuto = True
                    cantidad += record.min_37_45_t1_cant
                    if record.min_37_45_t1_cant == 0:
                        cantidad = 1
                if winner.min_0_9_t2 == record.min_0_9_t2 and record.min_0_9_t2 == True:
                    minuto = True
                    cantidad += record.min_0_9_t2_cant
                    if record.min_0_9_t2_cant == 0:
                        cantidad = 1
                if winner.min_10_18_t2 == record.min_10_18_t2 and record.min_10_18_t2 == True:
                    minuto = True
                    cantidad += record.min_10_18_t2_cant
                    if record.min_10_18_t2_cant == 0:
                        cantidad = 1
                if winner.min_19_27_t2 == record.min_19_27_t2 and record.min_19_27_t2 == True:
                    minuto = True
                    cantidad += record.min_19_27_t2_cant
                    if record.min_19_27_t2_cant == 0:
                        cantidad = 1
                if winner.min_28_36_t2 == record.min_28_36_t2 and record.min_28_36_t2 == True:
                    minuto = True
                    cantidad += record.min_28_36_t2_cant
                    if record.min_28_36_t2_cant == 0:
                        cantidad = 1
                if winner.min_37_45_t2 == record.min_37_45_t2 and record.min_37_45_t2 == True:
                    minuto = True
                    cantidad += record.min_37_45_t2_cant
                    if record.min_37_45_t2_cant == 0:
                        cantidad = 1
                if marcador:
                    winner.puntaje += record.name.monto_marcador
                if ganador:
                    winner.puntaje += record.name.monto_ganador
                if minuto:
                    winner.puntaje += record.name.monto_minute * cantidad