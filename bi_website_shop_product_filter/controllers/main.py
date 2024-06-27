# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
from werkzeug.exceptions import Forbidden, NotFound
from operator import itemgetter

from odoo import fields, http, tools, _
from odoo.http import request
from odoo.addons.base.models.ir_qweb_fields import nl2br
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.payment.controllers.portal import PaymentPostProcessing
from odoo.addons.website.controllers.main import QueryURL
from odoo.tools import groupby as groupbyelem
from odoo.exceptions import ValidationError
from odoo.addons.website.controllers.main import Website
from odoo.addons.sale_product_configurator.controllers.main import ProductConfiguratorController
from odoo.addons.website_sale.controllers.main import TableCompute
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.osv import expression

_logger = logging.getLogger(__name__)


PPG = 20  # Products Per Page
PPR = 4   # Products Per Row


class WebsiteSale(WebsiteSale):

    def _get_compute_currency(self, pricelist, product=None):
        company = product and product._get_current_company(pricelist=pricelist, website=request.website) or pricelist.company_id or request.website.company_id
        from_currency = (product or request.env['res.company']._get_main_company()).currency_id
        to_currency = pricelist.currency_id
        return lambda price: from_currency._convert(price, to_currency, company, fields.Date.today())

    def _get_search_order(self, post):
        # OrderBy will be parsed in orm and so no direct sql injection
        # id is added to be sure that order is a unique sort key
        order = post.get('order') or 'website_sequence ASC'
        return 'is_published desc, %s, id desc' % order

    def _get_search_domain(self, search, category, attrib_values, filter_values):
        domain = request.website.sale_product_domain()
        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', '|','|',

                    ('name', 'ilike', srch), 
                    ('description', 'ilike', srch),
                    ('description_sale', 'ilike', srch), 
                    ('product_variant_ids.default_code', 'ilike', srch)
                    ('x_studio_sku_no_de_parte', 'ilike', srch)

                    ]

        if category:
            domain += [('public_categ_ids', 'child_of', int(category))]

        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]


        if filter_values:
            filter = None
            ids = []
            for value in filter_values:
                if not filter:
                    filter = value[0]
                    ids.append(value[1])
                elif value[0] == filter:
                    ids.append(value[1])
                else:
                    domain += [('filter_ids.filter_value_ids', 'in', ids)]
                    filter = value[0]
                    ids = [value[1]]
            if filter:
                domain += [('filter_ids.filter_value_ids', 'in', ids)]

        return domain


    def sitemap_shop(env, rule, qs):
        if not qs or qs.lower() in '/shop':
            yield {'loc': '/shop'}

        Category = env['product.public.category']
        dom = sitemap_qs2dom(qs, '/shop/category', Category._rec_name)
        dom += env['website'].get_current_website().website_domain()
        for cat in Category.search(dom):
            loc = '/shop/category/%s' % slug(cat)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

    def _get_search_options(
        self, category=None, attrib_values=None, pricelist=None, min_price=0.0, max_price=0.0, conversion_rate=1, **post
    ):
        return {
            'displayDescription': True,
            'displayDetail': True,
            'displayExtraDetail': True,
            'displayExtraLink': True,
            'displayImage': True,
            'allowFuzzy': not post.get('noFuzzy'),
            'category': str(category.id) if category else None,
            'min_price': min_price / conversion_rate,
            'max_price': max_price / conversion_rate,
            'attrib_values': attrib_values,
            'display_currency': pricelist.currency_id,
        }


    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True, sitemap=sitemap_shop)
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        add_qty = int(post.get('add_qty', 1))
        try:
            min_price = float(min_price)
        except ValueError:
            min_price = 0
        try:
            max_price = float(max_price)
        except ValueError:
            max_price = 0

        Category = request.env['product.public.category']
        if category:
            category = Category.search([('id', '=', int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = Category

        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = False
            post['ppg'] = ppg
        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg or 20

        ppr = request.env['website'].get_current_website().shop_ppr or 4

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}


        filter_list = request.httprequest.args.getlist('filter')
        
        filter_values = [[int(x) for x in v.split("-")] for v in filter_list if v]
        filter_ids = {v[0] for v in filter_values}
        filter_set = {v[1] for v in filter_values}

        keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list, filter=filter_list, min_price=min_price, max_price=max_price, order=post.get('order'))

        pricelist_context, pricelist = self._get_pricelist_context()

        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        filter_by_price_enabled = request.website.is_view_active('website_sale.filter_products_price')
        if filter_by_price_enabled:
            company_currency = request.website.company_id.currency_id
            conversion_rate = request.env['res.currency']._get_conversion_rate(company_currency, pricelist.currency_id, request.website.company_id, fields.Date.today())
        else:
            conversion_rate = 1

        url = "/shop"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list
        if filter_list:
            post['filter'] = filter_list

        options = self._get_search_options(
            category=category,
            attrib_values=attrib_values,
            pricelist=pricelist,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            **post
        )
        # No limit because attributes are obtained from complete product list
        product_count, details, fuzzy_search_term = request.website._search_with_fuzzy("products_only", search,
            limit=None, order=self._get_search_order(post), options=options)
        search_product = details[0].get('results', request.env['product.template']).with_context(bin_size=True)

        filter_by_price_enabled = request.website.is_view_active('website_sale.filter_products_price')
        if filter_by_price_enabled:
            # TODO Find an alternative way to obtain the domain through the search metadata.
            Product = request.env['product.template'].with_context(bin_size=True)
            domain = self._get_search_domain(search, category, attrib_values, filter_values)

            # This is ~4 times more efficient than a search for the cheapest and most expensive products
            from_clause, where_clause, where_params = Product._where_calc(domain).get_sql()
           
            query = f"""
                SELECT COALESCE(MIN(list_price), 0) * {conversion_rate}, COALESCE(MAX(list_price), 0) * {conversion_rate}
                  FROM {from_clause}
                 WHERE {where_clause}
            """
            request.env.cr.execute(query, where_params)
            available_min_price, available_max_price = request.env.cr.fetchone()

            if min_price or max_price:
                # The if/else condition in the min_price / max_price value assignment
                # tackles the case where we switch to a list of products with different
                # available min / max prices than the ones set in the previous page.
                # In order to have logical results and not yield empty product lists, the
                # price filter is set to their respective available prices when the specified
                # min exceeds the max, and / or the specified max is lower than the available min.
                if min_price:
                    min_price = min_price if min_price <= available_max_price else available_min_price
                    post['min_price'] = min_price
                if max_price:
                    max_price = max_price if max_price >= available_min_price else available_max_price
                    post['max_price'] = max_price

        website_domain = request.website.website_domain()
        categs_domain = [('parent_id', '=', False)] + website_domain
        if search:
            search_categories = Category.search([('product_tmpl_ids', 'in', search_product.ids)] + website_domain).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
        else:
            search_categories = Category
        categs = Category.search(categs_domain)

        if category:
            url = "/shop/category/%s" % slug(category)

        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        offset = pager['offset']
        # products = search_product[offset:offset + ppg]
        Product = request.env['product.template'].with_context(bin_size=True)
        domain = self._get_search_domain(search, category, attrib_values, filter_values)
        products = Product.search(domain, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))

        ProductAttribute = request.env['product.attribute']
        ProductFilter = request.env['product.filter']
        filters = grouped_tasks = None
        if products:
            # get all products without limit
            attributes = ProductAttribute.search([
                ('product_tmpl_ids', 'in', search_product.ids),
                ('visibility', '=', 'visible'),
            ])
            selected_products = Product.search(domain, limit=False)
            
            filters = ProductFilter.search([('filter_value_ids', '!=', False), ('filter_ids.product_tmpl_id', 'in', selected_products.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)
            filters = ProductFilter.browse(filter_ids)

        filter_group = request.env['group.filter'].search([])

        applied_filter = False
        if filter_values:
            applied_filter = True

        if filter_group:
            grouped_tasks = [request.env['product.filter'].concat(*g) for k, g in groupbyelem(filters, itemgetter('group_id'))]
        else:
            grouped_tasks = [filters]

        layout_mode = request.session.get('website_sale_shop_layout_mode')
        if not layout_mode:
            if request.website.viewref('website_sale.products_list_view').active:
                layout_mode = 'list'
            else:
                layout_mode = 'grid'

        prods  = Product.sudo().search(domain)
        request.website.sudo().get_dynamic_count(prods)

        values = {
            'search': fuzzy_search_term or search,
            'original_search': fuzzy_search_term and search,
            'order': post.get('order', ''),
            'category': category,
            'attrib_values': attrib_values,
            'filter_set': filter_set,
            'filter_values': filter_values,
            'applied_filter':applied_filter,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'grouped_tasks':grouped_tasks,
            'add_qty': add_qty,
            'products': products,
            'filters': filters,
            'search_product': search_product,
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, ppg, ppr),
            'ppg': ppg,
            'ppr': ppr,
            'categories': categs,
            'attributes': attributes,
            'keep': keep,
            'filter_group' : filter_group,
            'search_categories_ids': search_categories.ids,
            'layout_mode': layout_mode,
        }
        if filter_by_price_enabled:
            values['min_price'] = min_price or available_min_price
            values['max_price'] = max_price or available_max_price
            values['available_min_price'] = tools.float_round(available_min_price, 2)
            values['available_max_price'] = tools.float_round(available_max_price, 2)
        if category:
            values['main_object'] = category
        values.update(self._get_additional_shop_values(values))
        return request.render("website_sale.products", values)

class WebsiteInherit(Website):
    @http.route('/website/snippet/autocomplete', type='json', auth='public', website=True)
    def autocomplete(self, search_type=None, term=None, order=None, limit=5, max_nb_chars=999, options=None):
        """
        Returns list of results according to the term and options

        :param str search_type: indicates what to search within, 'all' matches all available types
        :param str term: search term written by the user
        :param str order:
        :param int limit: number of results to consider, defaults to 5
        :param int max_nb_chars: max number of characters for text fields
        :param dict options: options map containing
            allowFuzzy: enables the fuzzy matching when truthy
            fuzzy (boolean): True when called after finding a name through fuzzy matching

        :returns: dict (or False if no result) containing
            - 'results' (list): results (only their needed field values)
                    note: the monetary fields will be strings properly formatted and
                    already containing the currency
            - 'results_count' (int): the number of results in the database
                    that matched the search query
            - 'parts' (dict): presence of fields across all results
            - 'fuzzy_search': search term used instead of requested search
        """
       
        res = super(WebsiteInherit, self).autocomplete(search_type, term, order, limit, max_nb_chars, options)
    
        return res