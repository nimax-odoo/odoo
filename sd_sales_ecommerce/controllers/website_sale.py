from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request, route
from werkzeug.urls import url_decode, url_encode, url_parse


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

    @route()
    def shop_payment_confirmation(self, **post):
        response = super(WebsiteSaleInherit, self).shop_payment_confirmation(**post)
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            user_id = request.env.user
            if not user_id.sd_reserva_stock:
                order = request.env['sale.order'].sudo().browse(sale_order_id)
                order._validate_order()
                order.reservar_picking_stock()
        return response


    @route(['/shop/change_pricelist/<model("product.pricelist"):pricelist>'], type='http', auth="public", website=True, sitemap=False)
    def pricelist_change(self, pricelist, **post):
        website = request.env['website'].get_current_website()
        redirect_url = request.httprequest.referrer
        if (
                pricelist in request.env.user.sd_pricelist_ids
        ):
            if redirect_url and request.website.is_view_active('website_sale.filter_products_price'):
                decoded_url = url_parse(redirect_url)
                args = url_decode(decoded_url.query)
                min_price = args.get('min_price')
                max_price = args.get('max_price')
                if min_price or max_price:
                    previous_price_list = request.website.pricelist_id
                    try:
                        min_price = float(min_price)
                        args['min_price'] = min_price and str(
                            previous_price_list.currency_id._convert(min_price, pricelist.currency_id, request.website.company_id, fields.Date.today(), round=False)
                        )
                    except (ValueError, TypeError):
                        pass
                    try:
                        max_price = float(max_price)
                        args['max_price'] = max_price and str(
                            previous_price_list.currency_id._convert(max_price, pricelist.currency_id, request.website.company_id, fields.Date.today(), round=False)
                        )
                    except (ValueError, TypeError):
                        pass
                    redirect_url = decoded_url.replace(query=url_encode(args)).to_url()
            request.session['website_sale_current_pl'] = pricelist.id
            request.session['website_sale_selected_pl_id'] = pricelist.id
            order_sudo = request.env['website'].get_current_website()
            if order_sudo:
                order_sudo._cart_update_pricelist(pricelist_id=pricelist.id)
        return request.redirect(redirect_url or '/shop')