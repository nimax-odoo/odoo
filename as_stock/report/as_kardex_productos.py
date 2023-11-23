# # -*- coding: utf-8 -*-

import datetime
from datetime import datetime
import pytz
from odoo import models,fields
from datetime import datetime, timedelta
from time import mktime
# from as_reporte_existencias import generate_xlsx_report2
import logging
_logger = logging.getLogger(__name__)

class as_kardex_productos_excel(models.AbstractModel):
    _name = 'report.as_stock.kardex_productos_report_xls.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):       
        dict_almacen = []
        dict_aux = []
        if data['form']['as_almacen']:
            for line in data['form']['as_almacen']:
                dict_almacen.append('('+str(line)+')')
                dict_aux.append(line)
        else:
            almacenes_internos = self.env['stock.location'].search([('usage', '=', 'internal')])
            for line in almacenes_internos:
                dict_almacen.append('('+str(line.id)+')')
                dict_aux.append(line.id)
        
        if data['form']['as_consolidado']:
            dict_almacen = []
            dict_almacen.append(str(dict_aux).replace('[','(').replace(']',')'))

        dict_productos = []
        if data['form']['as_productos']:
            for line in data['form']['as_productos']:
                dict_productos.append(line)
        if dict_productos:
            filtro_productos = "AND sm.product_id in "+str(dict_productos).replace('[','(').replace(']',')')
        else:
            filtro_productos = ''
        dict_marca = []
        valor = self.env.user.company_id.currency_id.rounding
        #Definiciones generales del archivo, formatos, titulos, hojas de trabajo
        sheet = workbook.add_worksheet('Detalle de Movimientos')
        titulo1 = workbook.add_format({'font_size': 16, 'align': 'center', 'text_wrap': True, 'bold':True })
        titulo2 = workbook.add_format({'font_size': 14, 'align': 'center', 'text_wrap': True, 'bottom': True, 'top': True, 'bold':True })
        titulo3 = workbook.add_format({'font_size': 12, 'align': 'left', 'text_wrap': True, 'bottom': True, 'top': True, 'bold':True })
        titulo3_number = workbook.add_format({'font_size': 14, 'align': 'right', 'text_wrap': True, 'bottom': True, 'top': True, 'bold':True, 'num_format': '#,##0.00' })
        titulo4 = workbook.add_format({'font_size': 14, 'align': 'center', 'text_wrap': True, 'bottom': True, 'top': True, 'left': True, 'right': True, 'bold':True })

        number_left = workbook.add_format({'font_size': 12, 'align': 'left', 'num_format': '#,##0.00'})
        number_right = workbook.add_format({'font_size': 12, 'align': 'right', 'num_format': '#,##0.00'})
        number_right_bold = workbook.add_format({'font_size': 12, 'align': 'right', 'num_format': '#,##0.00', 'bold':True})
        number_right_col = workbook.add_format({'font_size': 12, 'align': 'right', 'num_format': '#,##0.00','bg_color': 'silver'})
        number_center = workbook.add_format({'font_size': 12, 'align': 'center', 'num_format': '#,##0.00'})
        number_right_col.set_locked(False)

        letter1 = workbook.add_format({'font_size': 12, 'align': 'left', 'text_wrap': True})
        letter2 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold':True})
        letter3 = workbook.add_format({'font_size': 12, 'align': 'right', 'text_wrap': True})
        letter4 = workbook.add_format({'font_size': 12, 'align': 'left', 'text_wrap': True, 'bold': True})
        letter5 = workbook.add_format({'font_size': 12, 'align': 'right', 'text_wrap': True, 'bold': True})
        letter_locked = letter3
        letter_locked.set_locked(False)

        # Aqui definimos en los anchos de columna
        sheet.set_column('A:A',15, letter1)
        sheet.set_column('B:B',30, letter1)
        sheet.set_column('C:C',15, letter1)
        sheet.set_column('D:D',18, letter1)
        sheet.set_column('E:E',15, letter1)
        sheet.set_column('F:F',15, letter1)
        sheet.set_column('G:G',15, letter1)
        sheet.set_column('H:H',15, letter1)
        sheet.set_column('I:I',15, letter1)
        sheet.set_column('J:J',15, letter1)
        sheet.set_column('L:L',15, letter1)
        

        # Titulos, subtitulos, filtros y campos del reporte
        sheet.merge_range('A1:K1', 'KARDEX DE PRODUCTOS V3', titulo1)
        fecha = (datetime.now() - timedelta(hours=4)).strftime('%d/%m/%Y %H:%M:%S')
        fecha_inicial = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        fecha_inicial2 = datetime.strptime(data['form']['start_date'], '%Y-%m-%d')
        fecha_final = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        sheet.write(1, 0, 'Rango de Fechas: ', letter4)
        sheet.merge_range('B2:D2', fecha_inicial +' - '+ fecha_final)
        sheet.write(2, 0, 'Almacen: ', letter4)
        filtro_almacenes_name = 'VARIOS'
        for y in dict_aux:
            almacen_obj = self.env['stock.location'].search([('id', '=', y)], limit=1)
            filtro_almacenes_name += ', '+almacen_obj.name
        if len(dict_aux)==1 and not data['form']['as_consolidado']:
            filtro_almacenes_name = self.env['stock.location'].search([('id', '=', dict_aux[0])], limit=1).name
        sheet.merge_range('B3:D3', filtro_almacenes_name)
        sheet.merge_range('H3:I3', 'Fecha impresion: ', letter5)
        sheet.merge_range('J3:K3', fecha)

        sheet.merge_range('A4:A5', 'Codigo Producto', titulo4)
        sheet.merge_range('B4:B5', 'Comprobante', titulo4)
        sheet.merge_range('C4:C5', 'Fecha', titulo4)
        sheet.merge_range('D4:D5', 'Cliente / Proveedor', titulo4)
        sheet.merge_range('E4:G4', 'Inventario Fisico', titulo4)
        sheet.write(4, 4, 'Entrada', titulo2)
        sheet.write(4, 5, 'Salida', titulo2)
        sheet.write(4, 6, 'Saldo', titulo2)
        sheet.merge_range('H4:L4', 'Inventario Valorado - Costo', titulo4)
        sheet.write(4, 7, 'C/U', titulo2)
        sheet.write(4, 8, 'Entrada', titulo2)
        sheet.write(4, 9, 'Salida', titulo2)
        sheet.write(4, 10, 'Ajuste UFV', titulo2)
        sheet.write(4, 11, 'Saldo', titulo2)
        sheet.freeze_panes(5, 0)
        mostrar = True
        if data['form']['as_UFV']:
            mostrar= False
        sheet.set_column('K:K',15, letter1, {'hidden': mostrar})
        filas = 4
        totales_almacen = {}
        totales_almacen_ingresos = {}
        totales_almacen_salidas = {}
        totales_almacen_ajuste = {}

        for almacen in dict_almacen:
            filas += 1
            totales_almacen[almacen] = filas
            if almacen not in totales_almacen_ingresos: totales_almacen_ingresos[almacen] = 0
            if almacen not in totales_almacen_salidas: totales_almacen_salidas[almacen] = 0
            if data['form']['as_consolidado']:
                sheet.merge_range('A'+str(filas+1)+':D'+str(filas+1), 'CONSOLIDADO', titulo2)
            else:
                id_almacen = int(str(almacen).replace('(','').replace(')',''))
                almacen_obj = self.env['stock.location'].search([('id', '=', id_almacen)], limit=1)
                sheet.merge_range('A'+str(filas+1)+':D'+str(filas+1), almacen_obj.name, titulo2)
            join_categ = ' LEFT JOIN product_category pc1 ON pc1.id = pt.categ_id '
            result_categ = ",COALESCE(pc1.name, 'No asignado') "
            order_by = ' ORDER BY 3'
            level_names = {}

            for i in range(data['form']['as_categ_levels']):
                pc_number = i+1
                order_number = i+3
                level_names[i+2] = ''
                if pc_number > 1:
                    join_categ += ' LEFT JOIN product_category pc'+str(pc_number)+' ON pc'+str(pc_number)+'.id = pc'+str(pc_number-1)+'.parent_id '
                    tmp_str = " ,COALESCE(pc"+str(pc_number)+".name, 'No asignado') "
                    result_categ = tmp_str + result_categ
                if order_number > 3:
                    order_by += ' , '+str(order_number)            

            query_ids = ("""
                SELECT
                    pp.id as "ID"
                    ,CONCAT(pp.default_code, ' - ', pt.name) as "Codigo Producto"
                    """+result_categ+"""
                    ,pu.name    
                FROM
                    product_product pp
                    INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
                    INNER JOIN uom_uom pu ON pu.id = pt.uom_id
                    """+join_categ+"""
                WHERE
                    pp.id in                    
                    (SELECT
                        sm.product_id
                    FROM
                        stock_move sm
                        LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
                    WHERE
                        sm.state = 'done'
                        AND (sm.location_id IN """+str(almacen)+"""
                        OR sm.location_dest_id IN """+str(almacen)+""")
                        """+filtro_productos+"""
                        AND (sm.date::TIMESTAMP+ '-4 hr')::date <= '"""+str(data['form']['end_date'])+"""'
                    GROUP BY 1)
                """+order_by+"""
            """)
            
            _logger.debug("\n\n Query 3 KARDEX %s\n\n",query_ids)

            self.env.cr.execute(query_ids)

            product_categories = [j for j in self.env.cr.fetchall()]

            filas_totales_categ = {}
            total_ingresos_val = {}
            total_salidas_val = {}
            total_juste = {}
            ultimo_costo=0

            for producto in product_categories:
                total_producto=0.0
                query_movements = ("""
                    SELECT
                        pp.default_code as "Codigo Producto"
                        ,CONCAT(COALESCE(sp.name, sm.name), ' - ', COALESCE(sp.origin, 'S/Origen')) as "Comprobante"
                        ,COALESCE((sp.date_done AT TIME ZONE 'UTC' AT TIME ZONE 'BOT')::date, sm.date::date) as "Fecha"
                        ,COALESCE(rp.name,'SIN NOMBRE') as "Cliente/Proveedor"
                        ,CASE 
                            WHEN (sm.location_dest_id IN """+str(almacen)+""" AND sm.location_id NOT IN """+str(almacen)+""") THEN sm.product_qty
                            WHEN (sm.location_id IN """+str(almacen)+""" AND sm.location_dest_id NOT IN """+str(almacen)+""") THEN -sm.product_qty
                            ELSE 0 END as "Cantidad"
                        ,COALESCE(sm.price_unit, 0) as "Costo"
                        ,0.0 
                        ,0.0
                    FROM
                        stock_move sm
                        LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
                        LEFT JOIN product_product pp ON pp.id = sm.product_id
                        LEFT JOIN res_partner rp ON rp.id = sp.partner_id
                    WHERE
                        sm.state = 'done'
                        AND (sm.location_id IN """+str(almacen)+""" or sm.location_dest_id IN """+str(almacen)+""")
                        AND pp.id = """+str(producto[0])+"""
                        AND COALESCE((sp.date_done AT TIME ZONE 
                        'UTC' AT TIME ZONE 'BOT')::date, sm.date::date) <= '"""+str(data['form']['end_date'])+"""'
                    ORDER BY COALESCE(sp.date_done, sm.date)  asc
                """)
                _logger.debug("\n\n Query 1 KARDEX %s\n\n",query_movements)
                
                self.env.cr.execute(query_movements)
                all_movimientos_almacen = [k for k in self.env.cr.fetchall()]
                movimientos_almacen = []
                # en el saldo inicial almacenaremos el total ingresos, salidas, saldos, valorados y costo ponderado
                saldo_inicial = {
                    'producto' : '',
                    'ingresos' : 0,
                    'salidas'  : 0,
                    'saldo'    : 0,
                    'costo'    : 0,
                    'ingresos_val' : 0,
                    'salidas_val' : 0,
                    'saldo_val'   : 0,
                    'saldo_ufv':0,
                }
                aux1 = 0.0
                for line in all_movimientos_almacen:
                    if data['form']['as_saldo_inicial']:
                        saldo_inicial['producto'] = all_movimientos_almacen[0][0]
                        ultimo_costo = (line[5]*-1)
                        fechat = datetime.strptime(str(line[2]), '%Y-%m-%d')
                        if fechat >= fecha_inicial2:
                            movimientos_almacen.append(line)
                    else:
                        saldo_inicial['producto'] = all_movimientos_almacen[0][0]
                        ultimo_costo = (line[5]*-1)
                        fechat = datetime.strptime(str(line[2]), '%Y-%m-%d')
                        if fechat < fecha_inicial2:
                            if line[7] != None:
                                saldo_inicial['saldo_ufv'] += (line[7])
                            if line[4]>0:
                                saldo_inicial['ingresos'] += abs(line[4])
                                saldo_inicial['ingresos_val'] += abs(line[4]*line[5])
                            elif line[4]<0:
                                saldo_inicial['salidas'] += abs(line[4])
                                
                                saldo_inicial['salidas_val'] += abs(line[4]*line[5])
                        elif fechat >= fecha_inicial2:
                            movimientos_almacen.append(line)

                saldo_inicial['saldo'] = saldo_inicial['ingresos']-saldo_inicial['salidas']
                saldo_inicial['saldo_val'] = saldo_inicial['ingresos_val']-saldo_inicial['salidas_val']
                saldo_inicial['costo'] = abs(saldo_inicial['saldo_val']/saldo_inicial['saldo'] if saldo_inicial['saldo'] != 0 else ultimo_costo)
                if data['form']['as_saldo_inicial']:
                    result = movimientos_almacen
                else:
                    result = movimientos_almacen or saldo_inicial

                #si encontramos movimientos pasamos a la impresion
                if result:
                    blanco = ''
                    posicion = ''
                    for x in range(data['form']['as_categ_levels']):
                        level = x+2
                        if level>2: blanco += '      '
                        posicion += producto[level]+','
                        if producto[level] != level_names[level]:
                            filas += 1
                            filas_totales_categ[posicion] = filas
                            sheet.set_row(filas, None, None, {'level': level-1})
                            sheet.merge_range('A'+str(filas+1)+':D'+str(filas+1), blanco + producto[level], letter2)
                            level_names[level] = producto[level]

                    filas += 1
                    producto_obj = self.env['product.product'].search([('id', '=', producto[0])], limit=1)
                    if producto_obj.product_tmpl_id.name: 
                        name = str(producto[1]) +' - '+ producto_obj.product_tmpl_id.name
                    else:
                        name = producto[1]
                    sheet.merge_range('A'+str(filas+1)+':D'+str(filas+1), name, letter2)
                    sheet.set_row(filas, None, None, {'level': data['form']['as_categ_levels']+1})
                    fila_totales = filas #guardamops la fila donde debemos mostrar el resumen por producto o movimientos totales
                    bandera = True #esta bandera la usaremos para ver si es la primera linea escrita y variar el calculo de saldos
                    # IMPRESION DE SALDO INICIAL_____________________________________________________
                    saldo_UFV = 0.0
                    sumas = 0.0
                    if saldo_inicial['saldo']!=0 or saldo_inicial['ingresos']!=0 or saldo_inicial['salidas']!=0:
                        filas += 1
                        sheet.write(filas, 0, saldo_inicial['producto']) #codigo producto
                        sheet.write(filas, 1, 'SALDO INICIAL') #comprobante
                        sheet.write(filas, 2, fecha_inicial) #fecha
                        sheet.write(filas, 3, '') #cliente/proveedor
                        sheet.write(filas, 4, saldo_inicial['ingresos'], number_right)
                        sheet.write(filas, 5, saldo_inicial['salidas'], number_right)
                        sheet.write(filas, 6, saldo_inicial['saldo'], number_right)
                        sheet.write(filas, 7, saldo_inicial['costo'], number_right)
                        sheet.write(filas, 8, saldo_inicial['ingresos_val'], number_right)
                        sheet.write(filas, 9, saldo_inicial['salidas_val'], number_right)

                        
                        aux2 = 0.0
                        aux3 = 0.0
                        for stock_move1 in all_movimientos_almacen:
                        #if stock_move1[6]==True:
                            #res = self.get_saldo_entrada(producto[0],almacen,str(data['form']['end_date']))
                            if stock_move1[7] != None:
                                saldo_UFV = float(stock_move1[7])
                                # aux2 = saldo_UFV
                                
                                # aux2 = aux1 - saldo_UFV
                                # aux1 += saldo_UFV
                                # # aux3 = aux1 - saldo_UFV
                                # if saldo_UFV <= aux1:
                                #     aux2 = aux1 - saldo_UFV
                                # else:
                                #     aux2 = saldo_UFV
                                aux2 = aux1
                                sumas = saldo_inicial['saldo_ufv'] + saldo_inicial['saldo_val']
                                    
                        sheet.write(filas, 10, saldo_inicial['saldo_ufv'], number_right)
                        sheet.write(filas, 11, sumas, number_right)

                        posicion = ''
                            
                        for x in range(data['form']['as_categ_levels']):
                            level = x+2
                            posicion += producto[level]+','
                            if posicion in total_juste:
                                total_juste[posicion] += saldo_inicial['saldo_ufv'] #
                                
                            else:
                                total_juste[posicion] = 0
                                total_juste[posicion] += saldo_inicial['saldo_ufv'] #+ 1000

                        if almacen in totales_almacen_ajuste:
                            totales_almacen_ajuste[almacen] += saldo_inicial['saldo_ufv'] 
                        else:
                            totales_almacen_ajuste[almacen] = 0
                            totales_almacen_ajuste[almacen] += saldo_inicial['saldo_ufv'] 
                                

                        #if not movimientos_almacen:
                        #    continue
                            
                            
                            # posicion = ''
                            
                            # for x in range(data['form']['as_categ_levels']):
                            #     level = x+2
                            #     posicion += producto[level]+','
                            #     if posicion in total_juste:
                            #         total_juste[posicion] += saldo_UFV #
                                    
                            #     else:
                            #         total_juste[posicion] = 0
                            #         total_juste[posicion] += saldo_UFV #+ 1000
                                    
                                

                            # if almacen in totales_almacen_ajuste:
                            #     totales_almacen_ajuste[almacen] += saldo_UFV
                            # else:
                            #     totales_almacen_ajuste[almacen] = 0
                            #     totales_almacen_ajuste[almacen] += saldo_UFV


                        #else: 
                        # sheet.write(filas, 11, saldo_inicial['saldo_val'], number_right)
                        # sheet.set_row(filas, None, None, {'level': data['form']['as_categ_levels']+2})

                        # if stock_move[6]==True:
                        #     res = self.get_saldo_entrada(producto[0],almacen,str(data['form']['end_date']))
                        #     if float(res['diff']) > valor:
                        #         saldo_UFV = res['diff']

                        # if stock_move[6]==True:
                        #     res = self.get_saldo_entrada(producto[0],almacen,str(data['form']['end_date']))
                        #     if float(res['diff']) > valor:
                        #         saldo_UFV = res['diff']
                        # TOTALES POR CATEGORIA
                        posicion = ''
                        for x in range(data['form']['as_categ_levels']):
                            level = x+2
                            posicion += producto[level]+','
                            # totales de ingresos valorados
                            if posicion in total_ingresos_val:
                                total_ingresos_val[posicion] += saldo_inicial['ingresos_val']
                            else:
                                total_ingresos_val[posicion] = 0
                                total_ingresos_val[posicion] += saldo_inicial['ingresos_val']
                            # totales de egresos valorados
                            if posicion in total_salidas_val:
                                total_salidas_val[posicion] += saldo_inicial['salidas_val']
                            else:
                                total_salidas_val[posicion] = 0
                                total_salidas_val[posicion] += saldo_inicial['salidas_val']
                        
                        # TOTALES POR ALMACEN
                        if almacen in totales_almacen_ingresos:
                            totales_almacen_ingresos[almacen] += saldo_inicial['ingresos_val']
                        else:
                            totales_almacen_ingresos[almacen] = 0
                            totales_almacen_ingresos[almacen] += saldo_inicial['ingresos_val']
                        if almacen in totales_almacen_salidas:
                            totales_almacen_salidas[almacen] += saldo_inicial['salidas_val']
                        else:
                            totales_almacen_salidas[almacen] = 0
                            totales_almacen_salidas[almacen] += saldo_inicial['salidas_val']

                    else:
                        bandera = False
                        # TOTALES POR CATEGORIA
                        posicion = ''
                        for x in range(data['form']['as_categ_levels']):
                            level = x+2
                            posicion += producto[level]+','
                            # totales de ingresos valorados
                            if posicion in total_ingresos_val:
                                total_ingresos_val[posicion] += saldo_inicial['ingresos_val']
                            else:
                                total_ingresos_val[posicion] = 0
                                total_ingresos_val[posicion] += saldo_inicial['ingresos_val']
                            # totales de egresos valorados
                            if posicion in total_salidas_val:
                                total_salidas_val[posicion] += saldo_inicial['salidas_val']
                            else:
                                total_salidas_val[posicion] = 0
                                total_salidas_val[posicion] += saldo_inicial['salidas_val']

                    # IMPRESION DE MOVIMIENTOS EN RANGO DE FECHAS____________________________________
                    for stock_move in movimientos_almacen:
                        saldo_UFV = 0.0
                        filas += 1
                        sheet.write(filas, 0, stock_move[0])
                        sheet.write(filas, 1, stock_move[1])
                        fecha_movimiento = stock_move[2].strftime('%d/%m/%Y')
                        sheet.write(filas, 2, fecha_movimiento)
                        sheet.write(filas, 3, stock_move[3])

                        # en la posicion 4 guardamos la cantidad, si es negativa se trata de una salida, positiva ingreso
                        if stock_move[4]>0:
                            sheet.write(filas, 4, abs(stock_move[4]), number_right)
                        else:
                            sheet.write(filas, 5, abs(stock_move[4]), number_right)
                        
                        #Colocamos los saldos segun datos del reporte
                        if bandera:
                            sheet.write(filas, 6, '=E'+str(filas+1)+'-F'+str(filas+1)+'+G'+str(filas), number_right)
                        else:
                            sheet.write(filas, 6, '=E'+str(filas+1)+'-F'+str(filas+1), number_right)
                            # bandera = True
                        
                        # Precio unitario (costo) por cada transferencia
                        sheet.write(filas, 7, abs(stock_move[5]), number_right)

                        #valorados
                        sheet.write(filas, 8, '=H'+str(filas+1)+'*E'+str(filas+1), number_right)
                        sheet.write(filas, 9, '=H'+str(filas+1)+'*F'+str(filas+1), number_right)
                        #agregado difrenecia UFV
                        
                        aux1 = 0.0
                        aux2 = 0.0
                        # if stock_move[6]==True:
                            #res = self.get_saldo_entrada(producto[0],almacen,str(data['form']['end_date']))
                        if stock_move[7] != None:
                            

                            saldo_UFV = float(stock_move[7])
                            # aux1 += saldo_UFV
                            # if aux1 == saldo_UFV and saldo_UFV > 0:
                            #     aux2 = saldo_UFV
                            # else:
                            #     aux2 = aux1 - saldo_UFV
                            
                                
                        sheet.write(filas, 10, saldo_UFV, number_right)

                        # sheet.write(filas, 10, '=H'+str(filas+1)+'*G'+str(filas+1), number_right)

                        #Colocamos los saldos valorados segun datos del reporte                        
                        if bandera:
                            sheet.write(filas, 11, '=I'+str(filas+1)+'-J'+str(filas+1)+'+L'+str(filas)+'+K'+str(filas+1), number_right)
                        else:
                            sheet.write(filas, 11, '=I'+str(filas+1)+'-J'+str(filas+1), number_right)
                            bandera = True

                        sheet.set_row(filas, None, None, {'level': data['form']['as_categ_levels']+2})
                        
                        # TOTALES POR CATEGORIA
                        posicion = ''
                        for x in range(data['form']['as_categ_levels']):
                            level = x+2
                            posicion += producto[level]+','
                            # totales de ingresos valorados
                            if posicion in total_ingresos_val:
                                if stock_move[4]>0:
                                    total_ingresos_val[posicion] += stock_move[5]*abs(stock_move[4])
                            else:
                                total_ingresos_val[posicion] = 0
                                if stock_move[4]>0:
                                    total_ingresos_val[posicion] += stock_move[5]*abs(stock_move[4])
                            # totales de egresos valorados
                            if posicion in total_salidas_val:
                                if stock_move[4]<0:
                                    total_salidas_val[posicion] += stock_move[5]*abs(stock_move[4])
                            else:
                                total_salidas_val[posicion] = 0
                                if stock_move[4]<0:
                                    total_salidas_val[posicion] += stock_move[5]*abs(stock_move[4])
                            # totales de ajuste valorados
                            if posicion in total_juste:
                                total_juste[posicion] += saldo_UFV
                            else:
                                total_juste[posicion] = 0
                                total_juste[posicion] += saldo_UFV
                        
                        # TOTALES POR ALMACEN
                        if almacen in totales_almacen_ingresos:
                            totales_almacen_ingresos[almacen] += stock_move[5]*abs(stock_move[4]) if stock_move[4]>0 else 0
                        else:
                            totales_almacen_ingresos[almacen] = 0
                            totales_almacen_ingresos[almacen] += stock_move[5]*abs(stock_move[4]) if stock_move[4]>0 else 0
                        if almacen in totales_almacen_salidas:
                            totales_almacen_salidas[almacen] += stock_move[5]*abs(stock_move[4]) if stock_move[4]<0 else 0
                        else:
                            totales_almacen_salidas[almacen] = 0
                            totales_almacen_salidas[almacen] += stock_move[5]*abs(stock_move[4]) if stock_move[4]<0 else 0
                        if almacen in totales_almacen_ajuste:
                            totales_almacen_ajuste[almacen] += saldo_UFV
                        else:
                            totales_almacen_ajuste[almacen] = 0
                            totales_almacen_ajuste[almacen] += saldo_UFV
                    # TOTALES POR PRODUCTO
                    sheet.write(fila_totales, 4, '=SUM(E'+str(fila_totales+2)+':E'+str(filas+1)+')',number_right_bold) #INGRESO
                    sheet.write(fila_totales, 5, '=SUM(F'+str(fila_totales+2)+':F'+str(filas+1)+')',number_right_bold) #SALIDA
                    sheet.write(fila_totales, 6, '=E'+str(fila_totales+1)+'-F'+str(fila_totales+1),number_right_bold) #SALDO

                    sheet.write(fila_totales, 7, '=IF(G'+str(fila_totales+1)+'<>0, L'+str(fila_totales+1)+'/G'+str(fila_totales+1)+', H'+str(filas+1)+')',number_right_bold) #COSTO PROMEDIO

                    sheet.write(fila_totales, 8, '=SUM(I'+str(fila_totales+2)+':I'+str(filas+1)+')',number_right_bold) #VALORADO INGRESO
                    sheet.write(fila_totales, 9, '=SUM(J'+str(fila_totales+2)+':J'+str(filas+1)+')',number_right_bold) #VALORADO SALIDA
                    sheet.write(fila_totales, 10, '=SUM(K'+str(fila_totales+2)+':K'+str(filas+1)+')',number_right_bold) #VALORADO SALIDA
                    sheet.write(fila_totales, 11, '=I'+str(fila_totales+1)+'-J'+str(fila_totales+1)+'+K'+str(fila_totales+1),number_right_bold) #SALDO
                    # sheet.write(fila_totales, 10, '=SUM(K'+str(fila_totales+2)+':K'+str(filas+1)+')',number_right_bold) #VALORADO SALDO
                    # if data['form']['as_UFV']:
                    #     filas += 1
                    #     res = self.get_saldo_entrada(producto[0],almacen,str(data['form']['end_date']))
                    #     sheet.merge_range('A'+str(filas+1)+':B'+str(filas+1), 'ACTUALIZACION', letter2)
                    #     sheet.write(filas, 2, res['fecha'])
                    #     sheet.write(filas, 4, 0, number_right_bold)
                    #     sheet.write(filas, 5, 0, number_right_bold)
                    #     sheet.write(filas, 6, res['stock'], number_right_bold)
                    #     sheet.write(filas, 7, res['PU'], number_right_bold)
                    #     sheet.write(filas, 10, res['total'], number_right_bold)
                    #     filas += 1
                    #     sheet.merge_range('A'+str(filas+1)+':B'+str(filas+1), 'DIFERENCIA', letter2)
                    #     sheet.write(filas, 2, res['fecha'])
                    #     sheet.write(filas, 4, 0, number_right_bold)
                    #     sheet.write(filas, 5, 0, number_right_bold)
                    #     sheet.write(filas, 6, 0, number_right_bold)
                    #     sheet.write(filas, 7, 0, number_right_bold)
                    #     sheet.write(filas, 10, res['diff'], number_right_bold)

            for fila in filas_totales_categ:
                if fila in total_juste:
                    total_ajuste = total_juste[fila]
                else:
                    total_ajuste = 0.0
                sheet.write(filas_totales_categ[fila], 8, total_ingresos_val[fila], number_right_bold)
                sheet.write(filas_totales_categ[fila], 9, total_salidas_val[fila], number_right_bold)
                sheet.write(filas_totales_categ[fila], 10, total_ajuste, number_right_bold)
                sheet.write(filas_totales_categ[fila], 11, '=I'+str(filas_totales_categ[fila]+1)+'-J'+str(filas_totales_categ[fila]+1)+'+K'+str(filas_totales_categ[fila]+1), number_right_bold)
        
        for fila1 in totales_almacen:
            if fila1 in totales_almacen_ajuste:
                total_ajuste_almacen = totales_almacen_ajuste[fila1]
            else:
                total_ajuste_almacen = 0.0
            sheet.write(totales_almacen[fila1], 8, totales_almacen_ingresos[fila1], number_right_bold)
            sheet.write(totales_almacen[fila1], 9, totales_almacen_salidas[fila1], number_right_bold)
            sheet.write(totales_almacen[fila1], 10, total_ajuste_almacen, number_right_bold)
            sheet.write(totales_almacen[fila1], 11, '=I'+str(totales_almacen[fila1]+1)+'-J'+str(totales_almacen[fila1]+1)+'+K'+str(totales_almacen[fila1]+1), number_right_bold)

    def get_saldo_entrada(self,product,almacen,fecha):
        year = (datetime.strptime(str(fecha), '%Y-%m-%d')).strftime('%Y')
        ultimo_dia_year = year+'-'+'12'+'-'+'31'
        #tomamos 
        query_movements = ("""
            SELECT
                pp.default_code as "Codigo Producto"
                ,CONCAT(COALESCE(sp.name, sm.name), ' - ', COALESCE(sp.origin, 'S/Origen')) as "Comprobante"
                ,COALESCE(sp.date_done::date, sm.date::date) as "Fecha"
                ,COALESCE(rp.name,'SIN NOMBRE') as "Cliente/Proveedor"
                ,CASE 
                    WHEN (sm.location_dest_id IN """+str(almacen)+""" AND sm.location_id NOT IN """+str(almacen)+""") THEN sm.product_qty
                    WHEN (sm.location_id IN """+str(almacen)+""" AND sm.location_dest_id NOT IN """+str(almacen)+""") THEN -sm.product_qty
                    ELSE 0 END as "Cantidad"
                ,COALESCE(sm.price_unit, 0) as "Costo"
            FROM
                stock_move sm
                LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
                LEFT JOIN product_product pp ON pp.id = sm.product_id
                LEFT JOIN res_partner rp ON rp.id = sp.partner_id
            WHERE
                sp.as_ufv = 'True' AND
                sm.state = 'done'
                AND (sm.location_id IN """+str(almacen)+""" or sm.location_dest_id IN """+str(almacen)+""")
                AND pp.id = """+str(product)+"""
                AND (sm.date::TIMESTAMP+ '-4 hr')::date <= '"""+str(fecha)+"""'
            ORDER BY COALESCE(sp.date_done::date, sm.date::date)  asc
        """)
        _logger.debug("\n\n Query 2 KARDEX %s\n\n",query_movements)
        
        self.env.cr.execute(query_movements)
        ultimo_monto = [k for k in self.env.cr.fetchall()]
        total= 0.0
        stock= 0.0
        bandera = False
        fecha_ininial = ''
        fecha_ultimo = ''
        for stock_move in ultimo_monto:
            fecha_ultimo = stock_move[2]
            total_ingreso = 0.0
            total_egreso= 0.0
            stock_ingreso = 0.0
            stock_egreso= 0.0
            if stock_move[4]>0:
                fecha_ininial = stock_move[2]
                total_ingreso = stock_move[5]*abs(stock_move[4])
                stock_ingreso = abs(stock_move[4])
            if stock_move[4]<0:
                total_egreso = stock_move[5]*abs(stock_move[4])
                stock_egreso = abs(stock_move[4])
            if bandera:
                total= total_ingreso - total_egreso + total
                stock= stock_ingreso - stock_egreso + stock
            else:
                total = total_ingreso - total_egreso
                stock= stock_ingreso - stock_egreso 
                bandera = True
        if fecha_ininial=='':
            fecha_ininial = ultimo_dia_year
        ufv_inicial = float(self.get_rate_ufv_start(fecha_ininial))
        ufv_final = float(self.get_rate_ufv_end(ultimo_dia_year))
        monto_actualizacon = total*(ufv_final/ufv_inicial)
        if stock > 0:
            precio_costo = monto_actualizacon / stock
        else:
            precio_costo = 0
        diferencia =monto_actualizacon-total
        vals = {
            'fecha': (datetime.strptime(str(ultimo_dia_year), '%Y-%m-%d')).strftime('%d/%m/%Y'),
            'PU': precio_costo,
            'stock': stock,
            'total': monto_actualizacon,
            'diff': diferencia,
        }
        return vals
    
    def get_rate_ufv_end(self,fecha):
        ufv = self.env['res.currency'].search([('name', '=', 'UFV')],limit=1)
        as_ufv_actual = self.env['res.currency.rate'].search([('name', '<=', fecha),('currency_id', '=', ufv.id)], order="name desc", limit=1).rate or 1
        return as_ufv_actual

    def get_rate_ufv_start(self,fecha):
        ufv = self.env['res.currency'].search([('name', '=', 'UFV')],limit=1)
        as_ufv_ant = self.env['res.currency.rate'].search([('name', '=', fecha),('currency_id', '=', ufv.id)], order="name desc",limit=1).rate or 1
        return as_ufv_ant





                    
