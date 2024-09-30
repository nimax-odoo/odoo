{
    'name': 'Website Sale Product Stock',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Muestra el stock disponible en la página de producto del eCommerce',
    'author': 'The Godlike Odoo Programmer',
    'website': 'https://www.example.com',
    'depends': ['website_sale', 'stock'],
    'data': [
        'views/as_product_template_inherit.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
