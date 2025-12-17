# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import date, time
from odoo.tools.safe_eval import safe_eval
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError

#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class sdSaleOrderWiz(models.Model):
    _name = 'sd.free.owner.wiz'
    _description = 'liberar propietarios de stock de productos'

    quant_id = fields.Many2one("stock.quant", string='Movimiento de Stock')
    owner_id = fields.Many2one("res.partner", string='Propietario de Stock')

    @api.model
    def default_get(self, fields):
        res = super(sdSaleOrderWiz, self).default_get(fields)
        res_ids = self._context.get('active_id')
        if res_ids:
            so_line_obj = self.env['stock.quant'].browse(res_ids)
            res.update({
                'quant_id': so_line_obj.id,
                'owner_id': so_line_obj.owner_id.id,
            })
        return res
    
    def as_aprobe_sale(self):
        for wiz in self:
            wiz.quant_id.owner_id = wiz.owner_id
        return {'type': 'ir.actions.act_window_close'}





