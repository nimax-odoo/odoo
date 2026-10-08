# -*- coding: utf-8 -*-
{
    'name': 'Zebra Existencia de Productos',
    'version': '18.0.1.0.0',
    'summary': 'Reporte ordenable de existencia por producto',
    'description': '''
Aplicación simple para consultar existencia por product.template.
La existencia se calcula desde stock.quant en ubicaciones internas.
El campo Existencia es una columna SQL real para poder ordenar manualmente de mayor a menor o menor a mayor.
    ''',
    'author': 'Nimax',
    'category': 'Inventory/Inventory',
    'depends': ['stock', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_stock_report_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
