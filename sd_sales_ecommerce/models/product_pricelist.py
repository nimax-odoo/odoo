# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, time
from odoo.tools.safe_eval import safe_eval
from datetime import date, datetime, time
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.tools import format_amount
import operator as py_operator
import time
#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
class Pricelist(models.Model):
    _inherit = "product.pricelist"
    

    def get_price_pricelist_nimax(self, product, price, qty = 1):
        pricelist = self
        product = self.env['product.product'].browse(product)
        if pricelist:
            item_pricelist = False
            for item in pricelist.item_ids.filtered(lambda a: a.categ_id and a.categ_id == self.categ_id):
                if item.categ_id and item.categ_id == self.categ_id:
                    item_pricelist = item
                    
            tf_partner_id = self.env['tf.res.partner']
            for x in self.env.user.partner_id.tf_vendor_parameter_ids.filtered(lambda a: a.category_id == product.categ_id):
                if x.category_id.id == product.categ_id.id:
                    tf_partner_id = x
                    
            if not tf_partner_id:
                return False

            if [x for x in pricelist.item_ids if x.applied_on == '2_product_category'] and \
                    not [x for x in pricelist.item_ids if x.applied_on == '2_product_category' and self.categ_id.id == x.categ_id.id]:
                return False

            # Adaptación a Odoo 18: _compute_price_rule tiene una nueva API
            try:
                price_unit = price
                _logger.info(f"[default_get]1 Precio calculado: {price_unit}")
            except Exception as e:
                _logger.error(f"[default_get] Error al calcular el precio: {str(e)}")
                # Si hay error, intentamos con precio base del producto
                price_unit = product.list_price
                _logger.info(f"[default_get] Usando precio base: {price_unit}")
            
            if price_unit:
                   
                price_based_usd = (product.list_price - (product.list_price * tf_partner_id.partner_discount/100))*tf_partner_id.cost_deal_import/100*(product.tf_import_tax/100)
                moneda_usd = self.env.ref('base.USD', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','USD')], limit=1)
             
                if moneda_usd != pricelist.currency_id:
                    price_based_usd = moneda_usd._convert(
                        from_amount=price_based_usd,
                        to_currency=pricelist.currency_id,
                        company=self.env.company
                    )
                    
                    
                return (price_based_usd)/(1-pricelist.expected_earning/100) if pricelist.expected_earning else price_based_usd
            
class PricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    def selected_product(self,product):
        if product._name == 'product.product':
            return product
        else:
            return self.env['product.product'].search([('product_tmpl_id','=',product.id)],limit=1)

    def _compute_price(self, product, quantity, uom, date, currency=None, **kwargs):
        price = super()._compute_price(product, quantity, uom, date, currency, **kwargs)
        if 'website_id' in self.env.context and self.env.user.sd_pricelist_ids:
            product = self.selected_product(product)
            pricelist = self.pricelist_id
            price_new = pricelist.get_price_pricelist_nimax(product.id, price, quantity)
            # time.sleep(10)
            if price_new:
                price = price_new
        if 'website_id' in self.env.context:
            product = self.selected_product(product)
            pricelist = self.pricelist_id
            promos_disponibles = request.env['coupon.program'].sudo().search_promo_disponibles_ecommerce()
            partner_id = self.env.user.partner_id.id
            if promos_disponibles and partner_id:
                promociones = request.env['coupon.program'].sudo().search_promo_ecommerce(product,partner_id,promos_disponibles)
                if promociones[0]:
                    price = promociones[1]
                    moneda_usd = self.env.ref('base.USD', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','USD')], limit=1)
                    if moneda_usd != pricelist.currency_id:
                        price = moneda_usd._convert(
                            from_amount=promociones[1],
                            to_currency=pricelist.currency_id,
                            company=self.env.company
                        )
        return price