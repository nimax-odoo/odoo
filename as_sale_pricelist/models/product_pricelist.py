# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    expected_earning = fields.Float('Expected Earnings')