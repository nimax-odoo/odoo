# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models

class as_kardex_productos_wiz(models.TransientModel):
    _name="as.kardex.productos.wiz"
    _description = "Warehouse Reports by AhoraSoft"
    
    start_date = fields.Date('Desde la Fecha', default=fields.Date.context_today)
    end_date = fields.Date('Hasta la Fecha', default=fields.Date.context_today)
    as_almacen = fields.Many2many('stock.location', string="Almacen", domain="[('usage', '=', 'internal')]")
    as_productos = fields.Many2many('product.product', string="Productos")
    as_consolidado = fields.Boolean(string="Consolidado", default=False)
    as_categ_levels = fields.Integer(string="Niveles de categorias", help=u"Debe ser un entero igual o mayor a 1", default=2)
    as_reporte_existencias = fields.Boolean(string="Reporte existencias", default=False)
    as_reporte_diferencias = fields.Boolean(string="Reporte Diferencias", default=False)
    as_UFV = fields.Boolean(string="Mostrar Monto de Ajuste UFV", default=False)
    as_include_qty = fields.Boolean(string="Incluir saldo cero", default=False)
    as_saldo_inicial = fields.Boolean(string="Excluir Saldo Inicial", default=False)
    # as_brand_id = fields.Many2many('as.product.brand', string="Marca")


    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'as.kardex.productos.wiz'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        if context.get('xls_export'):
            return self.env.ref('as_stock.kardex_productos_xlsx').report_action(self, data=datas)