# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import date, time
from odoo.tools.safe_eval import safe_eval
import logging

#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class asSaleOrderPromoWizard(models.Model):
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

            # Filtrar por lista de precios
            # promos = self.env['sale.coupon.program'].sudo().search([('as_price_list','=',int(as_pricelist_id))])

            # Usar el domain de la promocion para filtrar promos
            promos_aprobadas = []
            promos = self.env['sale.coupon.program'].sudo().search([('active', '=', True)])

            # if 'promo_apply_dis_per' in self._context.keys():
            for promo in promos:

                domain = safe_eval(promo.rule_products_domain)

                # domain = tuple(domain[0])
                _logger.debug('\n\n\n\n domain %s ', domain)
                productos = self.env['product.product'].sudo().search(domain)
                # productos = self.env['product.template'].sudo().search([("name","ilike","a")])
                for producto in productos:
                    if so_line_obj.product_id.id == producto.id:
                        promos_aprobadas.append(promo)

            if promos_aprobadas:
                for promo in promos_aprobadas:

                    # if promo.as_type == 'Promo Remate' and self.process_time(fields.datetime.now(),promo.rule_date_from,promo.rule_date_to):
                    if promo.as_type == 'DEAL':

                        discount_percentage = promo.discount_percentage
                        price_unit = so_line_obj.price_unit - ((promo.discount_percentage/100) * so_line_obj.price_unit)
                        # total_price = (promo.discount_percentage * so_line_obj.product_id.standard_price) * so_line_obj.product_uom_qty
                        # price_unit =promo._compute_price_rule([(so_line_obj.product_id, so_line_obj.product_uom_qty, so_line_obj.order_id.partner_id)], date=date.today(), uom_id=so_line_obj.product_uom.id)[so_line_obj.product_id.id][0]

                        if price_unit:
                            # margin = price_unit - so_line_obj.product_id.standard_price
                            margin_per = (100 * (price_unit - so_line_obj.product_id.standard_price))/price_unit

                            # descuento = 0
                            # margin2 = 0
                            # if pricelist.item_ids.as_utilidad > 0:
                            #     descuento = (1-(so_line_obj.product_id.as_last_purchase_price/(1-pricelist.item_ids.as_utilidad/100)))*100
                            #     price_unit = so_line_obj.product_id.list_price *(1-descuento/100)
                            #     margin2 = price_unit * (pricelist.item_ids.as_utilidad / 100)

                            C47 = so_line_obj.price_unit
                            C48 = so_line_obj.product_id.list_price
                            C49 = so_line_obj.COST_NIMAX_USD
                            G46 = discount_percentage

                            wz_line_id = self.env['as.sale.order.promo.wizard.line'].create({
                                'sh_promo_id': promo.id,
                                'sh_unit_price': price_unit,
                                # 'sh_unit_measure':so_line_obj.product_uom.id,
                                # 'sh_unit_cost':so_line_obj.product_id.standard_price,
                                # 'sh_margin': margin,
                                # 'sh_margin_per': margin_per,
                                'line_id': so_line,
                                # 'as_precio_proveedor':so_line_obj.product_id.as_last_purchase_price,
                                'as_descuento': discount_percentage,
                                'RECALCULATED_PRICE_UNIT': C47-(C48*G46/100),
                                'RECALCULATED_COST_NIMAX_USD': C49-(C48*G46/100),
                            })

                            promo_list.append(wz_line_id.id)
                    if promo.as_type == 'DEMO':
                    # if promo.as_type == 'Promo Demo' and self.process_time(fields.datetime.now(),promo.rule_date_from,promo.rule_date_to):
                        discount = promo.discount_fixed_amount
                        discount_percentage = promo.discount_percentage
                        # price_unit = so_line_obj.product_id.standard_price - discount) # de precio de lista
                        price_unit = so_line_obj.product_id.standard_price - discount
                        if price_unit:
                            C57 = so_line_obj.price_unit
                            C58 = so_line_obj.product_id.list_price
                            C59 = so_line_obj.COST_NIMAX_USD
                            G55 = discount_percentage
                            wz_line_id = self.env['as.sale.order.promo.wizard.line'].create({
                                'sh_promo_id': promo.id,
                                'sh_unit_price': price_unit,
                                # 'sh_unit_measure':so_line_obj.product_uom.id,
                                # 'sh_unit_cost':so_line_obj.product_id.standard_price,
                                # 'sh_margin': margin,
                                # 'sh_margin_per': margin_per,
                                'line_id': so_line,
                                # 'as_precio_proveedor':so_line_obj.product_id.as_last_purchase_price,
                                'as_descuento': discount,
                                'RECALCULATED_PRICE_UNIT': (C58-(C58*G55/100)),
                                'RECALCULATED_COST_NIMAX_USD': C59-(C58*G55/100),
                            })

                            promo_list.append(wz_line_id.id)

                    if promo.as_type == 'ESPECIAL':
                        discount = promo.discount_fixed_amount
                        wz_line_id = self.env['as.sale.order.promo.wizard.line'].create({
                            'sh_promo_id': promo.id,
                            # 'sh_unit_price': price_unit,
                            # 'sh_unit_measure':so_line_obj.product_uom.id,
                            # 'sh_unit_cost':so_line_obj.product_id.standard_price,
                            # 'sh_margin': margin,
                            # 'sh_margin_per': margin_per,
                            'line_id': so_line,
                            # 'as_precio_proveedor':so_line_obj.product_id.as_last_purchase_price,
                            'as_descuento': discount,
                            'RECALCULATED_PRICE_UNIT': promo.PRICE_UNIT_USD,
                            'RECALCULATED_COST_NIMAX_USD': promo.COST_NIMAX_USD,
                        })

                        promo_list.append(wz_line_id.id)

                    if promo.as_type == 'FABRICANTE':
                        discount = promo.discount_fixed_amount
                        wz_line_id = self.env['as.sale.order.promo.wizard.line'].create({
                            'sh_promo_id': promo.id,
                            # 'sh_unit_price': price_unit,
                            # 'sh_unit_measure':so_line_obj.product_uom.id,
                            # 'sh_unit_cost':so_line_obj.product_id.standard_price,
                            # 'sh_margin': margin,
                            # 'sh_margin_per': margin_per,
                            'line_id': so_line,
                            # 'as_precio_proveedor':so_line_obj.product_id.as_last_purchase_price,
                            'as_descuento': discount,
                            'RECALCULATED_PRICE_UNIT': so_line_obj.price_unit - promo.DISCOUNT_AMOUNT_USD,
                            'RECALCULATED_COST_NIMAX_USD': so_line_obj.COST_NIMAX_USD - promo.DISCOUNT_AMOUNT_USD,
                        })

                        promo_list.append(wz_line_id.id)

            # by sachin
            new_promo = []
            sale_id = so_line_obj.order_id
            for tfpromo in promo_list:
                wiz_promo = self.env['as.sale.order.promo.wizard.line'].browse(tfpromo)
                # if wiz_promo.sh_promo_id.rule_partners_domain\
                #         and wiz_promo.sh_promo_id.rule_products_domain\
                #         and wiz_promo.sh_promo_id.rule_date_from\
                #         and wiz_promo.sh_promo_id.rule_date_to:
                check = True
                if wiz_promo.sh_promo_id.rule_partners_domain:
                    customer_domain = safe_eval(wiz_promo.sh_promo_id.rule_partners_domain)
                    customer_domain.append(["id","=",sale_id.partner_id.id])
                    customer = self.env['res.partner'].search(customer_domain)
                    if not customer:
                        check = False
                if check and wiz_promo.sh_promo_id.rule_products_domain:
                    product_domain = safe_eval(wiz_promo.sh_promo_id.rule_products_domain)
                    product_domain.append(('id','=',so_line_obj.product_id.id))
                    product = self.env['product.product'].search(product_domain)
                    if not product:
                        check = False
                # if check and not wiz_promo.sh_promo_id.rule_date_from:
                #     check = False
                # if check and not wiz_promo.sh_promo_id.rule_date_to:
                #     check = False
                if check and wiz_promo.sh_promo_id.rule_date_from and str(wiz_promo.sh_promo_id.rule_date_from.date()) >= str(sale_id.date_order):
                    check = False
                if check and wiz_promo.sh_promo_id.rule_date_to and str(sale_id.date_order) >= str(wiz_promo.sh_promo_id.rule_date_to.date()):
                    check = False
                if check:
                    new_promo.append(wiz_promo.id)
            # end


            res.update({

                # 'promo_line': [(6, 0, promo_list)],
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

class as_SaleOrderPromoWizardLine(models.Model):
    _name = 'as.sale.order.promo.wizard.line'
    _description = 'Promo Wizard'

    promo_id = fields.Many2one('as.sale.order.promo.wizard', "Promo Id")
    sh_promo_id = fields.Many2one(
        'sale.coupon.program', "Promo", required=True)
    # sh_unit_measure = fields.Many2one('uom.uom','Unit')
    sh_unit_price = fields.Float('Unit Price')
    # sh_unit_cost = fields.Float('Unit Cost')
    sh_margin = fields.Float('Margin')
    sh_margin_per = fields.Float('Margin %')
    line_id = fields.Many2one('sale.order.line')

    # Descuento calculado percent_price
    as_descuento = fields.Float(string='Descuento')
    tf_dis_amount = fields.Float('Discounted price')
    PRICE_UNIT_USD = fields.Float('PRICE UNIT USD')
    COST_NIMAX_USD = fields.Float('COST NIMAX USD')

    RECALCULATED_PRICE_UNIT = fields.Float('Precio Unitario')
    RECALCULATED_COST_NIMAX_USD = fields.Float('Costo NIMAX USD')

    def update_sale_line_unit_price_promo(self):
        if self.line_id:
            data_update = {
                'price_unit': self.sh_unit_price,
                'margin2': self.sh_margin,
                'coupon_ids': [(4, self.sh_promo_id.id)]
            }
            if self.sh_promo_id.as_type == 'DEAL':
                data_update.update({
                    'price_unit': self.line_id.price_unit,
                    'RECALCULATED_PRICE_UNIT': self.RECALCULATED_PRICE_UNIT,
                    'RECALCULATED_COST_NIMAX_USD': self.RECALCULATED_COST_NIMAX_USD,
                })
            elif self.sh_promo_id.as_type == 'DEMO':
                data_update.update({
                    'price_unit': self.line_id.price_unit,
                    'RECALCULATED_PRICE_UNIT': self.RECALCULATED_PRICE_UNIT,
                    'RECALCULATED_COST_NIMAX_USD': self.RECALCULATED_COST_NIMAX_USD,
                })

                gift_id = self.env['tf.gift.coupon.program'].search([('coupon_id', '=', self.sh_promo_id.id),
                                                           ('name', '=', self.sh_promo_id.as_type)], limit=1)
                if gift_id:
                    gift_id.gifted_qty += 1
            elif self.sh_promo_id.as_type == 'ESPECIAL':
                data_update.update({
                    'price_unit': self.line_id.price_unit,
                    'RECALCULATED_PRICE_UNIT': self.RECALCULATED_PRICE_UNIT,
                    'RECALCULATED_COST_NIMAX_USD': self.RECALCULATED_COST_NIMAX_USD,
                })
                gift_id = self.env['tf.gift.coupon.program'].search([('coupon_id', '=', self.sh_promo_id.id),
                                                                     ('name', '=', self.sh_promo_id.as_type)])
                if gift_id:
                    gift_id.gifted_qty += 1
            elif self.sh_promo_id.as_type == 'FABRICANTE':
                data_update.update({
                    'price_unit': self.line_id.price_unit,
                    'RECALCULATED_PRICE_UNIT': self.RECALCULATED_PRICE_UNIT,
                    'RECALCULATED_COST_NIMAX_USD': self.RECALCULATED_COST_NIMAX_USD,
                })
            data_update.update({
                'price_unit': self.RECALCULATED_PRICE_UNIT,
            })
            self.line_id.write(data_update)
