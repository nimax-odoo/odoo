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
#   Code in this file comes from "Product Last Price Info - Sale"
#   The module can be found on:
#   https://apps.odoo.com/apps/modules/8.0/sale_last_price_info/
#    Contributors:
#    Alfredo de la Fuente <alfredodelafuente@avanzosc.es>
#    Oihane Crucelaegui <oihanecrucelaegi@avanzosc.es>
#    Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#    Ana Juaristi <anajuaristi@avanzosc.es>
##############################################################################

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_last_sale(self):
        """ Get last sale price, last sale date and last customer """
        lines = self.env['sale.order.line'].search(
            [('product_id', '=', self.id),
             ('state', 'in', ['sale', 'done'])]).sorted(
            key=lambda l: l.order_id.date_order, reverse=True)
        self.last_sale_date = lines[:1].order_id.date_order
        self.last_sale_price = lines[:1].price_unit
        self.last_customer_id = lines[:1].order_id.partner_id

    last_sale_price = fields.Float(
        string='Last Sale Price', compute='_get_last_sale')
    last_sale_date = fields.Datetime(
        string='Last Sale Date', compute='_get_last_sale')
    last_customer_id = fields.Many2one(
        comodel_name='res.partner', string='Last Customer',
        compute='_get_last_sale')

class as_ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_last_sale(self):
        """ Get last sale price, last sale date and last customer """
        lines = self.env['sale.order.line'].search(
            [('product_id', '=', self.id),
             ('state', 'in', ['sale', 'done'])]).sorted(
            key=lambda l: l.order_id.date_order, reverse=True)
        self.as_last_sale_date = lines[:1].order_id.date_order
        self.as_last_sale_price = lines[:1].price_unit
        self.as_last_customer_id = lines[:1].order_id.partner_id

    as_last_sale_price = fields.Float(
        string='Last Sale Price', compute='_get_last_sale')
    as_last_sale_date = fields.Datetime(
        string='Last Sale Date', compute='_get_last_sale')
    as_last_customer_id = fields.Many2one(
        comodel_name='res.partner', string='Last Customer',
        compute='_get_last_sale')
