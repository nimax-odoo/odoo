# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID, api, fields, models, tools
from odoo.http import request
from odoo.osv import expression
from odoo.tools.translate import _, LazyTranslate
from odoo.tools import file_open, ormcache
_lt = LazyTranslate(__name__)

CART_SESSION_CACHE_KEY = 'sale_order_id'
FISCAL_POSITION_SESSION_CACHE_KEY = 'fiscal_position_id'
PRICELIST_SESSION_CACHE_KEY = 'website_sale_current_pl'
PRICELIST_SELECTED_SESSION_CACHE_KEY = 'website_sale_selected_pl_id'
from odoo.exceptions import AccessError, MissingError

class Website(models.Model):
    _inherit = 'website'

    def sale_reset(self):
        request.session.pop(CART_SESSION_CACHE_KEY, None)
        request.session.pop('website_sale_cart_quantity', None)
        # request.session.pop(PRICELIST_SESSION_CACHE_KEY, None)
        request.session.pop(FISCAL_POSITION_SESSION_CACHE_KEY, None)
        # request.session.pop(PRICELIST_SELECTED_SESSION_CACHE_KEY, None)
        
    def _get_and_cache_current_cart(self):
        """ Retrieves and caches the current cart for the session.

        Note: self.ensure_one()

        :return: A sudoed Sales order record.
        :rtype: sale.order
        """
        self.ensure_one()

        SaleOrderSudo = self.env['sale.order'].sudo()

        sale_order_sudo = SaleOrderSudo
        if CART_SESSION_CACHE_KEY in request.session:
            sale_order_sudo = SaleOrderSudo.browse(request.session[CART_SESSION_CACHE_KEY])

            try:
                # fetch the record field or raise a missingError
                # avoids a query with the use of exists()
                sale_order_sudo and sale_order_sudo.state
            except MissingError:
                self.sale_reset()
                sale_order_sudo = SaleOrderSudo

            if sale_order_sudo and (
                sale_order_sudo.state != 'draft'
                or sale_order_sudo.get_portal_last_transaction().state in (
                    'pending', 'authorized', 'done'
                )
                or sale_order_sudo.website_id != self
            ):
                self.sale_reset()
                sale_order_sudo = SaleOrderSudo

            # If customer logs in, the cart must be recomputed based on his information (in the
            # first non readonly request).
            if (
                sale_order_sudo
                and not self.env.user._is_public()
                and self.env.user.partner_id.id != sale_order_sudo.partner_id.id
                and not request.env.cr.readonly
            ):
                sale_order_sudo._update_address(self.env.user.partner_id.id, ['partner_id'])
        elif (
            self.env.user
            and not self.env.user._is_public()
            # If the company of the partner doesn't allow them to buy from this website, updating
            # the cart customer would raise because of multi-company checks.
            # No abandoned cart should be returned in this situation.
            and self.env.user.partner_id.filtered_domain(
                self.env['res.partner']._check_company_domain(self.company_id.id)
            )
        ):  # Search for abandonned cart.
            partner_sudo = self.env.user.partner_id
            abandonned_cart_sudo = SaleOrderSudo.search([
                ('partner_id', '=', partner_sudo.id),
                ('website_id', '=', self.id),
                ('state', '=', 'draft'),
            ], limit=1)
            if abandonned_cart_sudo:
                if not request.env.cr.readonly:
                    # Force the recomputation of the pricelist and fiscal position when resurrecting
                    # an abandonned cart
                    # abandonned_cart_sudo._update_address(partner_sudo.id, ['partner_id'])
                    abandonned_cart_sudo._verify_cart()
                sale_order_sudo = abandonned_cart_sudo

        if (
            (sale_order_sudo or not self.env.user._is_public())
            and sale_order_sudo.id != request.session.get(CART_SESSION_CACHE_KEY)
        ):
            # Store the id of the cart if there is one, or False if the user is logged in, to avoid
            # searching for an abandoned cart again for that user.
            request.session[CART_SESSION_CACHE_KEY] = sale_order_sudo.id
            if 'website_sale_cart_quantity' not in request.session:
                request.session['website_sale_cart_quantity'] = sale_order_sudo.cart_quantity
        return sale_order_sudo
    
    
    def _get_current_pricelist(self):
        return self._get_and_cache_current_pricelist()
    
    def cart_quantity(self):
        if 'website_sale_cart_quantity' not in request.session:
            return request.website.sale_get_order().cart_quantity
        return request.session['website_sale_cart_quantity']

    def sale_get_order(self):
        """ Return the current sale order for the session's user and
        create one if none is found. Only one sale order can be created
        per session.

        :return: the current sale order
        :rtype: recordset of sale.order
        """
        order = self.env['website'].get_current_website()
        return order
    
    def _prepare_sale_order_values(self, partner_sudo):
        res = super()._prepare_sale_order_values(partner_sudo)
        self.ensure_one()
        if self._get_current_pricelist():
            res['pricelist_id'] = self._get_current_pricelist().id
            res['currency_aux_id'] = self._get_current_pricelist().currency_id.id
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
    @ormcache(
        'country_code', 'show_visible', 'current_pl_id', 'website_pricelist_ids', 'partner_pl_id',
    )
    def _get_pl_partner_order(
        self, country_code, show_visible, current_pl_id, website_pricelist_ids, partner_pl_id=False
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
            country_code, show_visible, current_pl_id, website_pricelist_ids, partner_pl_id=False
        )
        if self.env.user.sd_pricelist_ids:
            return self.env.user.sd_pricelist_ids.sudo().ids
        return res
    

class ProductRibbon(models.Model):
    _inherit = 'product.ribbon'

    def _get_position_class(self):
        """
        Return the CSS classes for this ribbon based on style and position.
        rtype: str
        """
        css_classes = ""
        match self.style:
            case 'ribbon':
                css_classes += "o_wsale_ribbon"
            case 'tag':
                css_classes += "o_wsale_badge"

        match self.position:
            case 'left':
                css_classes += " o_left"
            case 'right':
                css_classes += " o_right"
        return css_classes