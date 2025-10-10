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

    def _compute_id_notify_assigned(self):
        for pick in self:
            igual = True
            for move_line in pick.move_ids_without_package:
                if move_line.product_uom_qty != move_line.quantity:
                    igual = False
            if pick.state == 'assigned' and pick.picking_type_code == 'outgoing' and igual:
                pick.id_notify_assigned = True
            else:
                pick.id_notify_assigned = False

    id_notify_assigned = fields.Boolean('Notificado Picking Listo', default=False, compute='_compute_id_notify_assigned')



    def _notificar_picking_assigned(self):
        pickings = self.env['stock.picking'].search([('id_notify_assigned','=',True)])
        
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
        pickings2 = self.env['stock.picking'].search([('id_notify_assigned','=',False),('sale_id.is_picking_assigned','=',True)])
        for pick2 in pickings2:
            pick2.sale_id.is_picking_assigned = False
        return True