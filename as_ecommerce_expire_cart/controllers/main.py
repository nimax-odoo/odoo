from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleCartExpire(WebsiteSale):
    @http.route(
        ["/shop/cart/get_expire_date"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False,
    )
    def get_expire_date(self, **kw):
        order = request.website.sale_get_order()
        return order.cart_expire_date
