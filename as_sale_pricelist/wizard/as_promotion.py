# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, time
from odoo.tools.safe_eval import safe_eval
from datetime import date, datetime, time
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError

#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class asSaleOrderPromoWizard(models.TransientModel):
    _name = 'as.sale.order.promo.wizard'
    _description = 'Promo Wizard'

    promo_line = fields.One2many('as.sale.order.promo.wizard.line', 'promo_id', string='PromoLine Id')

    @api.model
    def default_get(self, fields):
        res = super(asSaleOrderPromoWizard, self).default_get(fields)
        res_ids = self._context.get('active_ids')
        if res_ids[0]:
            so_line = res_ids[0]
            so_line_obj = self.env['sale.order.line'].browse(so_line)
            promo_list = []

            # Log para la depuración
            log_msg = []
            log_msg.append("==== FILTROS DE BÚSQUEDA DE PROMOCIONES ====")
            log_msg.append(f"Línea: {so_line_obj.name} (ID: {so_line_obj.id})")
            log_msg.append(f"Producto: {so_line_obj.product_id.name} (ID: {so_line_obj.product_id.id})")
            log_msg.append(f"Categoría de producto: {so_line_obj.product_id.categ_id.name} (ID: {so_line_obj.product_id.categ_id.id})")
            log_msg.append(f"Cliente: {so_line_obj.order_id.partner_id.name} (ID: {so_line_obj.order_id.partner_id.id})")
            
            # Usar el domain de la promocion para filtrar promos
            promos_aprobadas = []
            hoy = str(datetime.now())
            # Usando el modelo coupon.program en lugar de as.coupon.program
            promos = self.env['coupon.program'].sudo().search([('active', '=', True),('rule_date_to', '>', hoy)])
            
            log_msg.append(f"Total de promociones activas: {len(promos)}")
            log_msg.append("Filtros de búsqueda: [('active', '=', True), ('rule_date_to', '>', '%s')]" % hoy)
            
            for promo in promos:
                domain = safe_eval(promo.rule_products_domain)
                log_msg.append(f"\nPromo: {promo.name} (ID: {promo.id})")
                log_msg.append(f"Dominio de productos: {domain}")
                
                # Comprobar si el producto coincide con el dominio
                productos = self.env['product.product'].sudo().search(domain)
                log_msg.append(f"Productos que coinciden con el dominio: {len(productos)}")
                if productos:
                    log_msg.append(f"IDs de productos coincidentes: {productos.ids[:5]}{'...' if len(productos) > 5 else ''}")
                
                if so_line_obj.product_id in productos:
                    log_msg.append(f"✓ El producto {so_line_obj.product_id.name} coincide con el dominio")
                    promos_aprobadas.append(promo)
                else:
                    log_msg.append(f"✗ El producto {so_line_obj.product_id.name} NO coincide con el dominio")
            
            tf_partner_id = self.env['tf.res.partner']
            partner_params = so_line_obj.order_id.partner_id.tf_vendor_parameter_ids
            log_msg.append(f"\nParámetros de proveedor del cliente: {len(partner_params)} registros")
            
            for x in partner_params:
                log_msg.append(f"Parámetro: {x.name} (ID: {x.id})")
                log_msg.append(f"Categoría: {x.category_id.name} (ID: {x.category_id.id})")
                log_msg.append(f"Tipo de socio: {x.partner_type.name} (ID: {x.partner_type.id})")
                
                if x.category_id.id == so_line_obj.product_id.categ_id.id:
                    log_msg.append(f"✓ La categoría coincide con la del producto {so_line_obj.product_id.categ_id.name}")
                    tf_partner_id = x
                else:
                    log_msg.append(f"✗ La categoría NO coincide con la del producto {so_line_obj.product_id.categ_id.name}")
            
            price_unitt = so_line_obj.currency_id._convert_nimax(so_line_obj.price_unit, self.env.company.currency_id, self.env.company, so_line_obj.order_id.date_order,so_line_obj.id)
            
            if promos_aprobadas:
                log_msg.append(f"\nPromociones aprobadas que pasan el filtro de producto: {len(promos_aprobadas)}")
                for promo in promos_aprobadas:
                    log_msg.append(f"Procesando promo: {promo.name} (Tipo: {promo.as_type})")
                    
                    if promo.as_type == 'DEAL':
                        discount_percentage = promo.discount_percentage
                        price_unit = price_unitt - ((promo.discount_percentage/100) * price_unitt)

                        if price_unit:
                            margin_per = (100 * (price_unit - so_line_obj.product_id.standard_price))/price_unit

                            C47 = price_unitt
                            C48 = so_line_obj.product_id.list_price
                            C49 = so_line_obj.COST_NIMAX_USD
                            G46 = discount_percentage

                            wz_line_id = self.env['as.sale.order.promo.wizard.line'].create({
                                'sh_promo_id': promo.id,
                                'sh_unit_price': price_unit,
                                'line_id': so_line,
                                'tf_partner_id': tf_partner_id.id,
                                'line_id':so_line_obj.id,
                                'as_descuento': discount_percentage,
                                'RECALCULATED_PRICE_UNIT': C47-(C48*G46/100),
                                'RECALCULATED_COST_NIMAX_USD': C49-(C48*G46/100),
                            })

                            promo_list.append(wz_line_id.id)
                    if promo.as_type == 'DEMO':
                        discount = promo.discount_fixed_amount
                        discount_percentage = promo.discount_percentage
                        price_unit = so_line_obj.product_id.list_price - discount
                        if price_unit:
                            C57 = so_line_obj.product_id.list_price
                            C58 = so_line_obj.COST_NIMAX_USD
                            G55 = discount_percentage
                            H55 = promo.COSTO
                            wz_line_id = self.env['as.sale.order.promo.wizard.line'].create({
                                'sh_promo_id': promo.id,
                                'sh_unit_price': price_unit,
                                'line_id': so_line,
                                'tf_partner_id': tf_partner_id.id,
                                'as_descuento': discount,
                                'line_id':so_line_obj.id,
                                'RECALCULATED_PRICE_UNIT': (C57-(C57*G55/100)),
                                'RECALCULATED_COST_NIMAX_USD': (C57-(C57*H55/100)),
                            })

                            promo_list.append(wz_line_id.id)

                    if promo.as_type == 'ESPECIAL':
                        discount = promo.discount_fixed_amount
                        wz_line_id = self.env['as.sale.order.promo.wizard.line'].create({
                            'sh_promo_id': promo.id,
                            'line_id': so_line,
                            'tf_partner_id': tf_partner_id.id,
                            'as_descuento': discount,
                            'line_id':so_line_obj.id,
                            'RECALCULATED_PRICE_UNIT': promo.PRICE_UNIT_USD,
                            'RECALCULATED_COST_NIMAX_USD': promo.COST_NIMAX_USD,
                        })

                        promo_list.append(wz_line_id.id)

                    if promo.as_type == 'FABRICANTE':
                        discount = promo.discount_fixed_amount
                        wz_line_id = self.env['as.sale.order.promo.wizard.line'].create({
                            'sh_promo_id': promo.id,
                            'line_id': so_line,
                            'tf_partner_id': tf_partner_id.id,
                            'line_id':so_line_obj.id,
                            'as_descuento': discount,
                            'RECALCULATED_PRICE_UNIT': price_unitt - promo.DISCOUNT_AMOUNT_USD,
                            'RECALCULATED_COST_NIMAX_USD': so_line_obj.COST_NIMAX_USD - promo.DISCOUNT_AMOUNT_USD,
                        })

                        promo_list.append(wz_line_id.id)
            else:
                log_msg.append("\n⚠️ No se encontraron promociones que coincidan con los criterios")
            
            # Registrar toda la información en el chatter de la orden de venta
            so_line_obj.order_id.message_post(body="<pre>" + "\n".join(log_msg) + "</pre>", 
                                             subtype_xmlid='mail.mt_note',
                                             message_type='comment',
                                             body_is_html=True)

            # Filtro secundario para las promociones que ya pasaron el primer filtro de productos
            # Verifica las reglas de clientes, fechas y otros criterios adicionales
            new_promo = []
            sale_id = so_line_obj.order_id
            _logger.info("[as_promotion] Iniciando filtro secundario de promociones - %s promociones para evaluar", len(promo_list))
            
            for tfpromo in promo_list:
                wiz_promo = self.env['as.sale.order.promo.wizard.line'].browse(tfpromo)
                check = True
                _logger.info("[as_promotion] Evaluando promoción: %s (ID: %s)", wiz_promo.sh_promo_id.name, wiz_promo.sh_promo_id.id)
                
                # Verificar si el cliente actual cumple con el dominio de partners de la promoción
                if wiz_promo.sh_promo_id.rule_partners_domain:
                    customer_domain = safe_eval(wiz_promo.sh_promo_id.rule_partners_domain)
                    _logger.info("[as_promotion] Dominio original de clientes: %s", customer_domain)
                    
                    customer_domain.append(["id","=",sale_id.partner_id.id])
                    _logger.info("[as_promotion] Dominio con filtro de cliente actual: %s", customer_domain)
                    
                    customer = self.env['res.partner'].search(customer_domain)
                    if not customer:
                        check = False
                        _logger.info("[as_promotion] ❌ Cliente %s (ID: %s) NO cumple con el dominio de la promoción", 
                                     sale_id.partner_id.name, sale_id.partner_id.id)
                    else:
                        _logger.info("[as_promotion] ✓ Cliente %s (ID: %s) SÍ cumple con el dominio de la promoción", 
                                     sale_id.partner_id.name, sale_id.partner_id.id)
                else:
                    _logger.info("[as_promotion] Sin restricción de clientes definida")
                
                # Verificar nuevamente que el producto cumpla con el dominio específico
                if check and wiz_promo.sh_promo_id.rule_products_domain:
                    product_domain = safe_eval(wiz_promo.sh_promo_id.rule_products_domain)
                    product_domain.append(('id','=',so_line_obj.product_id.id))
                    _logger.info("[as_promotion] Dominio de productos con filtro específico: %s", product_domain)
                    
                    product = self.env['product.product'].search(product_domain)
                    if not product:
                        check = False
                        _logger.info("[as_promotion] ❌ Producto %s (ID: %s) NO cumple con el dominio específico", 
                                     so_line_obj.product_id.name, so_line_obj.product_id.id)
                    else:
                        _logger.info("[as_promotion] ✓ Producto %s (ID: %s) SÍ cumple con el dominio específico", 
                                     so_line_obj.product_id.name, so_line_obj.product_id.id)
                
                # Verificar fechas de validez: la fecha de inicio debe ser anterior a la fecha de la orden
                if check and wiz_promo.sh_promo_id.rule_date_from:
                    promo_start_date = str(wiz_promo.sh_promo_id.rule_date_from.date())
                    order_date = str(sale_id.date_order.date())
                    if promo_start_date >= order_date:
                        check = False
                        _logger.info("[as_promotion] ❌ Fecha inicio promoción (%s) es posterior o igual a fecha orden (%s)", 
                                     promo_start_date, order_date)
                    else:
                        _logger.info("[as_promotion] ✓ Fecha inicio promoción (%s) es anterior a fecha orden (%s)", 
                                     promo_start_date, order_date)
                
                # Verificar fechas de validez: la fecha de fin debe ser posterior a la fecha de la orden
                if check and wiz_promo.sh_promo_id.rule_date_to:
                    promo_end_date = str(wiz_promo.sh_promo_id.rule_date_to.date())
                    order_date = str(sale_id.date_order.date())
                    if order_date >= promo_end_date:
                        check = False
                        _logger.info("[as_promotion] ❌ Fecha fin promoción (%s) es anterior o igual a fecha orden (%s)", 
                                     promo_end_date, order_date)
                    else:
                        _logger.info("[as_promotion] ✓ Fecha fin promoción (%s) es posterior a fecha orden (%s)", 
                                     promo_end_date, order_date)
                
                # Añadir a la lista final solo las promociones que cumplen todos los criterios
                if check:
                    new_promo.append(wiz_promo.id)
                    _logger.info("[as_promotion] ✅ Promoción %s (ID: %s) APROBADA - cumple todos los criterios", 
                                 wiz_promo.sh_promo_id.name, wiz_promo.sh_promo_id.id)
                else:
                    _logger.info("[as_promotion] ❌ Promoción %s (ID: %s) RECHAZADA - no cumple todos los criterios", 
                                 wiz_promo.sh_promo_id.name, wiz_promo.sh_promo_id.id)
            
            _logger.info("[as_promotion] Resultado final: %s promociones aprobadas de %s evaluadas", 
                         len(new_promo), len(promo_list))
            
            # Actualizar el resultado con las promociones finales filtradas

            res.update({
                'promo_line': [(6, 0, new_promo)],
            })
        return res

    def process_time(self, intime, start, end):
        if start and end:
            if start <= intime <= end:
                return True
            elif start > end:
                end_day = time(hour=23, minute=59, second=59, microsecond=999999)
                if start <= intime <= end_day:
                    return True
                elif intime <= end:
                    return True
            return False
        elif start =='' and end == '':
            return True

