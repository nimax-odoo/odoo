from odoo.exceptions import UserError

# Campos de Studio / otros módulos que ya deben existir en sale.order
REQUERIDOS = {
    'x_studio_ordenado_a_fabricante': 'Ordenado a Fabricante (casilla)',
    'x_studio_marca': 'Marca (selección)',
    'x_studio_orden_de_compra': 'Orden de Compra del cliente (carácter)',
    'x_studio_comentarios': 'Comentarios (texto)',
    'as_usuario_final': 'Usuario Final (módulo as_sale_pricelist)',
}


def pre_init_check(env):
    env.cr.execute(
        "SELECT name FROM ir_model_fields WHERE model = 'sale.order' AND name IN %s",
        [tuple(REQUERIDOS)])
    existentes = {r[0] for r in env.cr.fetchall()}
    faltan = [f"{n}  ->  {d}" for n, d in REQUERIDOS.items() if n not in existentes]
    if faltan:
        raise UserError(
            "No se puede instalar: faltan estos campos en el pedido de venta (sale.order). "
            "Créalos primero (Ajustes > Técnico > Modelos > sale.order > Campos) "
            "con el mismo nombre técnico:\n\n" + "\n".join(faltan))
