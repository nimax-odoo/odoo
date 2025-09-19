# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Cambios en el Modulo E-Commerce",
    "version" : "18.0.0.1",
    "depends" : ['base','account','sale_management','sale','website_sale','website_sale_stock','bi_manual_currency_exchange_rate','as_sale_pricelist',],
    "author": "Smartdoo",
    "summary": "Cambios en modulo comercial de ventas para NIMAX",
    "description": """
            Cambios en modulo comercial de ventas para NIMAX
    """,
    'category': 'Sales',
    "website" : "http://www.smartdoosolutions.com",
    "data" :[
            'views/website_product_template.xml',
            "views/custom_program.xml",
            'views/res_users_views.xml',
            "data/cron.xml",
            "data/mail_template.xml",
        ],
    'qweb':[],
    "auto_install": False,
    "installable": True,
    'live_test_url':'http://www.smartdoosolutions.com',
	"images":['static/description/Banner.gif'],
    "license": "OPL-1",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
