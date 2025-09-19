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


    def _get_current_pricelist(self):
        """
        :returns: The current pricelist record
        """
        self = self.with_company(self.company_id)
        ProductPricelist = self.env['product.pricelist']

        pricelist = ProductPricelist
        if request and request.session.get('website_sale_current_pl'):
            # `website_sale_current_pl` is set only if the user specifically chose it:
            #  - Either, he chose it from the pricelist selection
            #  - Either, he entered a coupon code
            pricelist = ProductPricelist.browse(request.session['website_sale_current_pl']).exists().sudo()
            country_code = self._get_geoip_country_code()
            if not pricelist or not pricelist._is_available_on_website(self) or not pricelist._is_available_in_country(country_code):
                request.session.pop('website_sale_current_pl')
                pricelist = ProductPricelist
        user_id = self.env.user
        if user_id.sd_pricelist:
            pricelist = user_id.sd_pricelist
        if not pricelist:
            partner_sudo = self.env.user.partner_id

            # If the user has a saved cart, it take the pricelist of this last unconfirmed cart
            pricelist = partner_sudo.last_website_so_id.pricelist_id
            if not pricelist:
                # The pricelist of the user set on its partner form.
                # If the user is not signed in, it's the public user pricelist
                pricelist = partner_sudo.property_product_pricelist

            # The list of available pricelists for this user.
            # If the user is signed in, and has a pricelist set different than the public user pricelist
            # then this pricelist will always be considered as available
            available_pricelists = self.get_pricelist_available()
            if available_pricelists and pricelist not in available_pricelists:
                # If there is at least one pricelist in the available pricelists
                # and the chosen pricelist is not within them
                # it then choose the first available pricelist.
                # This can only happen when the pricelist is the public user pricelist and this pricelist is not in the available pricelist for this localization
                # If the user is signed in, and has a special pricelist (different than the public user pricelist),
                # then this special pricelist is amongs these available pricelists, and therefore it won't fall in this case.
                pricelist = available_pricelists[0]

        return pricelist