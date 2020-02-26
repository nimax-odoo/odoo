# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import date
from odoo.tools.safe_eval import safe_eval
import logging

#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class asSaleOrderPromoWizard(models.Model):
    _name = 'as.sale.order.promo.wizard'
    _description = 'Promo Wizard'

    as_pricelist_id = fields.Many2one('product.pricelist', string="Pricelist")
    promo_line = fields.One2many('as.sale.order.promo.wizard.line', 'promo_id', string='PromoLine Id')

    @api.model
    def default_get(self, fields):
        as_pricelist_id = 0  # Lista de precios de la linea de venta
        if self.env.context.get('as_pricelist_id', False):
            # print("get Context of Wizard HERE", self.env.context.get('as_pricelist_id')
            as_pricelist_id = self.env.context.get('as_pricelist_id')
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

            if 'promo_apply_dis_per' in self._context.keys():
                for promo in promos:

                    domain = safe_eval(promo.rule_products_domain)

                    # domain = tuple(domain[0])
                    _logger.debug('\n\n\n\n domain %d ', domain)
                    productos = self.env['product.product'].sudo().search(domain)
                    # productos = self.env['product.template'].sudo().search([("name","ilike","a")])
                    for producto in productos:
                        if so_line_obj.product_id.id == producto.id:
                            # promo_aprobada = {
                            #     "id": promo.id,
                            #     ""
                            # }
                            promos_aprobadas.append(promo)
                if promos_aprobadas:
                    for promo in promos_aprobadas:

                        # if promo.as_type == 'Promo Remate' and self.process_time(fields.datetime.now(),promo.rule_date_from,promo.rule_date_to):
                        if promo.as_type == 'Promo Remate':

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
                                })

                                promo_list.append(wz_line_id.id)
                        if promo.as_type == 'Promo Demo':
                        # if promo.as_type == 'Promo Demo' and self.process_time(fields.datetime.now(),promo.rule_date_from,promo.rule_date_to):
                            discount = promo.discount_fixed_amount
                            # price_unit = so_line_obj.product_id.standard_price - discount) # de precio de lista
                            price_unit = so_line_obj.product_id.standard_price - discount
                            if price_unit:
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
                                })

                                promo_list.append(wz_line_id.id)

            elif 'product_promo_apply_dis_value' in self._context.keys():
                for promo in promos:

                    domain = safe_eval(promo.rule_products_domain)

                    # domain = tuple(domain[0])
                    _logger.debug('\n\n\n\n domain %d ', domain)
                    productos = self.env['product.product'].sudo().search(domain)
                    # productos = self.env['product.template'].sudo().search([("name","ilike","a")])
                    for producto in productos:
                        if so_line_obj.product_id.id == producto.id:
                            # promo_aprobada = {
                            #     "id": promo.id,
                            #     ""
                            # }
                            promos_aprobadas.append(promo)
                if promos_aprobadas:
                    for promo in promos_aprobadas:

                        # if promo.as_type == 'Promo Remate' and self.process_time(fields.datetime.now(),promo.rule_date_from,promo.rule_date_to):
                        if promo.as_type == 'Promo Remate':

                            # discount_percentage = promo.discount_percentage
                            product_price = so_line_obj.product_id.list_price
                            # price_unit = so_line_obj.price_unit - (
                            #             (promo.discount_percentage / 100) * so_line_obj.price_unit)
                            price_unit = product_price - promo.discount_fixed_amount

                            # total_price = (promo.discount_percentage * so_line_obj.product_id.standard_price) * so_line_obj.product_uom_qty
                            # price_unit =promo._compute_price_rule([(so_line_obj.product_id, so_line_obj.product_uom_qty, so_line_obj.order_id.partner_id)], date=date.today(), uom_id=so_line_obj.product_uom.id)[so_line_obj.product_id.id][0]

                            if price_unit:
                                # margin = price_unit - so_line_obj.product_id.standard_price
                                margin_per = (100 * (price_unit - so_line_obj.product_id.standard_price)) / price_unit

                                # descuento = 0
                                # margin2 = 0
                                # if pricelist.item_ids.as_utilidad > 0:
                                #     descuento = (1-(so_line_obj.product_id.as_last_purchase_price/(1-pricelist.item_ids.as_utilidad/100)))*100
                                #     price_unit = so_line_obj.product_id.list_price *(1-descuento/100)
                                #     margin2 = price_unit * (pricelist.item_ids.as_utilidad / 100)
                                wz_line_id = self.env['as.sale.order.promo.wizard.line'].create({
                                    'sh_promo_id': promo.id,
                                    'sh_unit_price': price_unit,
                                    # 'sh_unit_measure':so_line_obj.product_uom.id,
                                    # 'sh_unit_cost':so_line_obj.product_id.standard_price,
                                    # 'sh_margin': margin,
                                    # 'sh_margin_per': margin_per,
                                    'line_id': so_line,
                                    # 'as_precio_proveedor':so_line_obj.product_id.as_last_purchase_price,
                                    # 'as_descuento': discount_percentage,
                                    "tf_dis_amount": price_unit
                                })

                                promo_list.append(wz_line_id.id)
                        if promo.as_type == 'Promo Demo':
                            # if promo.as_type == 'Promo Demo' and self.process_time(fields.datetime.now(),promo.rule_date_from,promo.rule_date_to):
                            discount = promo.discount_fixed_amount
                            # price_unit = so_line_obj.product_id.standard_price - discount) # de precio de lista
                            price_unit = so_line_obj.product_id.standard_price - discount
                            if price_unit:
                                wz_line_id = self.env['as.sale.order.promo.wizard.line'].create({
                                    'sh_promo_id': promo.id,
                                    'sh_unit_price': price_unit,
                                    # 'sh_unit_measure':so_line_obj.product_uom.id,
                                    # 'sh_unit_cost':so_line_obj.product_id.standard_price,
                                    # 'sh_margin': margin,
                                    # 'sh_margin_per': margin_per,
                                    'line_id': so_line,
                                    # 'as_precio_proveedor':so_line_obj.product_id.as_last_purchase_price,
                                    # 'as_descuento': discount,
                                    "tf_dis_amount": price_unit
                                })

                                promo_list.append(wz_line_id.id)


            elif 'prduct_promo_apply_dis_per' in self._context.keys():
                for promo in promos:

                    domain = safe_eval(promo.rule_products_domain)

                    # domain = tuple(domain[0])
                    _logger.debug('\n\n\n\n domain %d ', domain)
                    productos = self.env['product.product'].sudo().search(domain)
                    # productos = self.env['product.template'].sudo().search([("name","ilike","a")])
                    for producto in productos:
                        if so_line_obj.product_id.id == producto.id:
                            # promo_aprobada = {
                            #     "id": promo.id,
                            #     ""
                            # }
                            promos_aprobadas.append(promo)
                if promos_aprobadas:
                    for promo in promos_aprobadas:

                        # if promo.as_type == 'Promo Remate' and self.process_time(fields.datetime.now(),promo.rule_date_from,promo.rule_date_to):
                        if promo.as_type == 'Promo Remate':

                            discount_percentage = promo.discount_percentage
                            price_unit = so_line_obj.product_id.list_price - ((promo.discount_percentage/100) * so_line_obj.product_id.list_price)
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
                                })

                                promo_list.append(wz_line_id.id)
                        if promo.as_type == 'Promo Demo':
                        # if promo.as_type == 'Promo Demo' and self.process_time(fields.datetime.now(),promo.rule_date_from,promo.rule_date_to):
                            discount = promo.discount_fixed_amount
                            # price_unit = so_line_obj.product_id.standard_price - discount) # de precio de lista
                            price_unit = so_line_obj.product_id.standard_price - discount
                            if price_unit:
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
                                })

                                promo_list.append(wz_line_id.id)


            # by sachin
            new_promo = []
            sale_id = so_line_obj.order_id
            for tfpromo in promo_list:
                wiz_promo = self.env['as.sale.order.promo.wizard.line'].browse(tfpromo)
                if wiz_promo.sh_promo_id.rule_partners_domain and wiz_promo.sh_promo_id.rule_products_domain and wiz_promo.sh_promo_id.rule_date_from and wiz_promo.sh_promo_id.rule_date_to:
                    customer_domain = safe_eval(wiz_promo.sh_promo_id.rule_partners_domain)
                    customer_domain.append(["id","=",sale_id.partner_id.id])
                    customer = self.env['res.partner'].search(customer_domain)
                    product_domain = safe_eval(wiz_promo.sh_promo_id.rule_products_domain)
                    product_domain.append(('id','=',so_line_obj.product_id.id))
                    product = self.env['product.product'].search(product_domain)

                    if str(wiz_promo.sh_promo_id.rule_date_from.date()) < str(sale_id.date_order) < str(wiz_promo.sh_promo_id.rule_date_to.date()) and customer and product:
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

    def update_sale_line_unit_price_promo(self):
        if self.line_id:
            self.line_id.write({
                'price_unit': self.sh_unit_price,
                'margin2': self.sh_margin,
            })
