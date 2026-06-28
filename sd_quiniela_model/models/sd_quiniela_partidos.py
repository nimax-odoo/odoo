# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)


class SdQuinielaEquipo(models.Model):
    _name = 'sd.quiniela.partidos'
    _description = 'Quiniela partidos'

    name = fields.Char(string='Name')
    equipo_a_name = fields.Char(string='Equipo A')
    equipo_b_name = fields.Char(string='Equipo B')
    image_equipo_a = fields.Binary(string='Image Equipo A')
    image_equipo_b = fields.Binary(string='Image Equipo B')

    # ===== MONTOS =====
    monto_minute = fields.Float(string='Monto por minuto')
    monto_marcador = fields.Float(string='Monto por marcador')
    monto_ganador = fields.Float(string='Monto por ganador')

    # ===== TIEMPO EXTRA =====
    # Un solo monto porque se paga por gol acertado en tiempo extra
    monto_tiempo_extra = fields.Float(string='Monto por gol Tiempo Extra')

    active = fields.Boolean(string='Active', default=False)

    def _prepare_partido_name(self, vals):
        equipo_a = vals.get('equipo_a_name')
        equipo_b = vals.get('equipo_b_name')

        if equipo_a and equipo_b:
            return '{} vs {}'.format(equipo_a, equipo_b)

        return 'Partido'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self._prepare_partido_name(vals)

        return super(SdQuinielaEquipo, self).create(vals_list)

    def write(self, vals):
        res = super(SdQuinielaEquipo, self).write(vals)

        if 'equipo_a_name' in vals or 'equipo_b_name' in vals:
            for record in self:
                if record.equipo_a_name and record.equipo_b_name:
                    record.name = '{} vs {}'.format(
                        record.equipo_a_name,
                        record.equipo_b_name
                    )
                else:
                    record.name = 'Partido'

        return res