# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from functools import lru_cache
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_round, float_compare, OrderedSet,float_repr
from collections import defaultdict
from datetime import datetime, timedelta

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.depends('move_ids.product_uom_qty','move_ids.quantity','state','picking_type_code','write_date')
    def _compute_id_notify_assigned(self):
        for pick in self:
            pick.id_notify_assigned = False

    id_notify_assigned = fields.Boolean('Notificado Picking Listo', default=False, compute='_compute_id_notify_assigned',store=True)



    def _notificar_picking_assigned(self):
        pickings2 = self.env['stock.picking'].search([('id_notify_assigned','=',False),('sale_id.is_picking_assigned','=',True)])
        for pick2 in pickings2:
            pick2.sale_id.is_picking_assigned = False
        fecha = fields.Date.from_string('2025-01-01')
        pickings = self.env['stock.picking'].search([('id_notify_assigned','=',True),('sale_id.date_order','>=',fecha)])
        for pick in pickings:
            pick.sale_id.is_picking_assigned = True
            template = self.env.ref('sd_sales_change.email_template_notificar_assigned', raise_if_not_found=False)
            if template:
                template.sudo().send_mail(pick.id, force_send=True)
            # activity_vals = []
            # activity_type = self.env.ref('mail.mail_activity_data_todo')
            # model_id = self.env.ref('stock.model_stock_picking').id
            # activity_vals.append({
            #     'activity_type_id': activity_type.id,
            #     'automated': True,
            #     'date_deadline': datetime.now(),
            #     'note': "Tiene que marcar la orden de entrega como 'Hecho' en el sistema Odoo.",
            #     'user_id': pick.sale_id.user_id.id,
            #     'res_id': pick.id,
            #     'res_model_id': model_id,
            # })
            # self.env['mail.activity'].create(activity_vals)
        return True
    
class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    lot_id = fields.Many2one(
        'stock.lot', 'Número de lote/serie',
        domain="[('product_id', '=', product_id),('company_id', '=', company_id)]", check_company=True)

class Stockquants(models.Model):
    _inherit = 'stock.quant'

    def _get_available_quantity(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False, allow_negative=False):
        """ HEREDADA PARA FILTRAR LOTES POR COMPAÑIA, DADO QUE LA UBICACION DE QUANTS DEPENDE DE LA UBICACION, PERO ESTA PUEDE TENER LOTES DE OTRAS COMPAÑIAS
        """
        self = self.sudo()
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)
        rounding = product_id.uom_id.rounding
        if product_id.tracking == 'none':
            available_quantity = sum(quants.mapped('quantity')) - sum(quants.mapped('reserved_quantity'))
            if allow_negative:
                return available_quantity
            else:
                return available_quantity if float_compare(available_quantity, 0.0, precision_rounding=rounding) >= 0.0 else 0.0
        else:
            #seleccionamos solo lotes d ela compañia del lote
            for quant in quants:
                if quant.lot_id and quant.lot_id.company_id != quant.company_id:
                    quants -= quant
            availaible_quantities = {lot_id: 0.0 for lot_id in list(set(quants.mapped('lot_id'))) + ['untracked']}
            for quant in quants:
                if not quant.lot_id and strict and lot_id:
                    continue
                if not quant.lot_id:
                    availaible_quantities['untracked'] += quant.quantity - quant.reserved_quantity
                else:
                    availaible_quantities[quant.lot_id] += quant.quantity - quant.reserved_quantity
            if allow_negative:
                return sum(availaible_quantities.values())
            else:
                return sum([available_quantity for available_quantity in availaible_quantities.values() if float_compare(available_quantity, 0, precision_rounding=rounding) > 0])