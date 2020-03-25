# -*- coding: utf-8 -*-

from odoo import models, fields, api


class tfResPartner(models.Model):
    _name = "tf.res.partner"

    name = fields.Char('')
    partner_id = fields.Many2one('res.partner')
    partner_type = fields.Many2one('as.partner.type', 'Partner Type')
    category_id = fields.Many2one('product.category', 'Product Category')
    purchase_discount = fields.Float('Purchase Discount')
    partner_discount = fields.Float('Partner Discount')
    cost_deal_import = fields.Float('% Cost Of Import')
    fulfillment_rebate = fields.Float('Fullfillment Rebate')
