from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request, route


class WebsiteSaleInherit(WebsiteSale):

    def _shop_get_query_url_kwargs(
            self, category, search, min_price, max_price, order=None, tags=None,
            attribute_value=None, **post
    ):
        res = super(WebsiteSaleInherit, self)._shop_get_query_url_kwargs(category=category, search=search, min_price=min_price, max_price=max_price, order=order, tags=tags,
            attribute_value=attribute_value, **post)
        if post.get('show_only_in_stock'):
            res.update({'show_only_in_stock': post.get('show_only_in_stock')})
        return res

    def _get_search_options(
        self, category=None, attrib_values=None, tags=None, min_price=0.0, max_price=0.0,
        conversion_rate=1, **post
    ):
        res = super()._get_search_options(category, attrib_values, tags, min_price, max_price,
        conversion_rate, **post)
        if post.get('show_only_in_stock'):
            res.update({'show_only_in_stock': post.get('show_only_in_stock')})
        return res

    @http.route()
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        response = super(WebsiteSaleInherit, self).shop(page=page, category=category,
                                                        search=search, min_price=min_price, max_price=max_price,
                                                        ppg=ppg,**post)
        q = response.qcontext
        if post.get('show_only_in_stock'):
            response.qcontext.update({
                'show_only_in_stock': True
            })
        stock_map = {}
        products = q.get('products') or request.env['product.template']
        for tmpl in products:
                stock_map[tmpl.id] = tmpl.free_qty

        q['stock_map'] = stock_map
        return response
