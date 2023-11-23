# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import uuid
import time
import datetime
from datetime import datetime, timedelta, date
from time import mktime
from dateutil.relativedelta import relativedelta

class Picking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        if self.picking_type_id.code in ('outgoing','internal'):
            for line_move in self.move_ids_without_package:
                if line_move.as_product_stock <= 0.0:
                    raise UserError(_("No se puede confirmar el producto %s código %s no tiene stock en la ubicación de origen %s.")%(line_move.product_id.name,line_move.product_id.default_code,line_move.location_id.complete_name))
            for line_move_line in self.move_line_ids_without_package:
                if line_move_line.as_product_stock <= 0.0:
                    raise UserError(_("No se puede confirmar el producto %s código %s no tiene stock en la ubicación de origen %s.")%(line_move_line.product_id.name,line_move_line.product_id.default_code,line_move_line.location_id.complete_name))

        res = super().button_validate()
        return res

    @api.model
    def filter_on_product(self, barcode):
        """ Search for ready pickings for the scanned product. If at least one
        picking is found, returns the picking kanban view filtered on this product.
        """
        
        product = self.env['product.product'].search_read([('barcode', '=', barcode)], ['id'], limit=1)
        if product:
            product_id = product[0]['id']
            picking_type = self.env['stock.picking.type'].search_read(
                [('id', '=', self.env.context.get('active_id'))],
                ['name'],
            )[0]
            if not self.search_count([
                ('product_id', '=', product_id),
                ('picking_type_id', '=', picking_type['id']),
                ('state', 'not in', ['cancel', 'done', 'draft']),
            ]):
                return {'warning': {
                    'title': _("No %s ready for this product", picking_type['name']),
                }}
            action = self.env['ir.actions.actions']._for_xml_id('stock_barcode.stock_picking_action_kanban')
            action['context'] = dict(self.env.context)
            action['context']['search_default_product_id'] = product_id
            return {'action': action}
        return {'warning': {
            'title': _("No product found for barcode %s", barcode),
            'message': _("Scan a product to filter the transfers."),
        }}
        
class Asstockpicking_lines(models.Model):
    _inherit = "stock.move"
    
    as_product_stock = fields.Float(string="Stock", compute='_detalle_producto', help=u'Stock disponible actual del producto.')

    @api.onchange('product_id')
    def _detalle_producto(self):
        for record in self:
            if record:
                cantidad = 0.0
                if record.location_id and record.product_id:
                    almacen = record.location_id.id
                    producto = record.product_id.id
                    now= datetime.now().strftime('%Y-%m-%d')
                    query_movements = ("""
                        SELECT
                            pp.default_code as "Codigo Producto"
                            ,CONCAT(COALESCE(sp.name, sm.name), ' - ', COALESCE(sp.origin, 'S/Origen')) as "Comprobante"
                            ,COALESCE((sp.date_done AT TIME ZONE 'UTC' AT TIME ZONE 'BOT')::date, sm.date::date) as "Fecha"
                            ,COALESCE(rp.name,'SIN NOMBRE') as "Cliente/Proveedor"
                            ,CASE 
                                WHEN (sm.location_dest_id = """+str(almacen)+""" AND sm.location_id != """+str(almacen)+""") THEN sm.product_qty
                                WHEN (sm.location_id = """+str(almacen)+""" AND sm.location_dest_id != """+str(almacen)+""") THEN -sm.product_qty
                                ELSE 0 END as "Cantidad"
                            ,COALESCE(sm.price_unit, 0) as "Costo"
                        FROM
                            stock_move sm
                            LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
                            LEFT JOIN product_product pp ON pp.id = sm.product_id
                            LEFT JOIN res_partner rp ON rp.id = sp.partner_id
                        WHERE
                            sm.state = 'done'
                            AND (sm.location_id = """+str(almacen)+""" or sm.location_dest_id = """+str(almacen)+""")
                            AND pp.id = """+str(producto)+"""
                            AND (sm.date::TIMESTAMP+ '-4 hr')::date <= '"""+str(now)+"""'
                        ORDER BY COALESCE(sp.date_done, sm.date)  asc
                    """)
                    self.env.cr.execute(query_movements)
                    all_movimientos_almacen = [k for k in self.env.cr.fetchall()]
                    for line in all_movimientos_almacen:
                        cantidad += line[4]






                # cantidad= record.product_id.with_context(location_id=record.location_id).qty_available
                #previsto =  producto.product_id.with_context(location=[ruta]).virtual_available
                record.as_product_stock = cantidad
            else:
                record.as_product_stock = 0.0

class Asstockpicking_lines(models.Model):
    _inherit = "stock.move.line"
    
    as_product_stock = fields.Float(string="Stock", compute='_detalle_producto', help=u'Stock disponible actual del producto.')

    @api.onchange('product_id')
    def _detalle_producto(self):
        for record in self:
            if record:
                cantidad = 0.0
                if record.location_id and record.product_id:
                    almacen = record.location_id.id
                    producto = record.product_id.id
                    filtro = ''
                    if record.product_id.tracking in ('lot','serial') and record.lot_id:
                        filtro+= """AND sm.lot_id = '"""+str(record.lot_id.id)+"""'"""
                    now= datetime.now().strftime('%Y-%m-%d')
                    query_movements = ("""
                        SELECT
                            pp.default_code as "Codigo Producto"
                            ,CASE 
                                WHEN (sm.location_dest_id = """+str(almacen)+""" AND sm.location_id != """+str(almacen)+""") THEN sm.qty_done
                                WHEN (sm.location_id = """+str(almacen)+""" AND sm.location_dest_id != """+str(almacen)+""") THEN -sm.qty_done
                                ELSE 0 END as "Cantidad"
                        FROM
                            stock_move_line sm
                            left join stock_production_lot spl on spl.id = sm.lot_id
                            LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
                            LEFT JOIN product_product pp ON pp.id = sm.product_id
                            LEFT JOIN res_partner rp ON rp.id = sp.partner_id
                        WHERE
                            sm.state = 'done'
                            AND (sm.location_id = """+str(almacen)+""" or sm.location_dest_id = """+str(almacen)+""")
                            AND pp.id = """+str(producto)+"""
                            AND (sm.date::TIMESTAMP+ '-4 hr')::date <= '"""+str(now)+"""'
                            """+filtro+"""
                        ORDER BY COALESCE(sp.date_done, sm.date)  asc
                    """)
                    self.env.cr.execute(query_movements)
                    all_movimientos_almacen = [k for k in self.env.cr.fetchall()]
                    for line in all_movimientos_almacen:
                        cantidad += line[1]






                # cantidad= record.product_id.with_context(location_id=record.location_id).qty_available
                #previsto =  producto.product_id.with_context(location=[ruta]).virtual_available
                record.as_product_stock = cantidad
            else:
                record.as_product_stock = 0.0

class AsStockBarcodeLot(models.TransientModel):
    _inherit = "stock_barcode.lot"
    
    def get_lot_or_create(self, barcode):
        company = self.env.user.company_id
        lot = self.env['stock.production.lot'].search([('name', '=', barcode), ('product_id', '=', self.product_id.id), ('company_id', '=', company)])
        if not lot:
            lot = self.env['stock.production.lot'].create({'name': barcode, 'product_id': self.product_id.id, 'company_id':company})
        return lot