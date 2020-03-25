# -*- coding: utf-8 -*-

from odoo import models, fields, api

class tfResPartner(models.Model):
    _name = "tf.history.promo"

    promotion_id = fields.Many2one('sale.coupon.program')

    vendor_id = fields.Many2one('res.partner', 'Vendor')
    product_id = fields.Many2one('product.product', 'Product')
    customer_id = fields.Many2one('res.partner', 'Customer')
    customer_type = fields.Many2one('as_partner_type', 'Type Customer')
    category_id = fields.Many2one('product.category', 'Product Category')
    qty = fields.Float('Qty')
    recalculated_price_unit = fields.Float('Recalculated Price Unit')
    recalculated_price_unit_mxp = fields.Float('Recalculated Price Unit MXP')
    recalculated_cost_nimax_usd = fields.Float('Recalculated Cost Nimax USD')
    recalculated_cost_nimax_mxp = fields.Float('Recalculated Cost Nimax MXP')
    margin_mxp = fields.Float('Margin MXP')
    margin_usd = fields.Float('Margin USD')
    total_usd = fields.Float('Total USD')
    total_mxp = fields.Float('Total MXP')
    last_applied_promo = fields.Boolean('Last Applied Promo')
    salesman_id = fields.Many2one('res.users', 'Salesman')


