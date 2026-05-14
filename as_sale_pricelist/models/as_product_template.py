# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class as_product_template(models.Model):
    _inherit = 'product.template'

    @tools.ormcache()
    def _get_default_category_id(self):
        # Deletion forbidden (at least through unlink)
        return self.env.ref('product.product_category_services')
    
    as_proveedor = fields.Many2one(comodel_name='res.partner', string='Cliente - Proveedor')
    tf_import_tax = fields.Float('IMPORT TAX')
    as_product_comisionable = fields.Boolean('Producto no Comisionable')
    as_zebra = fields.Boolean('Es Zebra')
    default_code = fields.Char('SKU ó No. de Parte', index=True,tracking=True)
    standard_price = fields.Float(
        'Costo', compute='_compute_standard_price',
        inverse='_set_standard_price', search='_search_standard_price',
        digits='Product Price', groups="base.group_user",
        help="""Value of the product (automatically computed in AVCO).
        Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
        Used to compute margins on sale orders.""",tracking=True)
    categ_id = fields.Many2one(
        'product.category', 'Categoría',
        change_default=True, default=_get_default_category_id, group_expand='_read_group_categ_id',
        required=True,tracking=True)
    #campos para el historial de ingresos
    sd_partner_id = fields.Many2one('res.partner', string='Cliente - Proveedor')
    sd_fecha = fields.Datetime('Fecha ultimo ingreso')
    sd_picking_id = fields.Many2one('stock.picking', string='Picking')
    sd_purchase_id = fields.Many2one('purchase.order', string='Orden de Compra')
    sd_fecha_invoice = fields.Date('Fecha Factura')
    sd_invoice_id = fields.Many2one('account.move', string='Factura de Compra')


    def _actualizar_data_productos_compra(self):
        _logger.info('Iniciando actualización de data de productos de compra...')

        StockMove = self.env['stock.move']
        ProductTmpl = self.env['product.template']

        products = ProductTmpl.search([
            ('type', '=', 'consu'),
            ('is_storable', '=', True)
        ])
        # products = ProductTmpl.search([('type', '=', 'consu'),('is_storable', '=', True),('id', 'in', (19295
        #     ,5514
        #     ,5545
        #     ))])
        # 🔹 Buscar todos los movimientos relevantes
        moves = StockMove.search([
            ('product_id.product_tmpl_id', '=', products.ids),
            ('purchase_line_id', '!=', False),
            ('state', '=', 'done'),('location_usage', 'in', ('supplier'))
        ], order='date desc')

        last_moves = {}

        for move in moves:
            tmpl_id = move.product_id.product_tmpl_id.id

            # 🔹 Obtener devoluciones relacionadas
            returned_moves = move.returned_move_ids.filtered(lambda m: m.state == 'done')

            qty_returned = sum(returned_moves.mapped('product_uom_qty'))
            qty_original = move.product_uom_qty

            # 🔹 Validar devolución total
            if qty_returned >= qty_original:
                continue  # ❌ ignorar este movimiento

            # 🔹 Si aún no tengo uno válido, lo guardo
            if tmpl_id not in last_moves:
                last_moves[tmpl_id] = move

        # 🔹 Asignar valores
        for product in products:
            move = last_moves.get(product.id)
            if move:
                po = move.purchase_line_id.order_id

                product.sd_partner_id = po.partner_id.id
                product.sd_fecha = po.picking_ids[:1].date_done if po.picking_ids else False
                product.sd_picking_id = po.picking_ids[:1].id if po.picking_ids else False
                product.sd_purchase_id = po.id
                sd_fecha_invoice = po.invoice_ids[:1].date if po.invoice_ids else False
                product.sd_fecha_invoice = sd_fecha_invoice
                product.sd_invoice_id = po.invoice_ids[:1].id if po.invoice_ids else False

        _logger.info('Actualización de data de productos de compra completada.')