from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

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
