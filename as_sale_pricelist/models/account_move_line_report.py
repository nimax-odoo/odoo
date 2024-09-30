from odoo import models, fields, api, tools

class AccountMoveLineReport(models.Model):
    _name = 'account.move.line.report'
    _description = 'Account Move Line Report'
    _auto = False
    
    numero_factura = fields.Char(string='Número de Factura')
    partner = fields.Char(string='Partner')
    fecha_factura = fields.Date(string='Fecha de Factura')
    fecha_vencimiento = fields.Date(string='Fecha de Vencimiento')
    nombre_producto = fields.Char(string='Nombre del Producto')
    empresa = fields.Char(string='Empresa')
    total_sin_impuesto = fields.Float(string='Precio de venta unitario')
    estado_de_pago = fields.Selection([
        ('paid', 'Paid'),
        ('not_paid', 'Not Paid')
    ], string='Estado de Pago')
    last_applied_promo = fields.Char(string='Última Promoción Aplicada')
    recalculated_cost_nimax_usd = fields.Float(string='Costo Recalculado (USD)')
    x_studio_margen = fields.Float(string='Margen')
    promo_aplicada = fields.Char(string='Ultima promocion aplicada')
    margen_usd = fields.Float(string='Margen')
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute("""
        CREATE OR REPLACE VIEW {} as (
        WITH unique_aml AS (
        SELECT DISTINCT ON (aml.id)
            aml.id AS id,
            am.name AS numero_factura,
            rp.name AS partner,
            am.invoice_date AS fecha_factura,
            am.invoice_date_due AS fecha_vencimiento,
            pp.name AS nombre_producto,
            rc.name AS empresa,
            aml.price_unit AS precio_de_venta_unitario,
            aml.price_subtotal AS total_sin_impuesto,
            am.payment_state AS estado_de_pago,
            ppl.name AS promo_aplicada,
            tfp.recalculated_cost_nimax_usd,
            ROUND(CAST(tfp.margin_usd AS numeric), 2) AS margen_usd
        FROM
            public.account_move_line aml
        JOIN
            public.account_move am ON aml.move_id = am.id
        LEFT JOIN
            public.sale_order so ON am.invoice_origin = so.name
        LEFT JOIN
            public.tf_history_promo tfp ON so.id = tfp.sale_id
        LEFT JOIN
            public.product_template pp ON aml.product_id = pp.id
        LEFT JOIN
            public.res_partner rp ON am.partner_id = rp.id
        LEFT JOIN
            public.res_company rc ON am.company_id = rc.id
        LEFT JOIN
            public.product_pricelist ppl ON tfp.as_pricelist_id = ppl.id
        WHERE
            am.move_type = 'out_invoice'
            AND am.payment_state = 'paid'
            AND pp.name IS NOT NULL
            AND pp.name <> ''
        
    )
    SELECT
        id,
        numero_factura,
        partner,
        fecha_factura,
        fecha_vencimiento,
        nombre_producto,
        empresa,
        precio_de_venta_unitario,
        total_sin_impuesto,
        estado_de_pago,
        promo_aplicada,
        recalculated_cost_nimax_usd,
        margen_usd
    FROM
        unique_aml
    ORDER BY
        fecha_factura DESC)

        """.format(self._table))