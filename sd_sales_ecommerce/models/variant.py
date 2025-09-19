# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.http import request, route

from odoo.addons.website_sale.controllers.variant import WebsiteSaleVariantController


class WebsiteSaleStockWishlistVariantController(WebsiteSaleVariantController):

    @route()
    def get_combination_info_website(self, *args, **kwargs):
        request.update_context(website_compute_price=True)
        return super().get_combination_info_website(*args, **kwargs)
