# -*- coding: utf-8 -*-
# Part of Ahorasoft.

{
    'name': 'Ahorasoft Product Last Price Tab',
    'version': '18.0.2.0.0',
    'author': 'Ahorasoft',
    'website': 'http://www.ahorasoft.com',
    'category': 'Product',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'product',
        'purchase',
        'sale',
    ],
    'data': [
        'views/product_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'description': """
Product Last Price Tab
=====================
Adds a tab in products showing:
- Last purchase price and supplier
- Last sale price and customer

Updated for Odoo 18.0 Enterprise compatibility.
    """,
} 