# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccontMultiPaymentWizard(models.TransientModel):
    _name = 'account.multi.payment.wizard'
    _description = 'Account Multiple Payment Wizard'

    @api.model
    def default_get(self, field_vals):
        result = super(AccontMultiPaymentWizard, self).default_get(field_vals)
        if self._context.get('default_partner_type'):
            if self._context.get('default_partner_type') == 'customer':
                result.update({
                    'payment_type' : 'payin'
                })
            else:
                result.update({
                    'payment_type' : 'payout'
                })

        return result

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for payment in self:
            payment.update({
                'move_line_id' : False,
            })

    @api.onchange('partner_type')
    def _onchange_partner_id(self):
        for payment in self:
            if payment.partner_type == "customer":
                payment.update({'payment_type' : 'payin'})
            else:
                payment.update({'payment_type' : 'payout'})


    @api.onchange('move_line_id', 'partner_id')
    def _onchange_payment_id(self):
        for payment in self:
            payment.update({
                'move_lines_ids' : self.env['multi.move.line']
            })


    @api.depends('move_line_id','move_lines_ids',
        'move_lines_ids.amount_to_pay')
    def compute_payable_amt(self):
        for payment in self:
            amount_residual_currency = amount_residual = 0.0
            remain_amount = remain_amount_currency = 0.0
                
            move_line_id = payment.move_line_id
            transfer_currency_id = payment.currency_id

            if move_line_id:
                amount_residual = abs(move_line_id.amount_residual)
                amount_residual_currency = abs(move_line_id.amount_residual_currency)
            
            if payment.move_lines_ids:
                for line in payment.move_lines_ids:
                    if transfer_currency_id:
                        currency_id = payment.currency_id
                        company_currency_id =  payment.company_currency_id
                        # if line.is_comapany:
                        #     converted_amount = currency_id._convert(\
                        #         line.curr_amount_to_pay, company_currency_id, payment.company_id, \
                        #         fields.Date.context_today(self))
                        #     remain_amount += converted_amount
                        #     remain_amount_currency += line.curr_amount_to_pay
                    else:
                        remain_amount += line.amount_to_pay
            remain_amount -= amount_residual
            remain_amount_currency -= amount_residual_currency 

            payment.update({
                'amount_residual' : abs(amount_residual),
                'amount_residual_currency' : abs(amount_residual_currency),
                'remain_amount_currency' : abs(remain_amount_currency),
                'remain_amount' : abs(remain_amount)
            })

    partner_id = fields.Many2one('res.partner', string='Partner')
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')])
    payment_type = fields.Selection([('payin', 'Customer Payment'), ('payout', 'Vendor Payment')], string='Payment Type', required=True, default='payin')
    move_line_id = fields.Many2one('account.move.line', 'Customer/Vendor Payment Line')
    company_id = fields.Many2one('res.company', related='move_line_id.company_id', store=True, string='Company', readonly=False)
    company_currency_id = fields.Many2one('res.currency', string="Company Currency", related='company_id.currency_id', store=True,help='Utility field to express amount currency')
    currency_id = fields.Many2one('res.currency', string="Currency", related='move_line_id.currency_id', readonly=True, store=True,help='Utility field to express amount currency')
    amount_residual = fields.Monetary('Residual Amount', compute="compute_payable_amt", store=True, currency_field="company_currency_id")
    amount_residual_currency = fields.Monetary('Currency Residual Amount', compute="compute_payable_amt", store=True, currency_field="currency_id")
    remain_amount = fields.Monetary('Remain Amount', compute="compute_payable_amt",store=True, currency_field="company_currency_id")
    remain_amount_currency = fields.Monetary('Remain Currency Amount', compute="compute_payable_amt", store=True, currency_field="currency_id")
    move_lines_ids = fields.One2many('multi.move.line', 'multi_payment_id',string='Multiple Payments',)


    def multi_partial_pay(self):
        payment_id = self.move_line_id.payment_id
        for line in self.move_lines_ids:
            if line.amount_residual >= line.amount_to_pay:
                if line.pay_remaining_amount >= line.amount_to_pay:
                    invoice_id = line.invoice_id
                    total_pay = line.amount_to_pay or 0.0
                    if not line.amount_to_pay:
                        raise UserError(_('No amount for Line %s') % (line.invoice_id.name))
                    move_lines = payment_id.move_id.line_ids.filtered(lambda line: line.account_type in ('asset_receivable', 'liability_payable') and not line.reconciled)
                    if move_lines:
                        for inv_line in move_lines:
                            invoice_id.with_context(amount=total_pay).js_assign_outstanding_line(inv_line.id)
                    else:
                        invoice_id.with_context(amount=total_pay).js_assign_outstanding_line(line.id)
                else:
                    raise UserError(_('You can not pay more than Remaining Amount'))
            else:
                raise UserError(_('You can not pay more than Remaining Amount'))
        return {'type': 'ir.actions.client', 'tag': 'reload'}


class MultiMoveLine(models.TransientModel):
    _name = 'multi.move.line'
    _description = 'Account Multiple Payment Wizard'

    multi_payment_id = fields.Many2one('account.multi.payment.wizard', string='Payment Wizard') 
    move_line_id = fields.Many2one('account.move.line', string='Move Line')
    invoice_id = fields.Many2one('account.move', string='Account Move')
    partner_id = fields.Many2one('res.partner', string='Partner', related="multi_payment_id.partner_id")
    company_id = fields.Many2one('res.company', related='invoice_id.company_id', store=True, string='Company', readonly=False)
    currency_id = fields.Many2one('res.currency', string="Currency", related='invoice_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
    payment_type = fields.Selection(related='multi_payment_id.payment_type', string="Payment Type", store=True, readonly=True)
    amount_total = fields.Monetary(string='Amount Total', related="invoice_id.amount_total",currency_field='currency_id')
    amount_residual = fields.Monetary(string='Remaining Amount',related="invoice_id.amount_residual", readonly=True, default=0.00, currency_field='currency_id')
    amount_to_pay = fields.Monetary(string='Amount to Pay', default=0.00, currency_field='currency_id')
    pay_remaining_amount = fields.Monetary(string='Remaining Amount Of Payment', default=0.00, currency_field='currency_id')


    @api.onchange('invoice_id')
    def compute_order_amount(self):
        for multi_line in self:
            payment_curr_id = multi_line.multi_payment_id.currency_id
            pay_date = (
                multi_line.multi_payment_id.move_line_id.payment_id.date
                if multi_line.multi_payment_id.move_line_id.payment_id
                else fields.Date.context_today(self)
            )
            payment_remaining_amount = multi_line.multi_payment_id.amount_residual
            payment_currency_id = multi_line.multi_payment_id.currency_id

            if multi_line.currency_id == multi_line.multi_payment_id.currency_id:
                multi_line.pay_remaining_amount = payment_remaining_amount
            else:
                rate = self.env['res.currency']._get_conversion_rate(payment_currency_id,multi_line.currency_id , multi_line.company_id, pay_date)
                multi_line.pay_remaining_amount =  payment_currency_id._convert(payment_remaining_amount, multi_line.currency_id,multi_line.company_id,pay_date)


