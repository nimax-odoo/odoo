# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date
import logging
from odoo.tools.safe_eval import safe_eval
_logger = logging.getLogger(__name__)

#from odoo.exceptions import UserError


class SaleOrderPricelistWizard(models.TransientModel):
    _name = 'product.pricelist.promo.wizard'
    _description = 'Pricelist Wizard'
    
    sh_pricelist_id = fields.Many2one('product.pricelist', string="Pricelist")
    currency_id = fields.Many2one('res.currency', string="Currency", related='sh_pricelist_id.currency_id')
    nimax_price_usd = fields.Float(string="Precio")
    cost_nimax_usd = fields.Float(string="Costo NIMAX USD")
    product_uom_qty = fields.Float(string="Cantidad")
    partner_id = fields.Many2one('res.partner', string="Cliente")
    product_id = fields.Many2one('product.product', string="Producto")
    
    
    
    def calculate(self, sh_pricelist_id, currency_id, partner_id, product_id, product_uom_qty):
        fields_vals = []
        now = date.today()
        pricelists = sh_pricelist_id
        if pricelists:
            for pricelist in pricelists:
                item_pricelist = False
                for item in pricelist.item_ids:
                    if item.categ_id == product_id.categ_id:
                        item_pricelist = item
                        
                tf_partner_id = self.env['tf.res.partner']
                for x in partner_id.tf_vendor_parameter_ids:
                    if x.category_id.id == product_id.categ_id.id:
                        tf_partner_id = x
                        
                if not tf_partner_id:
                    continue

                if [x for x in pricelist.item_ids if x.applied_on == '2_product_category'] and \
                        not [x for x in pricelist.item_ids if x.applied_on == '2_product_category' and product_id.categ_id.id == x.categ_id.id]:
                    continue

                # Adaptación a Odoo 18: _compute_price_rule tiene una nueva API
                try:
                    # Usando la API de Odoo 18 para _compute_price_rule
                    # En Odoo 18, la firma ha cambiado completamente
                    # Ahora espera: products, quantity, currency=None, uom=None, date=False
                    price_result = pricelist._compute_price_rule(
                        products=product_id,
                        quantity=product_uom_qty,
                        currency=currency_id,
                        uom=product_id.uom_id,
                        date=date.today()
                    )
                    price_unit = price_result[product_id.id][0]
                    _logger.info(f"[default_get] Precio calculado: {price_unit}")
                except Exception as e:
                    _logger.error(f"[default_get] Error al calcular el precio: {str(e)}")
                    # Si hay error, intentamos con precio base del producto
                    price_unit = product_id.list_price
                    _logger.info(f"[default_get] Usando precio base: {price_unit}")
                
                if price_unit:
                    margin = price_unit - product_id.standard_price
                    margin_per = (100 * (price_unit - product_id.standard_price))/price_unit if price_unit else 0
                    descuento = 0
                    margin2 = 0
                    
                    if item_pricelist and item_pricelist.as_utilidad > 0:
                        # Verificamos si existe el campo as_last_purchase_price
                        last_purchase_price = 0.0
                        if hasattr(product_id, 'as_last_purchase_price'):
                            last_purchase_price = product_id.as_last_purchase_price
                        else:
                            # Si no existe, usamos el standard_price como alternativa
                            _logger.warning(f"[default_get] Campo as_last_purchase_price no existe, usando standard_price")
                            last_purchase_price = product_id.standard_price
                        
                        if last_purchase_price and (1-item_pricelist.as_utilidad/100) != 0:
                            descuento = (1-(last_purchase_price/(1-item_pricelist.as_utilidad/100)))*100
                            price_unit = product_id.list_price * (1-descuento/100)
                            margin2 = price_unit * (item_pricelist.as_utilidad / 100)
                        else:
                            _logger.warning(f"[default_get] Precio de compra es 0 o división por cero, saltando cálculo de descuento")
                        
                    price_based_usd = (product_id.list_price - (product_id.list_price * tf_partner_id.partner_discount/100))*tf_partner_id.cost_deal_import/100*(product_id.product_tmpl_id.tf_import_tax/100)
                    cost_nimax_usd = ((product_id.list_price - (product_id.list_price*tf_partner_id.purchase_discount/100))-(product_id.list_price*tf_partner_id.fulfillment_rebate/100))*(tf_partner_id.cost_deal_import/100)*(product_id.product_tmpl_id.tf_import_tax/100)
                    
                    # Convertimos valores
                    moneda_mxn = self.env.ref('base.MXN', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','MXN')], limit=1)
                    moneda_usd = self.env.ref('base.USD', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','USD')], limit=1)
                    
                    margin_per = self.env.company.currency_id._convert_nimax(margin_per, pricelist.currency_id, self.env.company, now, False)
                    margin2 = self.env.company.currency_id._convert_nimax(margin2, pricelist.currency_id, self.env.company, now, False)
                    cost_nimax_usd = self.env.company.currency_id._convert_nimax(cost_nimax_usd, pricelist.currency_id, self.env.company, now, False)
                    price_based_usd = self.env.company.currency_id._convert_nimax(price_based_usd, pricelist.currency_id, self.env.company, now, False)
                    descuento = self.env.company.currency_id._convert_nimax(descuento, pricelist.currency_id, self.env.company, now, False)
                    price_unit = self.env.company.currency_id._convert_nimax(price_unit, pricelist.currency_id, self.env.company, now, False)
                    list_price = self.env.company.currency_id._convert_nimax(product_id.list_price, pricelist.currency_id, self.env.company, now, False)
                    # Verificamos si existe el campo as_last_purchase_price
                    last_purchase_price = 0.0
                    if hasattr(product_id, 'as_last_purchase_price'):
                        last_purchase_price = product_id.as_last_purchase_price
                    else:
                        # Si no existe, usamos el standard_price como alternativa
                        _logger.warning(f"[default_get] Campo as_last_purchase_price no existe, usando standard_price")
                        last_purchase_price = product_id.standard_price
                        
                    as_last_purchase_price = self.env.company.currency_id._convert_nimax(last_purchase_price, pricelist.currency_id, self.env.company, now, False)
                    nimax_price_usd = (price_based_usd)/(1-pricelist.expected_earning/100) if pricelist.expected_earning else price_based_usd
                    fields_vals.append({
                        'sh_pricelist_id': sh_pricelist_id.id,
                        'currency_id': currency_id.id,
                        'partner_id': partner_id.id,
                        'product_id': product_id.id,
                        'product_uom_qty': product_uom_qty,
                        'cost_nimax_usd': cost_nimax_usd,
                        'nimax_price_usd': nimax_price_usd,
                    })
                    

                
            
            # Usar el domain de la promocion para filtrar promos
            promos_aprobadas = []
            hoy = str(date.today())
            # Usando el modelo coupon.program en lugar de as.coupon.program
            promos = self.env['coupon.program'].sudo().search([('active', '=', True),('rule_date_to', '>', hoy),('sd_apply_toprunner_api','=',True),('active','=',True)])
        
            
            for promo in promos.filtered(lambda l: l.tf_balance > 0):
                domain = safe_eval(promo.rule_products_domain)
                
                # Comprobar si el producto coincide con el dominio
                productos = self.env['product.product'].sudo().search(domain)
                if productos:
                    promos_aprobadas.append(promo)

            
            tf_partner_id = self.env['tf.res.partner']
            partner_params = partner_id.tf_vendor_parameter_ids
            
            for x in partner_params:               
                if x.category_id.id == product_id.categ_id.id:
                    tf_partner_id = x
            
            price_unitt = currency_id._convert_nimax(nimax_price_usd, self.env.company.currency_id, self.env.company, now,False)
            promociones = []
            if promos_aprobadas:
                for promo in promos_aprobadas:
                    
                    if promo.as_type == 'DEAL':
                        discount_percentage = promo.discount_percentage
                        price_unit = price_unitt - ((promo.discount_percentage/100) * price_unitt)

                        if price_unit:
                            margin_per = (100 * (price_unit - product_id.standard_price))/price_unit

                            C47 = price_unitt
                            C48 = product_id.list_price
                            C49 = cost_nimax_usd
                            G46 = discount_percentage

                            promociones.append({
                                'sh_promo_id': promo.id,
                                'sh_unit_price': price_unit,
                                'tf_partner_id': tf_partner_id.id,
                                'as_descuento': discount_percentage,
                                'RECALCULATED_PRICE_UNIT': C47-(C48*G46/100),
                                'RECALCULATED_COST_NIMAX_USD': C49-(C48*G46/100),
                            })

                    if promo.as_type == 'DEMO':
                        discount = promo.discount_fixed_amount
                        discount_percentage = promo.discount_percentage
                        price_unit = product_id.list_price - discount
                        if price_unit:
                            C57 = product_id.list_price
                            C58 = cost_nimax_usd
                            G55 = discount_percentage
                            H55 = promo.COSTO
                            promociones.append({
                                'sh_promo_id': promo.id,
                                'sh_unit_price': price_unit,
                                'tf_partner_id': tf_partner_id.id,
                                'as_descuento': discount,
                                'RECALCULATED_PRICE_UNIT': (C57-(C57*G55/100)),
                                'RECALCULATED_COST_NIMAX_USD': (C57-(C57*H55/100)),
                            })


                    if promo.as_type == 'ESPECIAL':
                        discount = promo.discount_fixed_amount
                        promociones.append({
                            'sh_promo_id': promo.id,
                            'tf_partner_id': tf_partner_id.id,
                            'as_descuento': discount,
                            'RECALCULATED_PRICE_UNIT': promo.PRICE_UNIT_USD,
                            'RECALCULATED_COST_NIMAX_USD': promo.COST_NIMAX_USD,
                        })


                    if promo.as_type == 'FABRICANTE':
                        discount = promo.discount_fixed_amount
                        promociones.append({
                            'sh_promo_id': promo.id,
                            'tf_partner_id': tf_partner_id.id,
                            'as_descuento': discount,
                            'RECALCULATED_PRICE_UNIT': price_unitt - promo.DISCOUNT_AMOUNT_USD,
                            'RECALCULATED_COST_NIMAX_USD': cost_nimax_usd - promo.DISCOUNT_AMOUNT_USD,
                        })


            
            new_promo = []
            
            for tfpromo in promociones:
                check = True
                promo_orm = self.env['coupon.program'].sudo().browse(tfpromo['sh_promo_id'])
                # Verificar si el cliente actual cumple con el dominio de partners de la promoción
                if promo_orm.rule_partners_domain:
                    customer_domain = safe_eval(promo_orm.rule_partners_domain)
                    
                    customer_domain.append(["id","=",partner_id.id])
                    
                    customer = self.env['res.partner'].search(customer_domain)
                    if not customer:
                        check = False


                
                # Verificar nuevamente que el producto cumpla con el dominio específico
                if check and promo_orm.rule_products_domain:
                    product_domain = safe_eval(promo_orm.rule_products_domain)
                    product_domain.append(('id','=',product_id.id))
                    
                    product = self.env['product.product'].search(product_domain)
                    if not product:
                        check = False

                
                # Verificar fechas de validez: la fecha de inicio debe ser anterior a la fecha de la orden
                if check and promo_orm.rule_date_from:
                    promo_start_date = str(promo_orm.rule_date_from.date())
                    order_date = str(now)
                    if promo_start_date >= order_date:
                        check = False

                
                # Verificar fechas de validez: la fecha de fin debe ser posterior a la fecha de la orden
                if check and promo_orm.rule_date_to:
                    promo_end_date = str(promo_orm.rule_date_to.date())
                    order_date = str(now)
                    if order_date >= promo_end_date:
                        check = False
                
                # Añadir a la lista final solo las promociones que cumplen todos los criterios
                if check:
                    new_promo.append(promo_orm.id)

        
        if new_promo:   
            # recorremos promociones para ver si existe new_promo en promociones en el campo sd_promo_id y retornar RECALCULATED_PRICE_UNIT y RECALCULATED_COST_NIMAX_USD
            for promo_id in new_promo:
                for tfpromo in promociones:
                    if tfpromo['sh_promo_id'] == promo_id:
                        # fields_vals[0]['nimax_price_usd'] = tfpromo['RECALCULATED_PRICE_UNIT']
                        # fields_vals[0]['cost_nimax_usd'] = tfpromo['RECALCULATED_COST_NIMAX_USD']
                        nimax_price_usd = tfpromo['RECALCULATED_PRICE_UNIT']
                        break
                     
        return nimax_price_usd
