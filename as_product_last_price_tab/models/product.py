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
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class AsProductLastPrice(models.AbstractModel):
    """Mixin para compartir funcionalidad de últimos precios"""
    _name = 'as.product.last.price.mixin'
    _description = 'Last Price Mixin'

    as_last_purchase_price = fields.Float(
        string='Last Purchase Price', compute='_compute_last_purchase', store=True)
    as_last_purchase_date = fields.Datetime(
        string='Last Purchase Date', compute='_compute_last_purchase', store=True)
    as_last_supplier_id = fields.Many2one(
        comodel_name='res.partner', string='Last Supplier',
        compute='_compute_last_purchase', store=True)
        
    as_last_sale_price = fields.Float(
        string='Last Sale Price', compute='_compute_last_sale', store=True)
    as_last_sale_date = fields.Datetime(
        string='Last Sale Date', compute='_compute_last_sale', store=True)
    as_last_customer_id = fields.Many2one(
        comodel_name='res.partner', string='Last Customer',
        compute='_compute_last_sale', store=True)

    def _get_purchase_line_domain(self):
        """Método para obtener el dominio específico para líneas de compra"""
        self.ensure_one()
        if self._name == 'product.template':
            return [('product_id.product_tmpl_id', '=', self.id)]
        return [('product_id', '=', self.id)]

    def _get_sale_line_domain(self):
        """Método para obtener el dominio específico para líneas de venta"""
        self.ensure_one()
        if self._name == 'product.template':
            return [('product_id.product_tmpl_id', '=', self.id)]
        return [('product_id', '=', self.id)]

    @api.depends('product_variant_ids.as_last_purchase_price', 
                'product_variant_ids.as_last_purchase_date', 
                'product_variant_ids.as_last_supplier_id')
    def _compute_last_purchase(self):
        """Calcula último precio de compra, fecha y proveedor"""
        for product in self:
            try:
                domain = product._get_purchase_line_domain() + [
                    ('state', 'in', ['purchase', 'done']),
                    ('order_id.state', 'in', ['purchase', 'done'])
                ]
                line = self.env['purchase.order.line'].search(
                    domain, order='date_planned desc', limit=1)
                
                product.as_last_purchase_date = line.date_planned if line else False
                product.as_last_purchase_price = line.price_unit if line else 0.0
                product.as_last_supplier_id = line.order_id.partner_id.id if line and line.order_id.partner_id else False
            except Exception as e:
                _logger.error("Error al calcular último precio de compra: %s", str(e))
                product.as_last_purchase_date = False
                product.as_last_purchase_price = 0.0
                product.as_last_supplier_id = False

    @api.depends('product_variant_ids.as_last_sale_price', 
                'product_variant_ids.as_last_sale_date', 
                'product_variant_ids.as_last_customer_id')
    def _compute_last_sale(self):
        """Calcula último precio de venta, fecha y cliente"""
        for product in self:
            try:
                domain = product._get_sale_line_domain() + [
                    ('state', 'in', ['sale', 'done']),
                    ('order_id.state', 'in', ['sale', 'done'])
                ]
                line = self.env['sale.order.line'].search(
                    domain, order='create_date desc', limit=1)
                
                product.as_last_sale_date = line.order_id.date_order if line and line.order_id else False
                product.as_last_sale_price = line.price_unit if line else 0.0
                product.as_last_customer_id = line.order_id.partner_id.id if line and line.order_id.partner_id else False
            except Exception as e:
                _logger.error("Error al calcular último precio de venta: %s", str(e))
                product.as_last_sale_date = False
                product.as_last_sale_price = 0.0
                product.as_last_customer_id = False

class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = ['product.product', 'as.product.last.price.mixin']

class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'as.product.last.price.mixin']
