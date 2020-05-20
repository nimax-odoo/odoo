# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models

class as_kardex_productos_wiz(models.TransientModel):
    _name="as.comisiones"
    _description = "Warehouse Reports by AhoraSoft"
    
    start_date = fields.Date('Desde la Fecha', default=fields.Date.context_today)
    end_date = fields.Date('Hasta la Fecha', default=fields.Date.context_today)
    user_id = fields.Many2many('res.users', string='Vendedor')
   
    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'as.comisiones'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        if context.get('xls_export'):
            return self.env.ref('as_sale_pricelist.comision_vendedor_xlsx').report_action(self, data=datas)