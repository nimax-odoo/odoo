{
    'name': 'Nimax - Pedidos a fábrica (Logística)',
    'version': '19.0.1.4.0',
    'category': 'Inventory/Purchase',
    'summary': 'Solicitar a fábrica -> PM -> Logística asigna OC -> llegó a almacén -> facturado -> cerrado',
    'description': """
Flujo
-----
1. Vendedor: marca "A fábrica" (Solicitar a Fabrica) en la línea del pedido.
2. PM: en el pedido marca "Ordenado a Fabricante" y asigna la Marca.
3. Logística: en la lista "Pedidos a fábrica" elige la OC (solo sin confirmar).
   El sistema inserta producto y cantidad en esa OC y la enlaza con la línea de venta.
4. Logística captura en la OC la "Orden del fabricante" y la nota de Compras.
5. Todo lo demás (FechaOC, entradas, llegada, días, estado de entrega, factura) se jala solo.
   Al facturarse la línea queda "Cerrada" y sale de la lista de abiertos.

Sucursal: se lee en vivo del contacto del vendedor (campo x_studio_sucursal).
Colores: verde = proceso completo (facturado); rojo = algo anda mal (cancelado, retrasado,
llegó y lleva más de N días sin facturar, o lleva más de N días sin ordenarse/asignarse).
N = parámetro nx_fabrica_logistica.dias_alerta (15 por defecto).
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
