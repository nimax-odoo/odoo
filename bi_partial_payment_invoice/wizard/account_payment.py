# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import math


class AccontPaymentWizard(models.TransientModel):
    _name = 'account.payment.wizard'
    _description = 'Account Payment Wizard'

    @api.model
    def default_get(self, field_vals):
        result = super(AccontPaymentWizard, self).default_get(field_vals)
        if self.env.context.get('move_id'):
            move_id = self.env['account.move'].browse(self.env.context.get('move_id'))
            line_id = self.env.context.get('line_id')
            move_line_id = self.env['account.move.line'].browse(line_id)
            amount_total = move_line_id.amount_residual
            if not move_id.currency_id == move_id.company_id.currency_id:
                amount_total = move_id.company_id.currency_id._convert(amount_total, move_id.currency_id, move_id.company_id, move_line_id.date)
            result.update({
                'move_id' : move_id.id,
                'move_line_id' : move_line_id.id,
                'amount_total' : abs(amount_total) or 0.00,
            })
        return result

    @api.depends('amount_total', 'amount_to_pay', 'amount_residual')
    def remain_amount_(self):
        for payment in self:
            amount = payment.amount_total - payment.amount_to_pay
            due_amount = payment.amount_residual - payment.amount_to_pay
            payment.amount_remain = amount or 0.00
            payment.amount_due_remain = due_amount or 0.00

    name = fields.Char('Payment Name')
    move_id = fields.Many2one('account.move','Account Move')
    company_id = fields.Many2one('res.company', related='move_id.company_id', store=True, string='Company', readonly=False)
    company_currency_id = fields.Many2one('res.currency', string="Company Currency", related='company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
    amount_to_pay = fields.Monetary(string='Amount to Pay', default=0.00)
    amount_remain = fields.Monetary(string='Remaining Amount for Payment', store=True, readonly=True, 
        compute='remain_amount_')
    amount_due_remain = fields.Monetary(string='Remaining Amount for Invoice', store=True, readonly=True,
        compute='remain_amount_')
    amount_total = fields.Monetary('Amount Total', default=0.00)
    move_line_id = fields.Many2one('account.move.line','Account Move Line')
    payment_id = fields.Many2one('account.payment', related='move_line_id.payment_id', store=True, string='Payment')
    amount_residual = fields.Monetary(string='Amount Due', store=True, readonly=True,
        related="move_id.amount_residual")
    currency_id = fields.Many2one('res.currency', string="Currency", related='move_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
    amount_currency = fields.Monetary('Amount In Currency')

    def partial_pay(self):
        for line in self:
            invoice_id = line.move_id
            total_pay = line.amount_to_pay or 0.0
            if not line.amount_to_pay:
                raise UserError(_('No amount for Line %s') % (line.move_id.name))

            if  line.amount_due_remain < 0:
                total_amount_due_remain = line.amount_to_pay + line.amount_due_remain
                total_amount_due_remain = math.floor(total_amount_due_remain * 100) / 100
                raise UserError(_('You can not add more than remaining amount for invoice %s') % (total_amount_due_remain))

            if  line.amount_remain < 0:
                total_amount_remain = line.amount_to_pay + line.amount_remain
                total_amount_remain = math.floor(total_amount_remain * 100) / 100
                raise UserError(_('You can not add more than remaining amount for payment %s') % (total_amount_remain))  

            move_lines = line.payment_id.move_id.line_ids.filtered(lambda line: line.account_type in ('asset_receivable', 'liability_payable') and not line.reconciled)
            if move_lines:
                for inv_line in move_lines:
                    invoice_id.with_context(amount=total_pay).js_assign_outstanding_line(inv_line.id)
            else:
                invoice_id.with_context(amount=total_pay).js_assign_outstanding_line(line.move_line_id.id)

        return {'type': 'ir.actions.client', 'tag': 'reload'}



    
