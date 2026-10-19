{
    'name': 'Nimax - Pedidos a fábrica (Logística)',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Solicitar a fábrica -> PM -> Logística asigna OC -> llegada -> facturado',
    'description': """
Flujo
-----
1. Vendedor: marca "Solicitar a Fabrica" en la línea del pedido.
2. PM: en el pedido marca "Ordenado a Fabricante" y asigna la Marca.
3. Logística: en la lista "Pedidos a fábrica" elige la OC (solo sin confirmar).
   El sistema inserta producto y cantidad en esa OC y la enlaza con la línea de venta.
4. Todo lo demás (FechaOC, entradas, llegada, días, estado de entrega, factura)
   se jala solo y se actualiza con el proceso.

Usa campos y relaciones que ya existen en Odoo (sale_purchase: sale_line_id /
purchase_line_ids). No crea modelos nuevos de seguimiento.
    """,
    'author': 'Nimax',
    'depends': ['sale', 'sale_stock', 'purchase', 'purchase_stock', 'sale_purchase', 'mail'],
    'pre_init_hook': 'pre_init_check',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/config.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'wizard/asignar_oc_wizard_views.xml',
        'views/fabrica_line_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
