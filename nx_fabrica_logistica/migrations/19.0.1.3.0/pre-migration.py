import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Se ejecuta al ACTUALIZAR el módulo desde 19.0.1.0.0 / 19.0.1.2.0.
    Mismas dos preparaciones que pre_init_check (que solo corre al instalar)."""
    # 1) Columnas de campos calculados guardados: evita recalcular toda la tabla
    cr.execute("ALTER TABLE sale_order_line ADD COLUMN IF NOT EXISTS nx_estado VARCHAR")
    cr.execute("ALTER TABLE sale_order_line ADD COLUMN IF NOT EXISTS nx_cerrado BOOLEAN")
    cr.execute("""
        UPDATE sale_order_line SET nx_cerrado = (nx_estado = 'facturado')
        WHERE nx_estado IS NOT NULL AND nx_cerrado IS NULL
    """)
    # 2) Casilla de Studio obligatoria con valores NULL (genera un ERROR al tocar sale.order)
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
