# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Cambios en el Modulo Comercial (Ventas)",
    "version" : "18.0.0.1",
    "depends" : ['base','account','sale_management','sale','stock'],
    "author": "Smartdoo",
    "summary": "Cambios en modulo comercial de ventas para NIMAX",
    "description": """
            Cambios en modulo comercial de ventas para NIMAX
    """,
    'category': 'Sales',
    "website" : "http://www.smartdoosolutions.com",
    "data" :[

             "views/product_category.xml",
             "views/product_template.xml",
             "views/sale_order.xml",
             "data/cron.xml",
        ],
    'qweb':[],
    "auto_install": False,
    "installable": True,
    'live_test_url':'http://www.smartdoosolutions.com',
	"images":['static/description/Banner.gif'],
    "license": "OPL-1",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
