# -*- coding: utf-8 -*-

from odoo import fields, models, tools, _


class ZebraProductTemplateStockReport(models.Model):
    _name = 'zebra.product.template.stock.report'
    _description = 'Zebra Existencia por Producto'
    _auto = False
    _order = 'qty_available desc, product_tmpl_id asc'
    _rec_name = 'product_tmpl_id'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Producto',
        readonly=True,
        index=True,
    )
    qty_available = fields.Float(
        string='Existencia',
        readonly=True,
        digits='Product Unit of Measure',
        help='Existencia calculada desde stock.quant únicamente en ubicaciones internas.',
    )

    def init(self):
        """Crea la vista SQL del reporte.

        Decisión técnica importante:
        No usamos directamente product.template.qty_available porque en Odoo es un
        campo calculado/contextual y puede no ordenar correctamente en una vista lista.

        Aquí qty_available sí queda como columna SQL de la vista, por eso el usuario
        puede dar clic en la columna Existencia y ordenar manualmente.

        Criterio:
        - Producto base: product.template.
        - Existencia: SUM(stock_quant.quantity).
        - Solo ubicaciones internas: stock_location.usage = 'internal'.
        - Agrupa variantes del producto en su template.
        - Muestra productos activos aunque estén en 0.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW zebra_product_template_stock_report AS (
                SELECT
                    pt.id AS id,
                    pt.id AS product_tmpl_id,
                    COALESCE(SUM(
                        CASE
                            WHEN sl.usage = 'internal' THEN sq.quantity
                            ELSE 0.0
                        END
                    ), 0.0) AS qty_available
                FROM product_template pt
                    JOIN product_product pp
                        ON pp.product_tmpl_id = pt.id
                    LEFT JOIN stock_quant sq
                        ON sq.product_id = pp.id
                    LEFT JOIN stock_location sl
                        ON sl.id = sq.location_id
                WHERE pt.active = TRUE
                GROUP BY pt.id
            )
        """)

    def action_open_product_template(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Producto'),
            'res_model': 'product.template',
            'res_id': self.product_tmpl_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
