# -*- coding: utf-8 -*-
{
    'name': "Pricelist and Promo",

    'summary': 'Pricelist and Promo',

    'description': """
        Pricelist and Promo
    """,

    'author': "Sachin ",
    'website': "https://theerpstore.com/",
    'version': '1.0',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/as_partner.xml',
        'views/history_promo.xml',
        'views/product_pricelist.xml',
    ],
}
