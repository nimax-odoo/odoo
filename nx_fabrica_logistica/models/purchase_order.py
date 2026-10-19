from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Solo las líneas que vienen de un pedido de venta (misma tabla que order_line, con filtro)
    nx_lineas_venta_ids = fields.One2many(
        'purchase.order.line', 'order_id', string='Líneas solicitadas a fábrica',
        domain=[('sale_line_id', '!=', False)], copy=False)
