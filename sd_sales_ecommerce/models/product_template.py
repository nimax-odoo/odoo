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
from odoo.http import request
from odoo.tools import format_amount
import operator as py_operator
OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne
}
#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    stock_status = fields.Selection(
        selection=[('in_stock', 'En Stock'), ('out_of_stock', 'Sin Stock')],
        string="Estado del stock",
        compute="_compute_stock_status"
    )
    free_qty = fields.Float(
        'Stock e-commerce ', compute='_compute_tmpl_quantities',  search='_search_free_tmp_qty', digits='Product Unit of Measure', compute_sudo=False,
        help="Forecast quantity (computed as Quantity On Hand "
             "- reserved quantity)\n"
             "In a context with a single Stock Location, this includes "
             "goods stored in this location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods stored in the Stock Location of this Warehouse, or any "
             "of its children.\n"
             "Otherwise, this includes goods stored in any Stock Location "
             "with 'internal' type.")
    
    def _search_free_tmp_qty(self, operator, value):
        return self._search_product_tmp_quantity(operator, value, 'free_qty')

    def _search_product_tmp_quantity(self, operator, value, field):
        # TDE FIXME: should probably clean the search methods
        # to prevent sql injections
        if field not in ('qty_available', 'virtual_available', 'incoming_qty', 'outgoing_qty', 'free_qty'):
            raise UserError(_('Invalid domain left operand %s', field))
        if operator not in ('<', '>', '=', '!=', '<=', '>='):
            raise UserError(_('Invalid domain operator %s', operator))
        if not isinstance(value, (float, int)):
            raise UserError(_("Invalid domain right operand '%s'. It must be of type Integer/Float", value))

        # TODO: Still optimization possible when searching virtual quantities
        ids = []
        # Order the search on `id` to prevent the default order on the product name which slows
        # down the search because of the join on the translation table to get the translated names.
        for product in self.with_context(prefetch_fields=False).search([], order='id'):
            if OPERATORS[operator](product[field], value):
                ids.append(product.id)
        return [('id', 'in', ids)]
    
    def _compute_tmpl_quantities(self):
        website = request.env['website'].get_current_website() if request else False
        for prodtc_tmp in self.sudo():
            free_qty = 0.0
            for product in prodtc_tmp.sudo().product_variant_ids:
                free_qty += website.sudo()._get_product_available_qty(product)
            prodtc_tmp.sudo().free_qty = free_qty

    def _compute_stock_status(self):
        for product in self:

            if product.free_qty > 0:
                product.sudo().stock_status = 'in_stock'
            else:
                product.sudo().stock_status = 'out_of_stock'

    @api.model
    def _search_get_detail(self, website, order, options):
        res = super()._search_get_detail(website, order, options)
        if options.get('show_only_in_stock'):
            res.get('base_domain').append([('free_qty', '>', 0)])
        return res


    # def _get_additionnal_combination_info(self, product_or_template, quantity, date, website):
    #     res = super()._get_additionnal_combination_info(product_or_template, quantity, date, website)
    #     request.update_context(website_compute_price=True)

    #     # pricelist = website.pricelist_id
    #     # fiscal_position = website.fiscal_position_id.sudo()
    #     # currency = pricelist.currency_id or self.env.company.currency_id
    #     # date = fields.Date.context_today(self)
    #     # website = self.env['website'].get_current_website()
    #     # so = website and request and website.sale_get_order()
    #     # for template in self:
    #     #     unit_price = template.get_price_pricelist_nimax(pricelist,so,1)
    #     #     if unit_price:
    #     #         # curr conversion
    #     #         if currency != pricelist.currency_id:
    #     #             unit_price = pricelist.currency_id._convert(
    #     #                 from_amount=unit_price,
    #     #                 to_currency=currency,
    #     #                 company=self.env.company,
    #     #                 date=date,
    #     #             )
    #     #         # taxes application
    #     #         product_taxes = template.sudo().taxes_id.filtered(lambda t: t.company_id == t.env.company)
    #     #         if product_taxes:
    #     #             taxes = fiscal_position.map_tax(product_taxes)
    #     #             unit_price = self.env['product.template']._apply_taxes_to_price(
    #     #                 unit_price, currency, product_taxes, taxes, template)
                
    #     #         res.update({
    #     #             'list_price': template.list_price,
    #     #             'price': unit_price,
    #     #             'base_unit_price': unit_price,
    #     #             'has_discounted_price': True,
    #     #         })
    #     return {
    #         **res,
    #     }

    # def _get_sales_prices(self, website):
    #     prices = super()._get_sales_prices(website)
    #     pricelist = website.pricelist_id
    #     fiscal_position = website.fiscal_position_id.sudo()
    #     currency = pricelist.currency_id or self.env.company.currency_id
    #     date = fields.Date.context_today(self)
    #     website = self.env['website'].get_current_website()
    #     so = website and request and website.sale_get_order()
    #     for template in self:
    #         unit_price = template.get_price_pricelist_nimax(pricelist,so,1)
    #         if unit_price:
    #             # curr conversion
    #             if currency != pricelist.currency_id:
    #                 unit_price = pricelist.currency_id._convert(
    #                     from_amount=unit_price,
    #                     to_currency=currency,
    #                     company=self.env.company,
    #                     date=date,
    #                 )
    #             # taxes application
    #             product_taxes = template.sudo().taxes_id.filtered(lambda t: t.company_id == t.env.company)
    #             if product_taxes:
    #                 taxes = fiscal_position.map_tax(product_taxes)
    #                 unit_price = self.env['product.template']._apply_taxes_to_price(
    #                     unit_price, currency, product_taxes, taxes, template)

    #             prices[template.id].update({
    #                 'base_price': template.list_price,
    #                 'price_reduce': unit_price,
    #                 'list_price': unit_price,
    #                 'price': unit_price,
    #             })
    #     return prices   
                
            
    def get_price_pricelist_nimax(self, pricelist,order,qty):
        self = self.sudo()
        if pricelist:
            item_pricelist = False
            for item in pricelist.item_ids:
                if item.categ_id and item.categ_id == self.categ_id:
                    item_pricelist = item
                    
            tf_partner_id = self.env['tf.res.partner']
            for x in self.env.user.partner_id.tf_vendor_parameter_ids:
                if x.category_id.id == self.categ_id.id:
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
                price_result = pricelist._compute_price_rule(
                    products=self,
                    quantity=qty,
                    currency=order.currency_id,
                    uom=self.uom_id,
                    date=date.today()
                )
                price_unit = price_result[self.id][0]
                _logger.info(f"[default_get] Precio calculado: {price_unit}")
            except Exception as e:
                _logger.error(f"[default_get] Error al calcular el precio: {str(e)}")
                # Si hay error, intentamos con precio base del producto
                price_unit = self.list_price
                _logger.info(f"[default_get] Usando precio base: {price_unit}")
            
            if price_unit:
                margin = price_unit - self.standard_price
                margin_per = (100 * (price_unit - self.standard_price))/price_unit if price_unit else 0
                descuento = 0
                margin2 = 0
                
                if item_pricelist and item_pricelist.as_utilidad > 0:
                    # Verificamos si existe el campo as_last_purchase_price
                    last_purchase_price = 0.0
                    if hasattr(self, 'as_last_purchase_price'):
                        last_purchase_price = self.as_last_purchase_price
                    else:
                        # Si no existe, usamos el standard_price como alternativa
                        _logger.warning(f"[default_get] Campo as_last_purchase_price no existe, usando standard_price")
                        last_purchase_price = self.standard_price
                    
                    if last_purchase_price and (1-item_pricelist.as_utilidad/100) != 0:
                        descuento = (1-(last_purchase_price/(1-item_pricelist.as_utilidad/100)))*100
                        price_unit = self.list_price * (1-descuento/100)
                        margin2 = price_unit * (item_pricelist.as_utilidad / 100)
                    else:
                        _logger.warning(f"[default_get] Precio de compra es 0 o división por cero, saltando cálculo de descuento")
                    
                price_based_usd = (self.list_price - (self.list_price * tf_partner_id.partner_discount/100))*tf_partner_id.cost_deal_import/100*(self.tf_import_tax/100)
                cost_nimax_usd = ((self.list_price - (self.list_price*tf_partner_id.purchase_discount/100))-(self.list_price*tf_partner_id.fulfillment_rebate/100))*(tf_partner_id.cost_deal_import/100)*(self.tf_import_tax/100)
                
                # Convertimos valores
                moneda_mxn = self.env.ref('base.MXN', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','MXN')], limit=1)
                moneda_usd = self.env.ref('base.USD', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','USD')], limit=1)
                
                cost_nimax_usd = self.env.company.currency_id._convert_nimax(cost_nimax_usd, pricelist.currency_id, self.env.company, date.today(), self.id)
              
                # Verificamos si existe el campo as_last_purchase_price
                last_purchase_price = 0.0
                if hasattr(self, 'as_last_purchase_price'):
                    last_purchase_price = self.as_last_purchase_price
                else:
                    # Si no existe, usamos el standard_price como alternativa
                    _logger.warning(f"[default_get] Campo as_last_purchase_price no existe, usando standard_price")
                    last_purchase_price = self.standard_price
                    
                return (price_based_usd)/(1-pricelist.expected_earning/100) if pricelist.expected_earning else price_based_usd