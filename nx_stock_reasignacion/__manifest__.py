{
    "name": "Nimax - Reasignacion de piezas entre pedidos",
    "summary": "Permite reasignar reservas del mismo producto entre pedidos de venta",
    "version": "19.0.1.0.0",
    "category": "Inventory/Inventory",
    "author": "Nimax",
    "license": "LGPL-3",
    "depends": ["sale_stock", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
        "wizard/stock_reassignment_wizard_views.xml"
    ],
    "installable": True,
    "application": False,
}
