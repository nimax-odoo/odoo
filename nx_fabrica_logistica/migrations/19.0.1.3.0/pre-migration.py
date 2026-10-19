def migrate(cr, version):
    """Se ejecuta al ACTUALIZAR el módulo a partir de la versión 19.0.1.3.0.
    Solo prepara las columnas propias del módulo (evita recalcular toda la tabla
    sale_order_line al actualizar). No toca ningún campo ajeno al módulo."""
    cr.execute("ALTER TABLE sale_order_line ADD COLUMN IF NOT EXISTS nx_estado VARCHAR")
    cr.execute("ALTER TABLE sale_order_line ADD COLUMN IF NOT EXISTS nx_cerrado BOOLEAN")
    cr.execute("""
        UPDATE sale_order_line SET nx_cerrado = (nx_estado = 'facturado')
        WHERE nx_estado IS NOT NULL AND nx_cerrado IS NULL
    """)
