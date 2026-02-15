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


    # def _compute_price_rule(self, products, quantity, currency=None, date=False, start_date=None, end_date=None,**kwargs):
    #     res = super()._compute_price_rule(products, quantity, currency=currency, date=date, start_date=start_date, end_date=end_date,**kwargs)
    #     for list in res:
    #         price = self.get_price_pricelist_nimax(list, res[list][0], quantity)
    #         res[list] = (price if price else res[list][0], res[list][1])
    #     return res
    

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
                # Usando la API de Odoo 18 para _compute_price_rule
                # En Odoo 18, la firma ha cambiado completamente
                # Ahora espera: products, quantity, currency=None, uom=None, date=False
                # price_result = pricelist._compute_price_rule(
                #     products=product,
                #     quantity=qty,
                #     currency=self.currency_id,
                #     uom=product.uom_id,
                #     date=date.today()
                # )
                price_unit = price
                _logger.info(f"[default_get] Precio calculado: {price_unit}")
            except Exception as e:
                _logger.error(f"[default_get] Error al calcular el precio: {str(e)}")
                # Si hay error, intentamos con precio base del producto
                price_unit = product.list_price
                _logger.info(f"[default_get] Usando precio base: {price_unit}")
            
            if price_unit:
                margin = price_unit - product.sudo().standard_price
                margin_per = (100 * (price_unit - product.standard_price))/price_unit if price_unit else 0
                descuento = 0
                margin2 = 0
                
                if item_pricelist and item_pricelist.as_utilidad > 0:
                    # Verificamos si existe el campo as_last_purchase_price
                    last_purchase_price = 0.0
                    if hasattr(self, 'as_last_purchase_price'):
                        last_purchase_price = product.as_last_purchase_price
                    else:
                        # Si no existe, usamos el standard_price como alternativa
                        _logger.warning(f"[default_get] Campo as_last_purchase_price no existe, usando standard_price")
                        last_purchase_price = product.standard_price
                    
                    if last_purchase_price and (1-item_pricelist.as_utilidad/100) != 0:
                        descuento = (1-(last_purchase_price/(1-item_pricelist.as_utilidad/100)))*100
                        price_unit = product.list_price * (1-descuento/100)
                        margin2 = price_unit * (item_pricelist.as_utilidad / 100)
                    else:
                        _logger.warning(f"[default_get] Precio de compra es 0 o división por cero, saltando cálculo de descuento")
                    
                price_based_usd = (product.list_price - (product.list_price * tf_partner_id.partner_discount/100))*tf_partner_id.cost_deal_import/100*(product.tf_import_tax/100)
                cost_nimax_usd = ((product.list_price - (product.list_price*tf_partner_id.purchase_discount/100))-(product.list_price*tf_partner_id.fulfillment_rebate/100))*(tf_partner_id.cost_deal_import/100)*(product.tf_import_tax/100)
                
                # Convertimos valores
                moneda_mxn = self.env.ref('base.MXN', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','MXN')], limit=1)
                moneda_usd = self.env.ref('base.USD', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','USD')], limit=1)
                
                cost_nimax_usd = self.env.company.currency_id._convert_nimax(cost_nimax_usd, pricelist.currency_id, self.env.company, date.today(), self.id)
              
                # Verificamos si existe el campo as_last_purchase_price
                last_purchase_price = 0.0
                if hasattr(self, 'as_last_purchase_price'):
                    last_purchase_price = product.as_last_purchase_price
                else:
                    # Si no existe, usamos el standard_price como alternativa
                    _logger.warning(f"[default_get] Campo as_last_purchase_price no existe, usando standard_price")
                    last_purchase_price = product.standard_price
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