# -*- coding: utf-8 -*-

from odoo import fields, models, api

class TfResPartner(models.Model):
    _name = 'tf.res.partner'
    _description = 'Partner Program'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, tracking=True)
    partner_type = fields.Many2one('as.partner.type', string='Partner Type', required=True, tracking=True)
    category_id = fields.Many2one('product.category', string='Product Category', tracking=True)
    partner_discount = fields.Float(string='Partner Discount (%)', tracking=True)
    purchase_discount = fields.Float(string='Purchase Discount (%)', tracking=True)
    fulfillment_rebate = fields.Float(string='Fulfillment Rebate (%)', tracking=True)
    cost_deal_import = fields.Float(string='Cost Deal Import (%)', tracking=True)

    @api.depends('partner_id', 'partner_type')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.partner_id.name or ''} - {record.partner_type.name or ''}" 