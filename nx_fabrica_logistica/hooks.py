import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Campos de Studio / otros módulos que ya deben existir: (modelo, campo, descripción)
REQUERIDOS = [
    ('sale.order', 'x_studio_ordenado_a_fabricante', 'Ordenado a Fabricante (casilla)'),
    ('sale.order', 'x_studio_marca', 'Marca (selección)'),
    ('sale.order', 'x_studio_orden_de_compra', 'Orden de Compra del cliente (carácter)'),
    ('sale.order', 'x_studio_comentarios', 'Comentarios (texto)'),
    ('sale.order', 'as_usuario_final', 'Usuario Final (módulo as_sale_pricelist)'),
    ('res.partner', 'x_studio_sucursal', 'Sucursal del contacto (selección: CDMX, MTY, GDL)'),
]


def preparar_columnas(cr):
    """Crea a mano las columnas de los campos calculados guardados de sale.order.line.

    Si no existen, Odoo recalcula esos campos para TODAS las líneas de venta al instalar
    o actualizar (cientos de miles de filas), con riesgo de agotar tiempo o memoria.
    Ninguna línea existente está marcada "Solicitar a Fabrica", así que el valor correcto
    de todas ellas es vacío (NULL = Falso) y no hay nada que calcular.
    """
    cr.execute("ALTER TABLE sale_order_line ADD COLUMN IF NOT EXISTS nx_estado VARCHAR")
    cr.execute("ALTER TABLE sale_order_line ADD COLUMN IF NOT EXISTS nx_cerrado BOOLEAN")
    cr.execute("""
        UPDATE sale_order_line SET nx_cerrado = (nx_estado = 'facturado')
        WHERE nx_estado IS NOT NULL AND nx_cerrado IS NULL
    """)


def corregir_nulos_studio(cr):
    """x_recoleccion_sucursal (casilla de Studio) está marcada como obligatoria pero hay
    pedidos con valor NULL. Cada vez que se instala/actualiza un módulo que toca sale.order,
    Odoo intenta ponerle NOT NULL y registra un ERROR. NULL y Falso son lo mismo para Odoo,
    así que se normaliza. Si no existe el campo, no hace nada."""
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
    faltan = []
    for modelo, campo, descripcion in REQUERIDOS:
        cr.execute("SELECT 1 FROM ir_model_fields WHERE model = %s AND name = %s", [modelo, campo])
        if not cr.fetchone():
            faltan.append(f"{modelo}  ->  {campo}  ({descripcion})")
    if faltan:
        raise UserError(
            "No se puede instalar: faltan estos campos. Créalos primero "
            "(Ajustes > Técnico > Modelos > Campos) con el mismo nombre técnico:\n\n"
            + "\n".join(faltan))
    preparar_columnas(cr)
    corregir_nulos_studio(cr)
