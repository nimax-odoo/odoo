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
    _name = 'sd.sale.order.wiz'
    _description = 'cambiar cantidades de orden de venta'

    sale_id = fields.Many2one("sale.order", string='Ventas')
    sale_product_ids = fields.One2many("sd.sale.order.line.wiz",'wiz_id', string='Lineas')

    @api.model
    def default_get(self, fields):
        res = super(sdSaleOrderWiz, self).default_get(fields)
        res_ids = self._context.get('active_id')
        if res_ids:
            so_line_obj = self.env['sale.order'].browse(res_ids)
            lines = []
            for line in so_line_obj.order_line:
                lines.append((0,0,{
                    'product_id': line.product_id.id,
                    'qty': line.product_uom_qty,
                    'qty_order': line.product_uom_qty,
                    'line_sale_id': line.id,
                }))
            
            res.update({
                'sale_id': so_line_obj.id,
                'sale_product_ids': lines,
            })
        return res
    
    def as_aprobe_sale(self):
        for wiz in self:
            wiz.sudo().sale_id.action_unlock()
            for line in wiz.sale_product_ids:
                line.line_sale_id.product_uom_qty = line.qty
            wiz.sudo().sale_id.action_lock()
        return {'type': 'ir.actions.act_window_close'}



class sdSaleOrderLineWiz(models.TransientModel):
    _name = 'sd.sale.order.line.wiz'
    _description = 'cambiar cantidades de orden de venta lineas'

    wiz_id = fields.Many2one("sd.sale.order.wiz", string='Wizard')
    product_id = fields.Many2one("product.product", string='Producto')
    line_sale_id = fields.Many2one("sale.order.line", string='Linea de Venta')
    qty = fields.Float(string='Cantidad')
    qty_order = fields.Float(string='Cantidad ordenada')

    @api.onchange('qty')
    def onchange_qty(self):
        if self.qty > self.qty_order:
            raise ValidationError('La cantidad no puede ser mayor a la cantidad ordenada')
    
    


