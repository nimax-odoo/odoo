# -*- coding: utf-8 -*-
# Modelo que extiende product.template para mostrar el stock disponible en el eCommerce.

from odoo import models, fields

class AsProductTemplate(models.Model):
    _inherit = 'product.template'

    # Campo que muestra la cantidad disponible en inventario
    as_qty_available = fields.Float(
        string="Cantidad Disponible",
        compute='_as_compute_qty_available',
        readonly=True,
    )

    def _as_compute_qty_available(self):
        """
        Método para calcular la cantidad disponible de producto.
        """
        for as_product in self:
            as_product.as_qty_available = as_product.sudo().qty_available
