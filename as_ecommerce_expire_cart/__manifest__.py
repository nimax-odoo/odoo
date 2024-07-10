# -*- coding: utf-8 -*-
{
    'name': 'As_ecommerce_expire_cart',
    'version': '15.0.1.0.0',
    'summary': """ As_ecommerce_expire_cart Summary """,
    'author': 'Ahora Soft',
    'website': '',
    'category': '',
    'depends': ['base', 'web', 'website_sale'],
    'data': [
        "data/scheduled_action.xml",
        "views/res_config_settings.xml",
        "views/templates.xml",
        
    ],'assets': {
            'web.assets_backend': [
                'as_ecommerce_expire_cart/static/src/scss/*.scss',
                'as_ecommerce_expire_cart/static/src/js/*.js'
            ],
            "web.assets_frontend": [
                "as_ecommerce_expire_cart/static/src/js/*.js",
            ],
            'web.assets_qweb': [
                'as_ecommerce_expire_cart/static/src/xml/*.xml',
            ],
        },
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
