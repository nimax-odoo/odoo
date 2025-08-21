# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, time
from odoo.tools.safe_eval import safe_eval
from datetime import date, datetime, time
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, is_html_empty
from odoo.tools.translate import html_translate

#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
class CouponProgram(models.Model):
    _inherit = 'coupon.program'
    
    sd_apply_toprunner_ecommerce = fields.Boolean('Aplicar automaticamente al E-commerce')

    def search_promo_ecommerce(self,product,partner):
        domain_promo = [('sd_apply_toprunner_ecommerce','=',True),('active','=',True)]
        promociones = self.env['coupon.program'].sudo().search(domain_promo)
        precio_usd = 0.0
        cumple = False
        promo = self.env['coupon.program']
        for promo in promociones:
            domain = safe_eval(promo.rule_products_domain)
            productos = self.env[product._name].sudo().search(domain)
            if product in productos:
                cumple = True
            domain_partner = safe_eval(promo.rule_partners_domain)
            clientes = self.env['res.partner'].sudo().search(domain_partner)
            if partner in clientes.ids:        
                cumple = True
            if cumple:
                precio_usd = promo.PRICE_UNIT_USD
                
        return cumple,precio_usd,promo   

class ProductTemplate(models.Model):
    _inherit = "product.template"     
      
    def _get_additionnal_combination_info(self, product_or_template, quantity, date, website):
        pricelist = website.pricelist_id
        currency = website.currency_id

        # Pricelist price doesn't have to be converted
        pricelist_price, pricelist_rule_id = pricelist._get_product_price_rule(
            product=product_or_template,
            quantity=quantity,
            target_currency=currency,
        )
        precio = 0.0
        promo = self.env['coupon.program'].sudo()
        partner_id = self.env.user.partner_id
        promociones = self.env['coupon.program'].sudo().search_promo_ecommerce(product_or_template,partner_id)
        if promociones[0]:
            precio = promociones[1]
            promo = promociones[2]
            pricelist_price = precio
            
        price_before_discount = pricelist_price
        pricelist_item = self.env['product.pricelist.item'].browse(pricelist_rule_id)
        if pricelist_item._show_discount_on_shop():
            price_before_discount = pricelist_item._compute_price_before_discount(
                product=product_or_template,
                quantity=quantity or 1.0,
                date=date,
                uom=product_or_template.uom_id,
                currency=currency,
            )

        has_discounted_price = price_before_discount > pricelist_price
        combination_info = {
            'list_price': max(pricelist_price, price_before_discount),
            'price': pricelist_price,
            'has_discounted_price': has_discounted_price,
        }

        comparison_price = None
        if (
            not has_discounted_price
            and product_or_template.compare_list_price
            and self.env.user.has_group('website_sale.group_product_price_comparison')
        ):
            comparison_price = product_or_template.currency_id._convert(
                from_amount=product_or_template.compare_list_price,
                to_currency=currency,
                company=self.env.company,
                date=date,
                round=False)
        combination_info['compare_list_price'] = comparison_price

        combination_info['price_extra'] = product_or_template.currency_id._convert(
            from_amount=product_or_template._get_attributes_extra_price(),
            to_currency=currency,
            company=self.env.company,
            date=date,
            round=False,
        )

        # Apply taxes
        fiscal_position = website.fiscal_position_id.sudo()

        product_taxes = product_or_template.sudo().taxes_id._filter_taxes_by_company(self.env.company)
        taxes = self.env['account.tax']
        if product_taxes:
            taxes = fiscal_position.map_tax(product_taxes)
            # We do not apply taxes on the compare_list_price value because it's meant to be
            # a strict value displayed as is.
            for price_key in ('price', 'list_price', 'price_extra'):
                combination_info[price_key] = self._apply_taxes_to_price(
                    combination_info[price_key],
                    currency,
                    product_taxes,
                    taxes,
                    product_or_template,
                    website=website,
                )

        combination_info.update({
            'prevent_zero_price_sale': website.prevent_zero_price_sale and float_is_zero(
                combination_info['price'],
                precision_rounding=currency.rounding,
            ),

            'base_unit_name': product_or_template.base_unit_name,
            'base_unit_price': product_or_template._get_base_unit_price(combination_info['price']),

            # additional info to simplify overrides
            'currency': currency,  # displayed currency
            'date': date,
            'product_taxes': product_taxes,  # taxes before fpos mapping
            'taxes': taxes,  # taxes after fpos mapping
        })

        if combination_info['prevent_zero_price_sale']:
            combination_info['compare_list_price'] = 0

        return combination_info

                
                
            
            