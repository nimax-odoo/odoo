# -*- encoding: utf-8 -*-
# © 2019 Piotr Cierkosz <info@cier.tech>
{
    "name": "Ahorasoft Inventario",
    "version": "1.0.3",
    "category": "Stock",
    "author": "Piotr Cierkosz",
    "depends": [
        "base",
        "stock",
        "stock_barcode",
    ],
    "data": [
        'security/ir.model.access.csv',
        "views/as_stock_picking.xml",
        "wizard/as_kardex_productos_wiz.xml",
    ],
    'installable' : True,
    'description' : "Desarrollos relacionados a inventario",
    'website': "https://www.cier.tech",
    'summary': 'Desarrollos relacionados a inventario',

}
