# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
#   Code in this file comes from Product Last Price Info - Purchase module
#   which is available on:
#   https://apps.odoo.com/apps/modules/8.0/purchase_last_price_info/
#
#   Module contributors:
#   Alfredo de la Fuente <alfredodelafuente@avanzosc.es>
#   Oihane Crucelaegui <oihanecrucelaegi@avanzosc.es>
#   Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#   Ana Juaristi <anajuaristi@avanzosc.es>
##############################################################################
from odoo import api, fields, models


class ProductProductAmore(models.Model):
    _inherit = 'product.product'

    def _get_last_purchase(self):
        """ Get last purchase price, last purchase date and last supplier """
        lines = self.env['purchase.order.line'].search(
            [('product_id', '=', self.id),
             ('state', 'in', ['purchase', 'done'])]).sorted(
            key=lambda l: l.order_id.date_order, reverse=True)
        self.last_purchase_date = lines[:1].order_id.date_order
        self.last_purchase_price = lines[:1].price_unit
        self.last_supplier_id = lines[:1].order_id.partner_id

    last_purchase_price = fields.Float(
        string='Last Purchase Price', compute='_get_last_purchase')
    last_purchase_date = fields.Datetime(
        string='Last Purchase Date', compute='_get_last_purchase')
    last_supplier_id = fields.Many2one(
        comodel_name='res.partner', string='Last Supplier',
        compute='_get_last_purchase')

class as_ProductTemplatePurchaseOrder(models.Model):
    _inherit = 'product.template'

    def _get_last_purchase(self):
        """ Get last purchase price, last purchase date and last supplier """
        lines = self.env['purchase.order.line'].search(
            [('product_id', '=', self.id),
             ('state', 'in', ['purchase', 'done'])]).sorted(
            key=lambda l: l.order_id.date_order, reverse=True)
        self.as_last_purchase_date = lines[:1].order_id.date_order
        self.as_last_purchase_price = lines[:1].price_unit
        self.as_last_supplier_id = lines[:1].order_id.partner_id

    as_last_purchase_price = fields.Float(
        string='Last Purchase Price', compute='_get_last_purchase')
    as_last_purchase_date = fields.Datetime(
        string='Last Purchase Date', compute='_get_last_purchase')
    as_last_supplier_id = fields.Many2one(
        comodel_name='res.partner', string='Last Supplier',
        compute='_get_last_purchase')
