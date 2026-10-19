from odoo import fields, models, _
from odoo.exceptions import UserError

from .nx_utils import nx_check_group


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Columnas del Excel que no existían en Odoo (nivel pedido)
    x_studio_fecha_oc_cliente = fields.Date(string='Fecha de la OC del cliente', copy=False)
    x_studio_proyecto_otras_marcas = fields.Char(string='Proyecto otras marcas', copy=False)
    x_studio_price_concession_zebra = fields.Char(string='Price Concession Zebra', copy=False)
    x_studio_dr_zebra = fields.Char(string='DR ZEBRA', copy=False)

    def write(self, vals):
        if 'x_studio_ordenado_a_fabricante' in vals or 'x_studio_marca' in vals:
            nx_check_group(self.env, 'group_nx_fabrica_pm',
                           _('Solo el PM puede marcar "Ordenado a Fabricante" o asignar la Marca.'))
        if 'x_studio_ordenado_a_fabricante' in vals and not vals['x_studio_ordenado_a_fabricante']:
            for order in self:
                asignadas = order.order_line.filtered('x_studio_oc_id')
                if asignadas:
                    raise UserError(_(
                        'No se puede quitar "Ordenado a Fabricante" en %s: ya hay líneas asignadas a una '
                        'orden de compra (%s). Logística debe quitarlas primero.')
                        % (order.name, ', '.join(asignadas.mapped('x_studio_oc_id.name'))))
        return super().write(vals)
