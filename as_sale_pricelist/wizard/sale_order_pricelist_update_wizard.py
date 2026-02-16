# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date
import logging

_logger = logging.getLogger(__name__)

#from odoo.exceptions import UserError


class SaleOrderPricelistWizard(models.TransientModel):
    _name = 'sale.order.pricelist.wizard'
    _description = 'Pricelist Wizard'
    
    sh_pricelist_id = fields.Many2one('product.pricelist', string="Pricelist")
    pricelist_line = fields.One2many('sale.order.pricelist.wizard.line', 'pricelist_id', string='PricelistLine Id')
    
    @api.model
    def default_get(self, fields):
        res = super(SaleOrderPricelistWizard, self).default_get(fields)
        active_id = self._context.get('active_id')
        line_id = self._context.get('order_line_id')
        if active_id:
            order = self.env['sale.order'].browse(active_id)
            pricelist_list = []
            
            for line in order.order_line.filtered(lambda l: l.id == line_id):
                pricelists = self.env['product.pricelist'].sudo().search([('currency_id', '=', order.currency_id.id)])
                if pricelists:
                    for pricelist in pricelists:
                        item_pricelist = False
                        for item in pricelist.item_ids:
                            if item.categ_id == line.product_id.categ_id:
                                item_pricelist = item
                                
                        tf_partner_id = self.env['tf.res.partner']
                        for x in order.partner_id.tf_vendor_parameter_ids:
                            if x.category_id.id == line.product_id.categ_id.id:
                                tf_partner_id = x
                                
                        if not tf_partner_id:
                            continue

                        if [x for x in pricelist.item_ids if x.applied_on == '2_product_category'] and \
                                not [x for x in pricelist.item_ids if x.applied_on == '2_product_category' and line.product_id.categ_id.id == x.categ_id.id]:
                            continue

                        # Adaptación a Odoo 18: _compute_price_rule tiene una nueva API
                        try:
                            # Usando la API de Odoo 18 para _compute_price_rule
                            # En Odoo 18, la firma ha cambiado completamente
                            # Ahora espera: products, quantity, currency=None, uom=None, date=False
                            price_result = pricelist._compute_price_rule(
                                products=line.product_id,
                                quantity=line.product_uom_qty,
                                currency=order.currency_id,
                                uom=line.product_uom_id,
                                date=date.today()
                            )
                            price_unit = price_result[line.product_id.id][0]
                            _logger.info(f"[default_get] Precio calculado: {price_unit}")
                        except Exception as e:
                            _logger.error(f"[default_get] Error al calcular el precio: {str(e)}")
                            # Si hay error, intentamos con precio base del producto
                            price_unit = line.product_id.list_price
                            _logger.info(f"[default_get] Usando precio base: {price_unit}")
                        
                        if price_unit:
                            margin = price_unit - line.product_id.standard_price
                            margin_per = (100 * (price_unit - line.product_id.standard_price))/price_unit if price_unit else 0
                            descuento = 0
                            margin2 = 0
                            
                            if item_pricelist and item_pricelist.as_utilidad > 0:
                                # Verificamos si existe el campo as_last_purchase_price
                                last_purchase_price = 0.0
                                if hasattr(line.product_id, 'as_last_purchase_price'):
                                    last_purchase_price = line.product_id.as_last_purchase_price
                                else:
                                    # Si no existe, usamos el standard_price como alternativa
                                    _logger.warning(f"[default_get] Campo as_last_purchase_price no existe, usando standard_price")
                                    last_purchase_price = line.product_id.standard_price
                                
                                if last_purchase_price and (1-item_pricelist.as_utilidad/100) != 0:
                                    descuento = (1-(last_purchase_price/(1-item_pricelist.as_utilidad/100)))*100
                                    price_unit = line.product_id.list_price * (1-descuento/100)
                                    margin2 = price_unit * (item_pricelist.as_utilidad / 100)
                                else:
                                    _logger.warning(f"[default_get] Precio de compra es 0 o división por cero, saltando cálculo de descuento")
                                
                            price_based_usd = (line.product_id.list_price - (line.product_id.list_price * tf_partner_id.partner_discount/100))*tf_partner_id.cost_deal_import/100*(line.product_id.product_tmpl_id.tf_import_tax/100)
                            cost_nimax_usd = ((line.product_id.list_price - (line.product_id.list_price*tf_partner_id.purchase_discount/100))-(line.product_id.list_price*tf_partner_id.fulfillment_rebate/100))*(tf_partner_id.cost_deal_import/100)*(line.product_id.product_tmpl_id.tf_import_tax/100)
                            
                            # Convertimos valores
                            moneda_mxn = self.env.ref('base.MXN', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','MXN')], limit=1)
                            moneda_usd = self.env.ref('base.USD', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','USD')], limit=1)
                            
                            margin_per = self.env.company.currency_id._convert_nimax(margin_per, pricelist.currency_id, self.env.company, order.date_order, line.id)
                            margin2 = self.env.company.currency_id._convert_nimax(margin2, pricelist.currency_id, self.env.company, order.date_order, line.id)
                            cost_nimax_usd = self.env.company.currency_id._convert_nimax(cost_nimax_usd, pricelist.currency_id, self.env.company, order.date_order, line.id)
                            price_based_usd = self.env.company.currency_id._convert_nimax(price_based_usd, pricelist.currency_id, self.env.company, order.date_order, line.id)
                            descuento = self.env.company.currency_id._convert_nimax(descuento, pricelist.currency_id, self.env.company, order.date_order, line.id)
                            price_unit = self.env.company.currency_id._convert_nimax(price_unit, pricelist.currency_id, self.env.company, order.date_order, line.id)
                            list_price = self.env.company.currency_id._convert_nimax(line.product_id.list_price, pricelist.currency_id, self.env.company, order.date_order, line.id)
                            # Verificamos si existe el campo as_last_purchase_price
                            last_purchase_price = 0.0
                            if hasattr(line.product_id, 'as_last_purchase_price'):
                                last_purchase_price = line.product_id.as_last_purchase_price
                            else:
                                # Si no existe, usamos el standard_price como alternativa
                                _logger.warning(f"[default_get] Campo as_last_purchase_price no existe, usando standard_price")
                                last_purchase_price = line.product_id.standard_price
                                
                            as_last_purchase_price = self.env.company.currency_id._convert_nimax(last_purchase_price, pricelist.currency_id, self.env.company, order.date_order, line.id)
                            
                            wz_line_id = self.env['sale.order.pricelist.wizard.line'].create({
                                'sh_pricelist_id': pricelist.id,
                                'sh_unit_price': price_unit,
                                'sh_unit_measure': line.product_uom_id.id,
                                'sh_unit_cost': list_price,
                                'sh_margin': margin2,
                                'sh_margin_per': margin_per,
                                'line_id': line.id,
                                'as_precio_proveedor': as_last_purchase_price,
                                'as_descuento': descuento,
                                'price_based_usd': price_based_usd,
                                'nimax_price_usd': (price_based_usd)/(1-pricelist.expected_earning/100) if pricelist.expected_earning else price_based_usd,
                                'cost_nimax_usd': cost_nimax_usd,
                                'tf_partner_id': tf_partner_id.id,
                            })
                            
                            pricelist_list.append(wz_line_id.id)
                            
            res.update({
                'pricelist_line': [(6, 0, pricelist_list)],
            })
        return res

class SaleOrderPricelistWizardLine(models.TransientModel):
    _name = 'sale.order.pricelist.wizard.line'
    _description = 'Pricelist Wizard Line'
    
    pricelist_id = fields.Many2one('sale.order.pricelist.wizard', "Pricelist Id")
    sh_pricelist_id = fields.Many2one('product.pricelist', "Pricelist", required=True)
    sh_unit_measure = fields.Many2one('uom.uom', 'Unit')
    sh_unit_price = fields.Float('Unit Price')
    sh_unit_cost = fields.Float('Unit Cost')
    sh_margin = fields.Float('Margin')
    sh_margin_per = fields.Float('Margin %')
    line_id = fields.Many2one('sale.order.line')
    tf_partner_id = fields.Many2one('tf.res.partner', "Partner program")
      
    as_precio_proveedor = fields.Float(string='Precio Compra') # Precio de la ultima compra
    as_descuento = fields.Float(string='Descuento') # Descuento calculado percent_price

    price_based_usd = fields.Float('PRICE BASE USD')
    nimax_price_usd = fields.Float('Precio NIMAX')
    cost_nimax_usd = fields.Float('Costo NIMAX')
    COST_NIMAX_MXP = fields.Float('COST NIMAX MXP')

    def update_sale_line_unit_price(self):
        if self.line_id:
            # Se convierte de dolares a pesos mexicanos
            moneda_mxn = self.env.ref('base.MXN', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','MXN')], limit=1)
            moneda_usd = self.env.ref('base.USD', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','USD')], limit=1)
            price_unit = self.nimax_price_usd
            RECALCULATED_PRICE_UNIT = self.line_id.currency_id._convert_nimax(price_unit, moneda_usd, self.env.company, fields.Date.today(), self.line_id.id)
            monto_mxp = self.line_id.currency_id._convert_nimax(self.nimax_price_usd, moneda_mxn, self.env.company, fields.Date.today(), self.line_id.id)
            NIMAX_PRICE_MXP = monto_mxp
            COST_NIMAX_USD = self.line_id.currency_id._convert_nimax(self.cost_nimax_usd, moneda_usd, self.env.company, fields.Date.today(), self.line_id.id)
            COST_NIMAX_MXP = self.line_id.currency_id._convert_nimax(self.cost_nimax_usd, moneda_mxn, self.env.company, fields.Date.today(), self.line_id.id)
            MARGIN_MXP = (NIMAX_PRICE_MXP * self.line_id.product_uom_qty) - (COST_NIMAX_MXP * self.line_id.product_uom_qty)
            MARGIN_USD = (RECALCULATED_PRICE_UNIT * self.line_id.product_uom_qty) - (COST_NIMAX_USD * self.line_id.product_uom_qty)
            TOTAL_USD = RECALCULATED_PRICE_UNIT * self.line_id.product_uom_qty
            TOTAL_MXP = NIMAX_PRICE_MXP * self.line_id.product_uom_qty

            self.line_id.write({
                'price_unit': price_unit,
                'margin2': self.sh_margin,
                'as_pricelist_id': self.sh_pricelist_id.id,
                'RECALCULATED_PRICE_UNIT': RECALCULATED_PRICE_UNIT,
                'NIMAX_PRICE_MXP': NIMAX_PRICE_MXP,
                'COST_NIMAX_USD': COST_NIMAX_USD,
                'COST_NIMAX_MXP': COST_NIMAX_MXP,
                'MARGIN_MXP': MARGIN_MXP,
                'MARGIN_USD': MARGIN_USD,
                'TOTAL_USD': TOTAL_USD,
                'TOTAL_MXP': TOTAL_MXP,
                'as_log_price': True,
                                })
        
            try:
                self.env['tf.history.promo'].create({
                    'vendor_id': self.tf_partner_id.partner_id.id,
                    'product_id': self.line_id.product_id.id,
                    'customer_id': self.line_id.order_id.partner_id.id,
                    'customer_type': self.tf_partner_id.partner_type.id,
                    'as_pricelist_id': self.sh_pricelist_id.id,
                    'category_id': self.line_id.product_id.categ_id.id,
                    'qty': self.line_id.product_uom_qty,
                    'recalculated_price_unit': RECALCULATED_PRICE_UNIT,
                    'recalculated_price_unit_mxp': NIMAX_PRICE_MXP,
                    'recalculated_cost_nimax_usd': COST_NIMAX_USD,
                    'recalculated_cost_nimax_mxp': COST_NIMAX_MXP,
                    'margin_mxp': MARGIN_MXP,
                    'margin_usd': MARGIN_USD,
                    'total_usd': TOTAL_USD,
                    'total_mxp': TOTAL_MXP,
                    'salesman_id': self.line_id.order_id.user_id.id,
                    'sale_id': self.line_id.order_id.id,
                    'sale_order_line': self.line_id.id,
                })
            except Exception as e:
                _logger.warning("[update_sale_line_unit_price] Error al crear historial de promoción: %s", str(e))










