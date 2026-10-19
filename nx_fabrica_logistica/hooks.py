import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Campos de Studio / otros módulos que ya deben existir en sale.order
REQUERIDOS = {
    'x_studio_ordenado_a_fabricante': 'Ordenado a Fabricante (casilla)',
    'x_studio_marca': 'Marca (selección)',
    'x_studio_orden_de_compra': 'Orden de Compra del cliente (carácter)',
    'x_studio_comentarios': 'Comentarios (texto)',
    'as_usuario_final': 'Usuario Final (módulo as_sale_pricelist)',
}


def preparar_columnas(cr):
    """Crea a mano las columnas de los campos calculados guardados de sale.order.line.

    Si no existen, Odoo recalcula esos campos para TODAS las líneas de venta al instalar
    o actualizar (cientos de miles de filas), con riesgo de agotar tiempo o memoria.
    Ninguna línea existente está marcada "Solicitar a Fabrica", así que el valor correcto
    de todas ellas es vacío (NULL = Falso) y no hay nada que calcular.
    """
    cr.execute("ALTER TABLE sale_order_line ADD COLUMN IF NOT EXISTS nx_estado VARCHAR")
    cr.execute("ALTER TABLE sale_order_line ADD COLUMN IF NOT EXISTS nx_cerrado BOOLEAN")
    # Solo aplica al actualizar desde una versión anterior que ya tenga líneas con estado
    cr.execute("""
        UPDATE sale_order_line SET nx_cerrado = (nx_estado = 'facturado')
        WHERE nx_estado IS NOT NULL AND nx_cerrado IS NULL
    """)


def corregir_nulos_studio(cr):
    """x_recoleccion_sucursal (casilla de Studio) está marcada como obligatoria pero hay
    pedidos con valor NULL. Cada vez que se instala/actualiza un módulo que toca sale.order,
    Odoo intenta ponerle NOT NULL y registra un ERROR. NULL y Falso son lo mismo para Odoo,
    así que se normaliza. Si no existe el campo, no hace nada. QUITAR este bloque si se
    prefiere corregirlo desde Studio."""
    cr.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sale_order' AND column_name = 'x_recoleccion_sucursal'
          AND data_type = 'boolean'
    """)
    if cr.fetchone():
        cr.execute("UPDATE sale_order SET x_recoleccion_sucursal = FALSE "
                   "WHERE x_recoleccion_sucursal IS NULL")
        _logger.info("nx_fabrica_logistica: x_recoleccion_sucursal NULL -> FALSE en %s pedidos",
                     cr.rowcount)


def pre_init_check(env):
    cr = env.cr
    cr.execute(
        "SELECT name FROM ir_model_fields WHERE model = 'sale.order' AND name IN %s",
        [tuple(REQUERIDOS)])
    existentes = {r[0] for r in cr.fetchall()}
    faltan = [f"{n}  ->  {d}" for n, d in REQUERIDOS.items() if n not in existentes]
    if faltan:
        raise UserError(
            "No se puede instalar: faltan estos campos en el pedido de venta (sale.order). "
            "Créalos primero (Ajustes > Técnico > Modelos > sale.order > Campos) "
            "con el mismo nombre técnico:\n\n" + "\n".join(faltan))
    preparar_columnas(cr)
    corregir_nulos_studio(cr)
