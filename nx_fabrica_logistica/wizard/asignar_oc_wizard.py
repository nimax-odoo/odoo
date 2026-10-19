from odoo import fields, models, _
from odoo.exceptions import UserError


class NxFabricaAsignarWizard(models.TransientModel):
    _name = 'nx.fabrica.asignar.wizard'
    _description = 'Asignar varias líneas a una OC existente'

    line_ids = fields.Many2many('sale.order.line', 'nx_fabrica_asignar_wiz_line_rel',
                                'wizard_id', 'line_id', string='Líneas')
    purchase_id = fields.Many2one('purchase.order', string='Orden de compra', required=True,
                                  domain=[('state', 'in', ('draft', 'sent'))])
    vendor_id = fields.Many2one(related='purchase_id.partner_id', string='Proveedor')

    def action_confirmar(self):
        self.ensure_one()
        validas = self.line_ids.filtered('nx_asignable')
        if not validas:
            raise UserError(_('Ninguna de las líneas seleccionadas está lista para asignar '
                              '(deben estar "Por asignar", "En OC sin confirmar" o con su OC cancelada).'))
        validas.write({'x_studio_oc_id': self.purchase_id.id})
        omitidas = len(self.line_ids) - len(validas)
        mensaje = _('%s línea(s) asignadas a %s.') % (len(validas), self.purchase_id.name)
        if omitidas:
            mensaje += _(' %s omitida(s) por su estado.') % omitidas
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': _('Listo'), 'message': mensaje, 'type': 'success', 'sticky': False,
                       'next': {'type': 'ir.actions.act_window_close'}},
        }
