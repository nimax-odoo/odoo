# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields,models,api
from datetime import date

#from odoo.exceptions import UserError


class SaleOrderPricelistWizard(models.Model):
    _name = 'sale.order.pricelist.wizard'
    _description = 'Pricelist Wizard'
    
    shs_pricelist_id = fields.Many2one('product.pricelist',string="Pricelist")
    pricelist_line = fields.One2many('sale.order.pricelist.wizard.line','pricelist_id',string='PricelistLine Id')
    
    @api.model
    def default_get(self, fields):
        res = super(SaleOrderPricelistWizard, self).default_get(fields)
        res_ids = self._context.get('active_ids')
        if res_ids[0]:
            so_line = res_ids[0]
            so_line_obj = self.env['sale.order.line'].browse(so_line)
            pricelist_list = []
            pricelists = self.env['product.pricelist'].sudo().search([])
            if pricelists:
                for pricelist in pricelists:
                    price_unit =pricelist._compute_price_rule([(so_line_obj.product_id, so_line_obj.product_uom_qty, so_line_obj.order_id.partner_id)], date=date.today(), uom_id=so_line_obj.product_uom.id)[so_line_obj.product_id.id][0]
                    if price_unit:
                        margin = price_unit - so_line_obj.product_id.standard_price
                        margin_per = (100 * (price_unit - so_line_obj.product_id.standard_price))/price_unit
                        
                        descuento = 0
                        margin2 = 0
                        if pricelist.item_ids.as_utilidad > 0:
                            descuento = (1-(so_line_obj.product_id.as_last_purchase_price/(1-pricelist.item_ids.as_utilidad/100)))*100
                            price_unit = so_line_obj.product_id.list_price *(1-descuento/100)
                            margin2 = price_unit * (pricelist.item_ids.as_utilidad / 100)
                        wz_line_id = self.env['sale.order.pricelist.wizard.line'].create({'sh_pricelist_id' :pricelist.id,
                                                                                    'sh_unit_price':price_unit,
                                                                                    'sh_unit_measure':so_line_obj.product_uom.id,
                                                                                    'sh_unit_cost':so_line_obj.product_id.standard_price,
                                                                                    'sh_margin':margin2,
                                                                                    'sh_margin_per':margin_per,
                                                                                    'line_id': so_line,
                                                                                    'as_precio_proveedor':so_line_obj.product_id.as_last_purchase_price,
                                                                                    'as_descuento':descuento,
                                                                                    })
                        
                        pricelist_list.append(wz_line_id.id)
            res.update({
                
                'pricelist_line':[(6,0,pricelist_list)],
            })
        return res
        
        
        
class SaleOrderPricelistWizardLine(models.Model):
    _name = 'sale.order.pricelist.wizard.line'
    _description = 'Pricelist Wizard'
    
    pricelist_id = fields.Many2one('sale.order.pricelist.wizard',"Pricelist Id")
    sh_pricelist_id = fields.Many2one('product.pricelist',"Pricelist",required=True)
    sh_unit_measure = fields.Many2one('uom.uom','Unit')
    sh_unit_price = fields.Float('Unit Price')
    sh_unit_cost = fields.Float('Unit Cost')
    sh_margin = fields.Float('Margin')
    sh_margin_per = fields.Float('Margin %')
    line_id =fields.Many2one('sale.order.line')
      
    as_precio_proveedor = fields.Float(string='Precio Compra') # Precio de la ultima compra
    # as_precio_nimax = fields.Float(string='Precio NIMAX') # Precio de venta Nimax
    # as_utilidad = fields.Float(string='Utilidad') # Utilidad esperada
    as_descuento = fields.Float(string='Descuento') # Descuento calculado percent_price
    # as_precio_final = fields.Float(string='Precio de Venta Final')
    # as_product_id = fields.Many2one('product.product', string='Product ID',  required=True, ondelete='cascade', index=True, copy=False)      
      
    def update_sale_line_unit_price(self):
        if self.line_id:
            self.line_id.write({
                'price_unit':self.sh_unit_price,
                'margin2':self.sh_margin,
                                })
        
