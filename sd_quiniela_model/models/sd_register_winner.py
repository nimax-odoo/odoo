# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import logging
from odoo.exceptions import UserError

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
    # CANTIDAD DE GOLES EN TIEMPO EXTRA
    # =========================
    tiempo_extra_1_cant = fields.Integer(string='Goles Tiempo Extra 1')
    tiempo_extra_2_cant = fields.Integer(string='Goles Tiempo Extra 2')

    def _get_winner_count(self):
        for record in self:
            record.winner_count = len(record.proposticos_winner_ids)

    def action_open_ganadores(self):
        self.ensure_one()

        action = {
            'res_model': 'sd.quiniela.data',
            'type': 'ir.actions.act_window',
            'name': _("Ganadores"),
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.proposticos_winner_ids.ids)],
        }

        return action

    def action_extract_winner(self):
        for record in self:
            ganadores = record.compute_winner()

            nombres = []
            for ganador in ganadores:
                if ganador.name:
                    nombres.append(ganador.name)
                elif ganador.quiniela_pronostico_id and ganador.quiniela_pronostico_id.partner_id:
                    nombres.append(ganador.quiniela_pronostico_id.partner_id.name)
                else:
                    nombres.append(str(ganador.id))

            message = 'Ganadores extraídos para el partido {}: {}'.format(
                record.name.name if record.name else '',
                ', '.join(nombres)
            )

            record.message_post(body=message)

    # =========================
    # HELPERS
    # =========================
    def _get_int_field_value(self, record, field_name):
        """
        Regresa el valor entero de un campo si existe.
        Sirve para evitar error si todavía no agregaste campos nuevos en sd.quiniela.data.
        """
        if field_name in record._fields:
            return getattr(record, field_name) or 0
        return 0

    def _get_bool_field_value(self, record, field_name):
        """
        Regresa el valor booleano de un campo si existe.
        """
        if field_name in record._fields:
            return bool(getattr(record, field_name))
        return False

    def _get_monto_tiempo_extra(self, partido):
        """
        Regresa el monto por gol de tiempo extra.
        Se usa un solo campo: monto_tiempo_extra.
        """
        return partido.monto_tiempo_extra or 0


    def _sumar_minuto_si_acerto(self, winner, record, campo_bool, campo_cantidad):
        """
        Si el participante marcó el rango y en el resultado real también aparece,
        suma la cantidad de goles de ese rango.

        Si el resultado tiene cantidad 0 pero el check está activo,
        suma 1 como respaldo para no dejarlo en cero.
        """
        participante_marco = self._get_bool_field_value(winner, campo_bool)
        resultado_marco = self._get_bool_field_value(record, campo_bool)

        if participante_marco and resultado_marco:
            cantidad = self._get_int_field_value(record, campo_cantidad)

            if cantidad == 0:
                cantidad = 1

            return cantidad

        return 0

    def _sumar_tiempo_extra_si_acerto(self, winner, record, campo_bool, campo_cantidad):
        """
        Tiempo extra:
        - El participante debe haber marcado el tiempo extra.
        - El resultado real debe tener marcado el tiempo extra.
        - Los goles del participante deben ser iguales a los goles reales.
        - Se paga por cantidad de goles reales acertados.
        """
        participante_marco = self._get_bool_field_value(winner, campo_bool)
        resultado_marco = self._get_bool_field_value(record, campo_bool)

        if not participante_marco or not resultado_marco:
            return 0

        goles_participante = self._get_int_field_value(winner, campo_cantidad)
        goles_reales = self._get_int_field_value(record, campo_cantidad)

        if goles_participante == goles_reales and goles_reales > 0:
            return goles_reales

        return 0

    def compute_winner(self):
        for record in self:
            if not record.name:
                raise UserError(_('Debe seleccionar un partido.'))

            # =========================
            # BUSCAR TODOS LOS PRONÓSTICOS DEL PARTIDO
            # =========================
            pronosticos = self.env['sd.quiniela.data'].sudo().search([
                ('equipo_a_id', '=', record.name.id)
            ])

            # =========================
            # LIMPIAR RESULTADOS ANTERIORES DE ESTE PARTIDO
            # =========================
            pronosticos.write({
                'is_winner': False,
                'register_winner_id': False,
                'puntaje': 0,
            })

            # =========================
            # CALCULAR PUNTAJE A TODOS
            # =========================
            record.compute_puntaje_winner(pronosticos)

            # =========================
            # MARCAR GANADORES SOLO SI TIENEN PUNTAJE
            # =========================
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
                cantidad_tiempo_extra = 0

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
                # MINUTOS NORMALES - TIEMPO 1
                # =========================
                cantidad_minutos += self._sumar_minuto_si_acerto(
                    winner, record, 'min_0_9_t1', 'min_0_9_t1_cant'
                )
                cantidad_minutos += self._sumar_minuto_si_acerto(
                    winner, record, 'min_10_18_t1', 'min_10_18_t1_cant'
                )
                cantidad_minutos += self._sumar_minuto_si_acerto(
                    winner, record, 'min_19_27_t1', 'min_19_27_t1_cant'
                )
                cantidad_minutos += self._sumar_minuto_si_acerto(
                    winner, record, 'min_28_36_t1', 'min_28_36_t1_cant'
                )
                cantidad_minutos += self._sumar_minuto_si_acerto(
                    winner, record, 'min_37_45_t1', 'min_37_45_t1_cant'
                )

                # =========================
                # MINUTOS NORMALES - TIEMPO 2
                # =========================
                cantidad_minutos += self._sumar_minuto_si_acerto(
                    winner, record, 'min_0_9_t2', 'min_0_9_t2_cant'
                )
                cantidad_minutos += self._sumar_minuto_si_acerto(
                    winner, record, 'min_10_18_t2', 'min_10_18_t2_cant'
                )
                cantidad_minutos += self._sumar_minuto_si_acerto(
                    winner, record, 'min_19_27_t2', 'min_19_27_t2_cant'
                )
                cantidad_minutos += self._sumar_minuto_si_acerto(
                    winner, record, 'min_28_36_t2', 'min_28_36_t2_cant'
                )
                cantidad_minutos += self._sumar_minuto_si_acerto(
                    winner, record, 'min_37_45_t2', 'min_37_45_t2_cant'
                )

                # =========================
                # SUMAR PUNTAJE POR MINUTOS NORMALES
                # =========================
                if cantidad_minutos > 0:
                    winner.puntaje += record.name.monto_minute * cantidad_minutos

                # =========================
                # TIEMPO EXTRA 1
                # =========================
                cantidad_tiempo_extra += self._sumar_tiempo_extra_si_acerto(
                    winner, record, 'tiempo_extra_1', 'tiempo_extra_1_cant'
                )

                # =========================
                # TIEMPO EXTRA 2
                # =========================
                cantidad_tiempo_extra += self._sumar_tiempo_extra_si_acerto(
                    winner, record, 'tiempo_extra_2', 'tiempo_extra_2_cant'
                )

                # =========================
                # SUMAR PUNTAJE POR TIEMPO EXTRA
                # =========================
                if cantidad_tiempo_extra > 0:
                    monto_tiempo_extra = self._get_monto_tiempo_extra(record.name)
                    winner.puntaje += monto_tiempo_extra * cantidad_tiempo_extra