# -*- coding: utf-8 -*-

from odoo import models,fields,api
    
class AccountMove(models.Model):
    _inherit = "account.move"
    
    def action_post(self):
        #heredada para registrar historico de promo de la venta en caso d enota de credito
        res = super(AccountMove, self).action_post()
        if self.move_type in ['out_refund']:
            sale_id = self.env['sale.order'].sudo()
            for line in self.invoice_line_ids:
                if line.sale_line_ids:
                    sale_id = line.sale_line_ids[0].order_id
                    break
            if sale_id:
                histotico = self.env['tf.history.promo'].sudo().search([('sale_id', '=', sale_id.id),('last_applied_promo', '=', True)])
                for hosto in histotico:
                    hosto.copy()
                    hosto.recalculated_price_unit = hosto.recalculated_price_unit*-1
                    hosto.recalculated_price_unit_mxp = hosto.recalculated_price_unit_mxp*-1
                    hosto.recalculated_cost_nimax_usd = hosto.recalculated_cost_nimax_usd*-1
                    hosto.recalculated_cost_nimax_mxp = hosto.recalculated_cost_nimax_mxp*-1
                    hosto.margin_mxp = hosto.margin_mxp*-1
                    hosto.margin_usd = hosto.margin_usd*-1
                    hosto.total_usd = hosto.total_usd*-1
                    hosto.total_mxp = hosto.total_mxp*-1
                    hosto.move_credit_id = self.id
                    
        return res
    
    