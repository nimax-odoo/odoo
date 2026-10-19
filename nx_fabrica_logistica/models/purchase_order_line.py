from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Número de orden propio del fabricante (columna SALES ORDER del Excel).
    # Lo captura Logística en la línea de la OC; cambia en cada orden.
    x_studio_orden_fabricante = fields.Char(
        string='Orden del fabricante', copy=False, index=True,
        help='Número de orden / Sales Order que asigna el fabricante a este pedido.')
    # Nota por línea del lado de Compras (columna "Comentario Compras" del Excel)
    x_studio_nota_compra = fields.Text(string='Nota (Compras)', copy=False)

    def unlink(self):
        if self.env.context.get('nx_skip_oc_sync'):
            return super().unlink()
        # Si borran a mano la línea de la OC, la línea de venta vuelve a "Por asignar"
        liberar = self.env['sale.order.line']
        for pol in self:
            sl = pol.sale_line_id
            if sl and sl.x_studio_oc_id == pol.order_id:
                liberar |= sl
        res = super().unlink()
        if liberar:
            liberar.sudo().with_context(nx_skip_oc_sync=True).write(
                {'x_studio_oc_id': False, 'x_studio_fecha_asignacion': False})
        return res
