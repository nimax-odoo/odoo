# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from functools import lru_cache
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_round, float_compare, OrderedSet,float_repr
from collections import defaultdict


class InheritProductCategory(models.Model):
    _inherit = 'product.category'
    
    sd_update_price_mx = fields.Boolean('Actualizar Precios MXN-USD')
    
    def _cron_update_product_mx(self):
        categories = self.env['product.category'].sudo().search([('sd_update_price_mx','=',True)])
        for category in categories:
            products = self.env['product.product'].sudo().search([('categ_id','=',category.id)])
            for product in products:
                moneda_MXN = self.env['res.currency'].sudo().search([('name','=','MXN')])
                moneda_USD = self.env['res.currency'].sudo().search([('name','=','USD')])
                if not moneda_MXN:
                    raise UserError(_("No se encontro la moneda MXN"))
                if not moneda_USD:
                    raise UserError(_("No se encontro la moneda USD"))
                if product.list_price_mx > 0.0:
                    precio_mxn = moneda_MXN._convert(
                                product.list_price_mx,
                                moneda_USD,
                                self.env.company,
                                fields.Datetime.now(),
                                round=False
                            )
                    product.lst_price = precio_mxn