# -*- coding: utf-8 -*-

from odoo import models,fields,api
from odoo.exceptions import UserError, ValidationError

class as_res_partner(models.Model):
    _inherit="res.partner"
    
    as_partner_type = fields.Many2one('as.partner.type', string='Tipo de Cliente')

    tf_vendor_parameter_ids = fields.Many2many('tf.res.partner', string='Vendor Parameter')


    def get_pending_invoices_total(self):
        self.ensure_one()
        invoices = self.env['account.move'].search([
            ('partner_id', '=', self.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid')
        ])
      
        total_pending = sum(invoice.amount_residual for invoice in invoices)
        return total_pending

    def check_credit_limit(self, order_amount):
        self.ensure_one()
        total_pending = self.get_pending_invoices_total()
        credit_limit = self.credit_limit 
      
        if total_pending + order_amount >= credit_limit:
            raise UserError(self.sale_warn_msg)
