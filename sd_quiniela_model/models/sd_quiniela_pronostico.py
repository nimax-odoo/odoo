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

class SdQuinielaData(models.Model):
    _name = 'sd.quiniela.pronostico'
    _description = 'Quiniela Data'
    
    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', string='Participante')
    datas_ids = fields.One2many('sd.quiniela.data', 'quiniela_pronostico_id', string='Quiniela Partidos')
    
    

    
    
    def action_pronosticos_partidos(self):
        for record in self:
            record.name = 'Pronóstico ' + str(record.partner_id.name) if record.partner_id else 'Pronóstico'
            record.datas_ids.unlink()  # Eliminar los registros existentes antes de crear nuevos
            pronosticos = self.env['sd.quiniela.partidos'].sudo().search([('active', '=', True)])
            if not pronosticos:
                raise UserError(_('Ya existen pronósticos para participantes.'))
            for pronostico in pronosticos:
                self.env['sd.quiniela.data'].create({
                    'name': 'Pronóstico ' + str(record.partner_id.name),
                    'quiniela_pronostico_id': record.id,
                    'equipo_a_id': pronostico.id,
                })

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for vals in vals_list:
            vals['name'] = str(vals.get('partner_id')) if vals.get('partner_id') else 'Pronóstico'
        return res