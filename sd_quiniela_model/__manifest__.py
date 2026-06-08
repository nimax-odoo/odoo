# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Modulo quiniela para NIMAX",
    "version" : "19.0.0.1",
    "depends" : ['base','website','portal'],
    "author": "Smartdoo",
    "summary": "Cambios en modulo quiniela para NIMAX",
    "description": """
            Cambios en modulo quiniela para NIMAX
    """,
    'category': 'Sales',
    "website" : "http://www.smartdoosolutions.com",
    "data" :[
            "security/ir.model.access.csv",
            "views/menu_website.xml",
            "views/sd_quiniela_data.xml",
            "views/sd_quiniela_partidos.xml",
            "views/sd_quiniela_pronostico.xml",
            "views/sd_register_winner.xml",
            "views/sd_template_website.xml",

        ],
    'qweb':[],
    "auto_install": False,
    "installable": True,
    'live_test_url':'http://www.smartdoosolutions.com',
	"images":['static/description/Banner.gif'],
    "license": "OPL-1",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
