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


def pre_init_check(env):
    """Se ejecuta SOLO al instalar el módulo por primera vez en una base.
    Únicamente valida requisitos y prepara columnas propias del módulo.
    NO debe tocar ningún campo ajeno (por ejemplo, de Studio) que no sea de este módulo."""
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