class as_SaleOrderPromoWizardLine(models.TransientModel):
    _name = 'as.sale.order.promo.wizard.line'
    _description = 'Promo Wizard Line'

    promo_id = fields.Many2one('as.sale.order.promo.wizard', "Promo Id")
    # Campo relacionado con ondelete='cascade' para evitar errores de restricción
    sh_promo_id = fields.Many2one(
        'coupon.program', "Promo", required=True, ondelete='cascade')
    sh_unit_price = fields.Float('Unit Price')
    sh_margin = fields.Float('Margin')
    sh_margin_per = fields.Float('Margin %')
    line_id = fields.Many2one('sale.order.line')

    # Descuento calculado percent_price
    as_descuento = fields.Float(string='Descuento')
    tf_dis_amount = fields.Float('Discounted price')
    PRICE_UNIT_USD = fields.Float('PRICE UNIT USD')
    COST_NIMAX_USD = fields.Float('COST NIMAX USD')
    tf_partner_id = fields.Many2one('tf.res.partner',"Partner program")
    RECALCULATED_PRICE_UNIT = fields.Float('Precio Unitario USD')
    RECALCULATED_COST_NIMAX_USD = fields.Float('Costo NIMAX USD')

    def update_sale_line_unit_price_promo(self):
        if self.line_id:
            _logger.info("[as_promotion] Aplicando promoción %s (ID: %s) a línea de venta %s", 
                         self.sh_promo_id.name, self.sh_promo_id.id, self.line_id.id)

            # Primero creamos un diccionario básico con los valores a actualizar
            data_update = {
                'price_unit': self.sh_unit_price,
                'margin2': self.sh_margin,
                # 'coupon_ids': [(4, self.sh_promo_id.id)]  # COMENTADO: Esto está causando el error
            }
            
            try:
                # En lugar de usar el campo coupon_ids, intentamos vincular la promoción de otra manera
                # Primero comprobamos si existe el campo en el modelo
                if hasattr(self.line_id, 'coupon_id'):
                    # Odoo 18 usa coupon_id (loyalty.card) y reward_id (loyalty.reward)
                    _logger.info("[as_promotion] Odoo 18 detected: usando campos coupon_id y reward_id")
                    # No hacemos nada aquí, ya que necesitaríamos crear un loyalty.card primero
                elif hasattr(self.line_id, 'promotion_coupon_id'):
                    # Odoo 15 podría usar promotion_coupon_id
                    _logger.info("[as_promotion] Campo promotion_coupon_id detectado")
                    data_update['promotion_coupon_id'] = self.sh_promo_id.id
                else:
                    # Enfoque alternativo: podríamos usar un campo personalizado
                    _logger.info("[as_promotion] Sin campos compatibles detectados, saltando vinculación de cupón")
                    # Podríamos crear un campo personalizado as_promotion_id si es necesario
            except Exception as e:
                _logger.error("[as_promotion] Error al verificar campos de cupón: %s", str(e))
            
            # Continuar con el proceso normal para los diferentes tipos de promoción
            if self.sh_promo_id.as_type == 'DEAL':
                # Código existente sin cambios
                moneda_mxn = self.env['res.currency'].search([('id','=',33)])
                moneda_usd = self.env['res.currency'].search([('id','=',2)])
                price_unit = self.line_id.price_unit
                RECALCULATED_PRICE_UNIT = self.RECALCULATED_PRICE_UNIT
                monto_mxp= moneda_usd._convert_nimax(self.RECALCULATED_PRICE_UNIT, moneda_mxn, self.env.company, fields.Date.today(),self.line_id.id)
                NIMAX_PRICE_MXP = monto_mxp
                COST_NIMAX_USD = moneda_usd._convert_nimax(self.RECALCULATED_COST_NIMAX_USD, moneda_usd, self.env.company, fields.Date.today(),self.line_id.id)
                COST_NIMAX_MXP = moneda_usd._convert_nimax(self.RECALCULATED_COST_NIMAX_USD, moneda_mxn, self.env.company, fields.Date.today(),self.line_id.id)
                MARGIN_MXP = (NIMAX_PRICE_MXP*self.line_id.product_uom_qty)-(COST_NIMAX_MXP*self.line_id.product_uom_qty)
                MARGIN_USD = (RECALCULATED_PRICE_UNIT*self.line_id.product_uom_qty)-(COST_NIMAX_USD*self.line_id.product_uom_qty)
                TOTAL_USD = RECALCULATED_PRICE_UNIT*self.line_id.product_uom_qty
                TOTAL_MXP = NIMAX_PRICE_MXP * self.line_id.product_uom_qty

                data_update.update({
                    'price_unit': self.line_id.price_unit,
                    'RECALCULATED_PRICE_UNIT': self.RECALCULATED_PRICE_UNIT,
                    'RECALCULATED_COST_NIMAX_USD': self.RECALCULATED_COST_NIMAX_USD,
                    'MARGIN_USD':  (self.RECALCULATED_PRICE_UNIT*self.line_id.product_uom_qty)-(self.RECALCULATED_COST_NIMAX_USD*self.line_id.product_uom_qty),
                    'TOTAL_USD':  self.RECALCULATED_PRICE_UNIT* self.line_id.product_uom_qty,
                    'NIMAX_PRICE_MXP':  NIMAX_PRICE_MXP,
                    'COST_NIMAX_MXP':  COST_NIMAX_MXP,
                    'MARGIN_MXP':  MARGIN_MXP,
                    'TOTAL_MXP':  TOTAL_MXP,
                })
                self.get_sentinel_qty_promotion(self.sh_promo_id,self.line_id.product_uom_qty)
            elif self.sh_promo_id.as_type == 'DEMO':
                moneda_mxn = self.env['res.currency'].search([('id','=',33)])
                moneda_usd = self.env['res.currency'].search([('id','=',2)])
                price_unit = self.line_id.price_unit
                RECALCULATED_PRICE_UNIT = self.RECALCULATED_PRICE_UNIT
                monto_mxp= moneda_usd._convert_nimax(RECALCULATED_PRICE_UNIT, moneda_mxn, self.env.company, fields.Date.today(),self.line_id.id)
                NIMAX_PRICE_MXP = monto_mxp
                COST_NIMAX_USD = self.RECALCULATED_COST_NIMAX_USD
                COST_NIMAX_MXP = moneda_usd._convert_nimax(self.RECALCULATED_COST_NIMAX_USD, moneda_mxn, self.env.company, fields.Date.today(),self.line_id.id)
                MARGIN_MXP = (NIMAX_PRICE_MXP*self.line_id.product_uom_qty)-(COST_NIMAX_MXP*self.line_id.product_uom_qty)
                MARGIN_USD = (RECALCULATED_PRICE_UNIT*self.line_id.product_uom_qty)-(COST_NIMAX_USD*self.line_id.product_uom_qty)
                TOTAL_USD = RECALCULATED_PRICE_UNIT*self.line_id.product_uom_qty
                TOTAL_MXP = NIMAX_PRICE_MXP * self.line_id.product_uom_qty
                data_update.update({
                    'price_unit': self.line_id.price_unit,
                    'RECALCULATED_PRICE_UNIT': self.RECALCULATED_PRICE_UNIT,
                    'RECALCULATED_COST_NIMAX_USD': self.RECALCULATED_COST_NIMAX_USD,
                    'MARGIN_USD':  (self.RECALCULATED_PRICE_UNIT*self.line_id.product_uom_qty)-(self.RECALCULATED_COST_NIMAX_USD*self.line_id.product_uom_qty),
                    'TOTAL_USD':  self.RECALCULATED_PRICE_UNIT* self.line_id.product_uom_qty,
                    'NIMAX_PRICE_MXP':  NIMAX_PRICE_MXP,
                    'COST_NIMAX_USD':  COST_NIMAX_USD,
                    'COST_NIMAX_MXP':  COST_NIMAX_MXP,
                    'MARGIN_MXP':  MARGIN_MXP,
                    'TOTAL_MXP':  TOTAL_MXP,
                })
                self.get_sentinel_qty_promotion(self.sh_promo_id,self.line_id.product_uom_qty)
            elif self.sh_promo_id.as_type == 'ESPECIAL':
                moneda_mxn = self.env['res.currency'].search([('id','=',33)])
                moneda_usd = self.env['res.currency'].search([('id','=',2)])
                price_unit = self.line_id.price_unit
                RECALCULATED_PRICE_UNIT = self.RECALCULATED_PRICE_UNIT
                monto_mxp= moneda_usd._convert_nimax(RECALCULATED_PRICE_UNIT, moneda_mxn, self.env.company, fields.Date.today(),self.line_id.id)
                NIMAX_PRICE_MXP = monto_mxp
                COST_NIMAX_USD = moneda_usd._convert_nimax(self.RECALCULATED_COST_NIMAX_USD, moneda_usd, self.env.company, fields.Date.today(),self.line_id.id)
                COST_NIMAX_MXP = moneda_usd._convert_nimax(self.RECALCULATED_COST_NIMAX_USD, moneda_mxn, self.env.company, fields.Date.today(),self.line_id.id)
                MARGIN_MXP = (NIMAX_PRICE_MXP*self.line_id.product_uom_qty)-(COST_NIMAX_MXP*self.line_id.product_uom_qty)
                MARGIN_USD = (RECALCULATED_PRICE_UNIT*self.line_id.product_uom_qty)-(COST_NIMAX_USD*self.line_id.product_uom_qty)
                TOTAL_USD = RECALCULATED_PRICE_UNIT*self.line_id.product_uom_qty
                TOTAL_MXP = NIMAX_PRICE_MXP * self.line_id.product_uom_qty
                
                data_update.update({
                    'price_unit': self.line_id.price_unit,
                    'RECALCULATED_PRICE_UNIT': self.RECALCULATED_PRICE_UNIT,
                    'RECALCULATED_COST_NIMAX_USD': self.RECALCULATED_COST_NIMAX_USD,
                    'MARGIN_USD':  (self.RECALCULATED_PRICE_UNIT*self.line_id.product_uom_qty)-(self.RECALCULATED_COST_NIMAX_USD*self.line_id.product_uom_qty),
                    'TOTAL_USD':  self.RECALCULATED_PRICE_UNIT* self.line_id.product_uom_qty,                    
                    'NIMAX_PRICE_MXP':  NIMAX_PRICE_MXP,
                    'COST_NIMAX_MXP':  COST_NIMAX_MXP,
                    'MARGIN_MXP':  MARGIN_MXP,
                    'TOTAL_MXP':  TOTAL_MXP,
                })
                self.get_sentinel_qty_promotion(self.sh_promo_id,self.line_id.product_uom_qty)
            elif self.sh_promo_id.as_type == 'FABRICANTE':
                moneda_mxn = self.env['res.currency'].search([('id','=',33)])
                moneda_usd = self.env['res.currency'].search([('id','=',2)])
                price_unit = self.line_id.price_unit
                RECALCULATED_PRICE_UNIT = self.RECALCULATED_PRICE_UNIT
                monto_mxp= moneda_usd._convert_nimax(RECALCULATED_PRICE_UNIT, moneda_mxn, self.env.company, fields.Date.today(),self.line_id.id)
                NIMAX_PRICE_MXP = monto_mxp
                COST_NIMAX_USD = moneda_usd._convert_nimax(self.RECALCULATED_COST_NIMAX_USD, moneda_usd, self.env.company, fields.Date.today(),self.line_id.id)
                COST_NIMAX_MXP = moneda_usd._convert_nimax(self.RECALCULATED_COST_NIMAX_USD, moneda_mxn, self.env.company, fields.Date.today(),self.line_id.id)
                MARGIN_MXP = (NIMAX_PRICE_MXP*self.line_id.product_uom_qty)-(COST_NIMAX_MXP*self.line_id.product_uom_qty)
                MARGIN_USD = (RECALCULATED_PRICE_UNIT*self.line_id.product_uom_qty)-(COST_NIMAX_USD*self.line_id.product_uom_qty)
                TOTAL_USD = RECALCULATED_PRICE_UNIT*self.line_id.product_uom_qty
                TOTAL_MXP = NIMAX_PRICE_MXP * self.line_id.product_uom_qty
                data_update.update({
                    'price_unit': self.line_id.price_unit,
                    'RECALCULATED_PRICE_UNIT': self.RECALCULATED_PRICE_UNIT,
                    'RECALCULATED_COST_NIMAX_USD': self.RECALCULATED_COST_NIMAX_USD,
                    'MARGIN_USD':  (self.RECALCULATED_PRICE_UNIT*self.line_id.product_uom_qty)-(self.RECALCULATED_COST_NIMAX_USD*self.line_id.product_uom_qty),
                    'TOTAL_USD':  self.RECALCULATED_PRICE_UNIT* self.line_id.product_uom_qty,
                    'NIMAX_PRICE_MXP':  NIMAX_PRICE_MXP,
                    'COST_NIMAX_MXP':  COST_NIMAX_MXP,
                    'MARGIN_MXP':  MARGIN_MXP,
                    'TOTAL_MXP':  TOTAL_MXP,
                })
                self.get_sentinel_qty_promotion(self.sh_promo_id,self.line_id.product_uom_qty)
            precio_nimax= self.env.company.currency_id._convert_nimax(self.RECALCULATED_PRICE_UNIT, self.line_id.currency_id, self.env.company, self.line_id.order_id.date_order,self.line_id.id)
            data_update.update({
                'price_unit': precio_nimax,
                'COST_NIMAX_USD': self.RECALCULATED_COST_NIMAX_USD,
                'as_log_price': True,
            })
            
            # Guardar registro con qué promoción se está aplicando sin usar campos M2M problemáticos
            try:
                _logger.info("[as_promotion] Actualizando línea de venta con: %s", data_update)
                self.line_id.write(data_update)
                
                # Actualizar la orden para que sepa qué promoción se aplicó
                if hasattr(self.line_id.order_id, 'last_promo_id'):
                    self.line_id.order_id.last_promo_id = self.sh_promo_id.id
                    
                # Crear un registro en el historial de promociones
                self.env['tf.history.promo'].create({
                    'vendor_id': self.tf_partner_id.partner_id.id if hasattr(self.tf_partner_id, 'partner_id') else False,
                    'product_id': self.line_id.product_id.id,
                    'customer_id': self.line_id.order_id.partner_id.id,
                    'customer_type': self.tf_partner_id.partner_type.id if hasattr(self.tf_partner_id, 'partner_type') else False,
                    'category_id': self.line_id.product_id.categ_id.id,
                    'qty': self.line_id.product_uom_qty,
                    'recalculated_price_unit': self.line_id.RECALCULATED_PRICE_UNIT,
                    'recalculated_price_unit_mxp': self.line_id.NIMAX_PRICE_MXP,
                    'recalculated_cost_nimax_mxp': self.line_id.COST_NIMAX_MXP,
                    'recalculated_cost_nimax_usd': self.line_id.RECALCULATED_COST_NIMAX_USD,
                    'margin_mxp': self.line_id.MARGIN_MXP,
                    'margin_usd': self.line_id.MARGIN_USD,
                    'total_usd': self.line_id.TOTAL_USD,
                    'total_mxp': self.line_id.TOTAL_MXP,
                    'salesman_id': self.line_id.order_id.user_id.id,
                    'sale_id': self.line_id.order_id.id,
                    'promo_id': self.sh_promo_id.id,
                    'sale_order_line': self.line_id.id,
                })
                
                _logger.info("[as_promotion] ✓ Promoción aplicada correctamente")
                
            except Exception as e:
                _logger.error("[as_promotion] Error al aplicar promoción: %s", str(e))
                raise

    def get_sentinel_qty_promotion(self,promo,qty):
        try:
            # Verificar si la promoción tiene los campos necesarios
            _logger.info("[as_promotion] Verificando límites de cantidad para promoción %s (ID: %s)", 
                         promo.name, promo.id)
            
            # Obtener valores con manejo seguro de atributos
            # Si algún atributo no existe, usar valores predeterminados seguros
            maximo = getattr(promo, 'tf_max_gifted_qty', 999999)
            balance = getattr(promo, 'tf_balance', 0)
            gifted_qty = getattr(promo, 'tf_gifted_qty', 0)
            
            _logger.info("[as_promotion] Valores de control: máximo=%s, balance=%s, cantidad_regalada=%s, cantidad_solicitada=%s", 
                         maximo, balance, gifted_qty, qty)
            
            quantity = gifted_qty + qty
            
            if quantity > maximo:
                _logger.warning("[as_promotion] ❌ Cantidad excedida para promoción %s: solicitado=%s, máximo=%s", 
                               promo.name, quantity, maximo)
                raise ValidationError('La cantidad a vender (%s) supera la permitida para la promoción (%s). Máximo: %s' % 
                                     (qty, str(promo.name), maximo))
            else:
                _logger.info("[as_promotion] ✓ Cantidad aceptada para promoción %s: %s de %s máximo", 
                            promo.name, quantity, maximo)
        except AttributeError as e:
            # Registrar el error pero continuar sin validar
            _logger.warning("[as_promotion] ⚠️ No se pudo validar cantidad para promoción %s: %s", 
                           promo.name, str(e))
            _logger.info("[as_promotion] Continuando sin validación de cantidad")
            # No lanzamos excepción para que el proceso pueda continuar


