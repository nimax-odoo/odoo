
# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name" : "Ahorasoft Lista de Precios por Linea de Productos en Ventas",
    "author" : "Ahorasoft",
    "website": "http://www.ahorasoft.com",
    "support": "soporte@ahorasoft.com",
    "category": "Product",
    "summary": "Lista de precios por linea de producto en ventas.",
    "description": """
Lista de precios por linea de producto en ventas.
""",    
    "version":"13.0.1",
    "depends" : [
        "base",
        "sale_management",
        'product',
        'sale_margin',
        'as_product_last_price_tab',
        "purchase"
        ],
    "application" : True,
    "data" : [
              "security/ir.model.access.csv",
              'views/sale_order_inherit_view.xml',
              'views/as_product_pricelist.xml',
              'views/as_partner_type.xml',
              'views/as_partner.xml',
              'views/as_product_template.xml',
              'wizard/sale_order_pricelist_update_wizard.xml',
            ],            
    "images": ["static/description/background.png",],              
    "auto_install":False,
    "installable" : True,
}