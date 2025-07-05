# -*- coding: utf-8 -*-

import logging
from odoo import models
import datetime

_logger = logging.getLogger(__name__)


class ComisionXlsx(models.AbstractModel):
    _name = 'report.as_sale_pricelist.comision_vendedor_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Reporte XLSX de Comisiones"

    def generate_xlsx_report(self, workbook, data, obj):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        user_ids = data['form']['user_id']
        if not isinstance(user_ids, list):
            user_ids = [user_ids]
            
        # Formato de fecha para mostrar
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        
        # Formato para títulos
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'bg_color': '#D3D3D3',
            'border': 1
        })
        
        # Formato para totales
        total_format = workbook.add_format({
            'bold': True,
            'align': 'right',
            'num_format': '#,##0.00',
            'border': 1
        })
        
        # Formato para montos
        amount_format = workbook.add_format({
            'num_format': '#,##0.00',
            'border': 1
        })
        
        # Formato para texto
        text_format = workbook.add_format({
            'border': 1
        })
        
        # Buscar órdenes
        orders = self.env['sale.order'].search([
            ('date_order', '>=', start_date),
            ('date_order', '<=', end_date),
            ('user_id', 'in', user_ids),
            ('state', 'in', ['sale', 'done'])
        ])
        
        # Crear hoja de trabajo
        sheet = workbook.add_worksheet('Comisiones')
        sheet.set_column('A:A', 20)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 30)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        
        # Títulos
        sheet.write(0, 0, 'Vendedor', header_format)
        sheet.write(0, 1, 'Orden', header_format)
        sheet.write(0, 2, 'Cliente', header_format)
        sheet.write(0, 3, 'Fecha', header_format)
        sheet.write(0, 4, 'Monto', header_format)
        sheet.write(0, 5, 'Comisión', header_format)
        
        # Inicializar variables
        row = 1
        total_comision = 0
        
        # Llenar datos
        for order in orders:
            # Calcular comisión según la tabla
            comision = self._calculate_comision(order.amount_total)
            total_comision += comision
            
            sheet.write(row, 0, order.user_id.name, text_format)
            sheet.write(row, 1, order.name, text_format)
            sheet.write(row, 2, order.partner_id.name, text_format)
            sheet.write(row, 3, order.date_order, date_format)
            sheet.write(row, 4, order.amount_total, amount_format)
            sheet.write(row, 5, comision, amount_format)
            
            row += 1
        
        # Escribir totales
        sheet.write(row, 4, 'Total Comisiones:', total_format)
        sheet.write(row, 5, total_comision, total_format)
    
    def _calculate_comision(self, amount):
        """Calcula la comisión basada en el monto usando la tabla de comisiones."""
        tabla_comisiones = self.env['as.tabla.comisiones'].search([
            ('as_desde', '<=', amount),
            ('as_hasta', '>=', amount)
        ], limit=1)
        
        if not tabla_comisiones:
            return 0
        
        if tabla_comisiones.as_division:
            # Si es cálculo por división
            return amount * tabla_comisiones.as_comision / 100
        else:
            # Si es valor fijo
            return tabla_comisiones.as_comision 