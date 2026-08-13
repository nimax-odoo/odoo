# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
import psycopg2

import odoo.api
import odoo.exceptions
import odoo.modules.registry
from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request

class accessLogger(http.Controller):

    @http.route('/access_successful/process', type='http', auth='public', methods=['POST'], csrf=False)
    def process_form(self, **post):
        def redirect(success=True, partner=None, error_message=None):
            pass
    
    @http.route('/access_successful', type='http', auth="public", website=True)
    def access_successful(self, **kw):
        return request.render('sd_sales_ecommerce.access_successful_page', {'error': kw.get('error')})

    @http.route('/access_successful/partner', type="jsonrpc", auth="public", website=True)
    def get_html_content(self, vat):
        partners = request.env['res.partner'].sudo().get_partner_id(vat)
        if not partners:
            return {'error': 'No se encontró ningún socio con el RFC proporcionado.'}
        return {'partner': partners}
