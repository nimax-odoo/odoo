# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
class SaleOrder(models.Model):
    _inherit="sale.order" 

    def cancel_expired_quotations(self):
        """
        Cancels all expired sales orders by changing their state to 'cancel'.

        """
        expired_sales_orders = self.find_expired_quotations()
       
        batch_size = 400 
        for batch_start in range(0, len(expired_sales_orders), batch_size):
            batch_end = min(batch_start + batch_size, len(expired_sales_orders))
            batch = expired_sales_orders[batch_start:batch_end]
   
            [order.write({'state': 'cancel'}) for order in batch]
        

        
 
    def find_expired_quotations(self):
        """
        Finds all sales orders that have been in the draft state for 1 month or more.

        :return: A list of sale.order records that have expired.
        """
       
        draft_sales_orders = self.env['sale.order'].search([
            ('state', '=', 'draft'),
            ('validity_date', '!=', False)
        ])
  
        expired_sales_orders = [order for order in draft_sales_orders if self.has_expired(order)]
       
        return expired_sales_orders

    
    def has_expired(self, sale_order):
        """
        Checks if the sale order's validity date has expired based on a configured number of days.

        :param sale_order: sale.order record
        :return: True if the sale order has expired, False otherwise
        """
        # Get the configured number of days for expiration
        expiration_days = int(self.env['ir.config_parameter'].sudo().get_param('bi_website_shop_product_filter.quotation_expiration_days'))
        validity_date = sale_order.validity_date

        if validity_date:
            current_date = datetime.now().date()
            days_since_validity = (current_date - validity_date).days

            # Check if the number of days since the validity date is greater than or equal to the configured expiration days
            return days_since_validity >= expiration_days
        else:
            return False
        


class SaleConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    quotation_expiration_days = fields.Integer(string="Días de validez de la cotización", default=0)

        
    def set_values(self):
        super(SaleConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('bi_website_shop_product_filter.quotation_expiration_days', self.quotation_expiration_days)

    @api.model
    def get_values(self):
        res = super(SaleConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(quotation_expiration_days = str(params.get_param('bi_website_shop_product_filter.quotation_expiration_days', default=0)))
        return res
    
    def set_values(self):
        super(SaleConfigSettings,self).set_values()
        ir_parameter = self.env['ir.config_parameter'].sudo()        
        ir_parameter.set_param('bi_website_shop_product_filter.quotation_expiration_days', self.quotation_expiration_days)

        
