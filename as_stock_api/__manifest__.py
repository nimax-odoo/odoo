# -*- encoding: utf-8 -*-
# © 2019 Piotr Cierkosz <info@cier.tech>
{
    "name": "Ahorasoft Inventario API",
    "version": "1.0.23",
    "category": "Stock",
    "author": "Ahorasoft",
    "depends": [
        "base",
        "stock",
    ],
    "data": [
        'security/ir.model.access.csv',
        "views/as_res_users_views.xml",
    ],
    'installable' : True,
    'description' : "API REST para consulta de stock en tiempo real",
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
}
