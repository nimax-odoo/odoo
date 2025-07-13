# -*- coding: utf-8 -*-
{
    'name': 'AS MX Factura Electrónica (CFDI)',
    'summary': 'Mejoras para la Facturación Electrónica Mexicana (CFDI)',
    'description': """
Mejoras para la Facturación Electrónica Mexicana (CFDI)
=======================================================
Este módulo extiende la funcionalidad de facturación electrónica mexicana de Odoo:
- Botón para timbrado manual de facturas
- Verificación de PAC y certificados
- Herramientas de diagnóstico para CFDI
- Mejora en el formato de impresión de facturas
- Correcciones para tipos de cambio en facturas en USD
""",
    'author': 'Ahorasoft',
    'website': 'http://www.ahorasoft.com',
    'category': 'Accounting/Localization/Mexico',
    'version': '1.0.35',
    'depends': [
        'l10n_mx_edi',
        'account',
        'website',
        'bi_manual_currency_exchange_rate',
    ],
    'data': [
        "security/ir.model.access.csv",
        'views/account_move_view.xml',
        'views/as_report_format.xml',
        'views/report/as_report_invoice_mx.xml',
        'views/report/report_payment_receipt_document.xml',
        'views/account_payment_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
} 