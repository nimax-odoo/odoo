# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID, api, fields, models, tools
from odoo.http import request
from odoo.osv import expression
from odoo.tools.translate import _, LazyTranslate

_lt = LazyTranslate(__name__)

class ProductTemplate(models.Model):
    _inherit = 'website'

    def _prepare_sale_order_values(self, partner_sudo):
        res = super()._prepare_sale_order_values(partner_sudo)
        self.ensure_one()
        if self.env.user.sd_pricelist:
            res['pricelist_id'] = self.env.user.sd_pricelist.id
            res['currency_aux_id'] = self.env.user.sd_pricelist.currency_id.id
            res['x_studio_orden_de_compra'] = 'N/A'
            res['as_usuario_final'] = 'N/A'
            if self.env.user.partner_id.parent_id:
                res['partner_invoice_id'] = self.env.user.partner_id.parent_id.id
        return res

    
    def _get_product_available_qty(self, product, **kwargs):
        """ Override of `website_sale_stock` to include free quantities of the product in warehouses
         of in-store delivery method and return maximum possible for one order. Needed only if a
         warehouse is set on website, otherwise free quantity is already calculated from all
         warehouses."""
        free_qty = super()._get_product_available_qty(product, **kwargs)
        # Aplicar el porcentaje de stock configurado por el usuario
        user =  request.env.user
        if user.sd_desc_percentaje and user.sd_desc_percentaje != 1.0:
            stock_factor = user.sd_desc_percentaje
            free_qty = round(free_qty * stock_factor)
        return free_qty

    # This method is cached, must not return records! See also #8795
    @tools.ormcache(
        'country_code', 'show_visible',
        'current_pl_id', 'website_pricelist_ids',
        'partner_pl_id', 'order_pl_id',
    )
    def _get_pl_partner_order(
        self, country_code, show_visible, current_pl_id, website_pricelist_ids,
        partner_pl_id=False, order_pl_id=False
    ):
        """ Return the list of pricelists that can be used on website for the current user.

        :param str country_code: code iso or False, If set, we search only price list available for this country
        :param bool show_visible: if True, we don't display pricelist where selectable is False (Eg: Code promo)
        :param int current_pl_id: The current pricelist used on the website
            (If not selectable but currently used anyway, e.g. pricelist with promo code)
        :param tuple website_pricelist_ids: List of ids of pricelists available for this website
        :param int partner_pl_id: the partner pricelist
        :param int order_pl_id: the current cart pricelist
        :returns: list of product.pricelist ids
        :rtype: list
        """
        self.ensure_one()
        res = super()._get_pl_partner_order(
            country_code, show_visible, current_pl_id, website_pricelist_ids,
            partner_pl_id, order_pl_id
        )
        if self.env.user.sd_pricelist_ids:
            return self.env.user.sd_pricelist_ids.sudo().ids
        return res
    
