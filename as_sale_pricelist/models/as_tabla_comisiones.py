# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class AsTablaComisiones(models.Model):
    _name = "as.tabla.comisiones"
    _description = "Tabla de Comisiones a Vendedores"

    name = fields.Char('Nombre', compute='_compute_name', store=True)
    as_desde = fields.Float('Desde USD')
    as_hasta = fields.Float('Hasta USD')
    as_comision = fields.Float('Comision Pesos MXP')
    as_division = fields.Boolean('Calculo por division',default=False)
    
    @api.depends('as_desde', 'as_hasta', 'as_comision')
    def _compute_name(self):
        for record in self:
            record.name = f"Desde {record.as_desde} hasta {record.as_hasta} MXP: {record.as_comision}"
    
    @api.model
    def calculate_comision(self, amount):
        """Calcula la comisión basada en el monto usando la tabla de comisiones."""
        tabla_comisiones = self.search([
            ('as_desde', '<=', amount),
            ('as_hasta', '>=', amount)
        ], limit=1)
        
        if not tabla_comisiones:
            return 0
        
        if tabla_comisiones.as_division:
            # Si es cálculo por división
            return amount * tabla_comisiones.as_comision / 100
        else:
            # Si es valor fijo
            return tabla_comisiones.as_comision