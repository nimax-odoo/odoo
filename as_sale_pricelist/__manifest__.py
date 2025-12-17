# -*- coding: utf-8 -*-
# Part of Ahorasoft.
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
    "version":"18.0.1.0.49",
    "depends" : [
        "base",
        "sale_management",
        'product',
        'account',
        'sale_margin',
        'as_product_last_price_tab',
        "purchase",
        # "loyalty",  # Eliminada esta dependencia para evitar problemas de normalización
        "crm",
        "stock",
        'report_xlsx',
        "sale",
        # "l10n_mx_edi",
        "stock_account",
        # "bi_manual_currency_exchange_rate",
        # "l10n_mx_edi_40",  # Eliminada esta dependencia que no está disponible
        "sales_team",
        ],
    "application" : True,
    "data" : [
              # Cargar primero datos y seguridad
              "security/ir.model.access.csv",
              'data/mail_template_data.xml',  # Disabled mail template data
              
              # Luego las vistas
              'views/as_product_template.xml',
              'views/sale_order_inherit_view.xml',
              'views/as_product_pricelist.xml',
              'views/as_partner_type.xml',
              'views/as_partner.xml',
              'views/as_marca.xml',
              'views/coupon_views.xml',
              'views/tf_as_partner.xml',
              'views/history_promo.xml',
              'views/product_pricelist.xml',
              'views/as_tabla_comisiones.xml',
              'views/as_res_config.xml',
              'views/tf_promotions_gift.xml',
              'views/sd_stock_quant.xml',
              'wizard/sd_sale_order_wiz.xml',
              # 'wizard/sd_free_owner_wiz.xml',


              'data/mail_template_ajust.xml',
              'security/security.xml',
              # 'views/report_sale_proforma.xml',
            #   'views/assets.xml',
              
              # Finalmente los wizards
              'wizard/sale_order_pricelist_update_wizard.xml',
              'wizard/as_promotion.xml',
              'wizard/as_report_comisiones.xml',
              'wizard/as_aprobe_utility.xml',
              'wizard/as_aprobe_utility.xml',
            ],            
    # "icon": "static/description/icon.png",
    "auto_install":False,
    "installable" : True,
    "license": "LGPL-3",
    # "post_init_hook": "migrations.remove_problematic_entry.migrate",
}