# -*- coding: utf-8 -*-
from odoo import fields, models
import base64
import openpyxl
from io import BytesIO


class StockMove(models.Model):
    """ Inheriting stock_move to add additional new field and function """
    _inherit = 'stock.move'

    attachment = fields.Binary(string="Upload")

    def action_import_lot(self):
        """ Import and write lots to stock_move_line """
        vals_list = []
        wb = openpyxl.load_workbook(
            filename=BytesIO(base64.b64decode(self.attachment)),
            read_only=True)
        ws = wb.active
        for record in ws.iter_rows(min_row=2, max_row=None,
                                   min_col=None,
                                   max_col=None, values_only=True):
            if record[1] == self.product_id.display_name:
                vals_list.append((0, 0, {
                    'lot_name': record[0],
                    'quantity': record[2],
                    'product_id': self.product_id.id
                }))
            continue
        self.move_line_ids.unlink()
        self.write({
            'move_line_ids': vals_list
        })
