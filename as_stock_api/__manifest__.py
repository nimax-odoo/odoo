# -*- encoding: utf-8 -*-
# © 2019 Piotr Cierkosz <info@cier.tech>
{
    "name": "Ahorasoft Inventario API",
    "version": "19.0.1.0.2",
    "category": "Stock",
    "author": "Ahorasoft",
    "depends": [
        "base",
        "stock",
        "as_sale_pricelist",
    ],
    "data": [
        'security/ir.model.access.csv',
        "views/as_res_users_views.xml",
        "views/custom_program.xml",
        "views/match_locations.xml",
        "views/sale_order.xml",
        "views/account_move.xml",
        "views/request_logger.xml",
        "data/cron.xml",
    ],
    'installable': True,
    'description': "API REST para consulta de stock en tiempo real",
    'website': "http://www.ahorasoft.com",
    'summary': 'API REST para consulta de stock',
    'external_dependencies': {
        'python': ['markdown'],
    },
    'assets': {
        'web.assets_backend': [
            'as_stock_api/static/postman/as_stock_api_collection.json',
        ],
    },
    'license': 'LGPL-3',
}
