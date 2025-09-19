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

#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _cart_update(self, product_id, line_id=None, add_qty=0, set_qty=0, **kwargs):
        res = super()._cart_update(
            product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty, **kwargs
        )
        line = self.env['sale.order.line'].sudo().browse(res['line_id'])
        website = self.env['website'].get_current_website()
        so = website and request and website.sale_get_order()
        so.pricelist_id = self.env.user.sd_pricelist or so.pricelist_id
        so.currency_aux_id = self.env.user.sd_pricelist.currency_id or so.pricelist_id.currency_id
        if line and line.product_id:
            pricelist = line.order_id.pricelist_id
            line.as_pricelist_id = pricelist

        return res
    
    def _cron_update_sales_ecoomerce(self):
        orders = self.env['sale.order'].sudo().search([('state','=','draft'),('website_id','!=',False)])
        for order in orders:
            order.action_cancel()
            order.message_post(body=_('La venta fue cancelada automaticamente por el sistema, ya que no fue confirmada en el tiempo limite.'))
            #notificar al cliente que el pedido fue cancelado automáticamente
            template = self.env.ref('sd_sales_ecommerce.email_template_update_Sale_order', raise_if_not_found=False)
            if template:
                template.sudo().send_mail(order.id, force_send=True)
            _logger.info('CANCELO LA VENTA %s POR CRON',order.name)
            
        return True
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_pricelist_price(self):
        """Compute the price given by the pricelist for the given line information.

        :return: the product sales price in the order currency (without taxes)
        :rtype: float
        """
        self.ensure_one()
        self.product_id.ensure_one()

        price = super()._get_pricelist_price()
        # price = self.pricelist_item_id.pricelist_id.get_price_pricelist_nimax(self.product_id.with_context(**self._get_product_price_context()).id, price, self.product_uom_qty or 1.0)

        return price

    def _prepare_order_line_update_values(
        self, order_line, quantity, linked_line_id=False, **kwargs
    ):
        values = super()._prepare_order_line_update_values(order_line, quantity, linked_line_id=False, **kwargs)

        values['as_pricelist_id'] = self.order_id.pricelist_id.id

        return values