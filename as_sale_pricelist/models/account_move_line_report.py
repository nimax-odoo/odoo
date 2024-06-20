from odoo import models, fields, api

class AccountMoveLineReport(models.Model):
    _name = 'account.move.line.report'
    _description = 'Account Move Line Report'
    
    numero_factura = fields.Char(string='Número de Factura')
    partner = fields.Char(string='Partner')
    fecha_factura = fields.Date(string='Fecha de Factura')
    fecha_vencimiento = fields.Date(string='Fecha de Vencimiento')
    nombre_producto = fields.Char(string='Nombre del Producto')
    empresa = fields.Char(string='Empresa')
    total_sin_impuesto = fields.Float(string='Total sin Impuesto')
    estado_de_pago = fields.Selection([
        ('paid', 'Paid'),
        ('not_paid', 'Not Paid')
    ], string='Estado de Pago')
    last_applied_promo = fields.Char(string='Última Promoción Aplicada')
    recalculated_cost_nimax_usd = fields.Float(string='Costo Recalculado (USD)')
    x_studio_margen = fields.Float(string='Margen')

    @api.model
    def fetch_report_data(self):
        # Borra los registros existentes antes de la inserción
        self.env['account.move.line.report'].search([]).unlink()
        # Realiza la inserción de los nuevos datos
        query = """
        INSERT INTO account_move_line_report (numero_factura, partner, fecha_factura, fecha_vencimiento, nombre_producto, empresa, total_sin_impuesto, estado_de_pago, last_applied_promo, recalculated_cost_nimax_usd, x_studio_margen)
        SELECT DISTINCT
            am.name AS numero_factura,
            rp.name AS partner,
            am.invoice_date AS fecha_factura,
            am.invoice_date_due AS fecha_vencimiento,
            pp.name AS nombre_producto,
            rc.name AS empresa,
            aml.price_unit AS total_sin_impuesto,
            am.payment_state AS estado_de_pago,
            tfp.last_applied_promo,
            tfp.recalculated_cost_nimax_usd,
            tfp.x_studio_margen
        FROM
            public.account_move am
        JOIN
            public.account_move_line aml ON aml.move_id = am.id
        LEFT JOIN
            public.sale_order so ON am.invoice_origin = so.name  -- Unir con sale_order usando invoice_origin
        LEFT JOIN
            public.tf_history_promo tfp ON so.id = tfp.sale_id  -- Unir tf_history_promo con sale_order
        LEFT JOIN
            public.product_template pp ON aml.product_id = pp.id
        LEFT JOIN
            public.res_partner rp ON am.partner_id = rp.id
        LEFT JOIN
            public.res_company rc ON am.company_id = rc.id
        WHERE
            am.move_type = 'out_invoice'
            AND am.payment_state = 'paid'
            AND pp.name IS NOT NULL
            AND pp.name <> ''
        
        ORDER BY
            am.invoice_date DESC;

        """
        self.env.cr.execute(query)
        self.env.cr.commit()

        return True

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountMoveLineReport, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        if view_type == 'tree':
            self.fetch_report_data()

        return res
