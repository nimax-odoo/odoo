# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

class tf_history_promo(models.Model):
    _name = 'tf.history.promo'
    _description = 'Historial de Promociones'
    
    vendor_id = fields.Many2one('res.partner', string='Proveedor')
    product_id = fields.Many2one('product.product', string='Producto')
    customer_id = fields.Many2one('res.partner', string='Cliente')
    customer_type = fields.Many2one('as.partner.type', string='Tipo de Cliente')
    as_pricelist_id = fields.Many2one('product.pricelist', string='Lista de Precios')
    category_id = fields.Many2one('product.category', string='Categoría')
    qty = fields.Float('Cantidad')
    recalculated_price_unit = fields.Float('Precio Unitario USD')
    recalculated_price_unit_mxp = fields.Float('Precio Unitario MXP')
    recalculated_cost_nimax_usd = fields.Float('Costo NIMAX USD')
    recalculated_cost_nimax_mxp = fields.Float('Costo NIMAX MXP')
    margin_mxp = fields.Float('Margen MXP')
    margin_usd = fields.Float('Margen USD')
    total_usd = fields.Float('Total USD')
    total_mxp = fields.Float('Total MXP')
    sale_order_line = fields.Many2one('sale.order.line', string='Línea de Pedido')
    salesman_id = fields.Many2one('res.users', string='Vendedor')
    sale_id = fields.Many2one('sale.order', string='Pedido')
    promo_id = fields.Many2one('coupon.program', string='Promoción')
    last_applied_promo = fields.Boolean('Última Promoción Aplicada', default=False) 
    move_credit_id = fields.Many2one('account.move', string='Nota de Crédito')