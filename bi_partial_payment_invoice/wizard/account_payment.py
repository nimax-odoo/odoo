# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccontPaymentWizard(models.Model):
    _name = 'account.payment.wizard'
    _description = 'Account Payment Wizard'

    @api.model
    def default_get(self, field_vals):
        result = super(AccontPaymentWizard, self).default_get(field_vals)

        if self._context.get('payment_value'):
            payment_value = self._context.get('payment_value')

            move_id = payment_value['move_id']

            line_values = payment_value['content']

            current_line = self._context.get('line_id')

            amount = 0.00
            name = '/'

            for line in line_values:
                move_line_id = line.get('id')
                if int(current_line) == int(move_line_id):
                    amount = line.get('amount')
                    name = line.get('journal_name')
                    move_line = self.env['account.move.line'].search([('id','=',move_line_id)])
                    move = self.env['account.move'].search([('id','=',move_id)])
                    result.update({
                        'move_id': int(move_id),
                        'move_line_id': int(move_line_id),
                        'amount_total': amount or 0.00,
                        'amount_total_currency': self.tomar_monto_currency(move_line_id,move_id,amount) or 0.00,
                        'amount_residual_payment': abs(move_line.amount_residual) or 0.00,
                        'name': name
                    })
                    if move.move_type in ('in_refund', 'out_refund', 'in_receipt', 'out_receipt'):
                        result.update({
                        'amount_to_pay': move.amount_total,
                        })
                    
                    return result
        return result

    def tomar_monto_currency(self,move_line_id,move_id,amount):
        amount_payment = amount
        move_line = self.env['account.move.line'].search([('id','=',move_line_id)])
        move = self.env['account.move'].search([('id','=',move_id)])
        payment  = move_line.payment_id
        if payment:
            date = payment.date or fields.Date.context_today(self)
            if payment.currency_id != move.currency_id:
                if payment.manual_currency_rate_active:
                    
                    amount_payment = move.currency_id._convert_custom(
                        amount, payment.currency_id, payment.company_id, date,rate= payment.manual_currency_rate)
                else:
                    amount_payment = move.currency_id._convert(
                        amount, payment.currency_id, payment.company_id, date)
            else:
                amount_payment = amount
        return amount_payment


    @api.depends('amount_total', 'amount_to_pay', 'amount_residual','amount_total_currency')
    def remain_amount_(self):
        for payment in self:
            amount = payment.amount_total_currency - payment.amount_to_pay
            residual = self.tomar_monto_currency(payment.move_line_id.id,payment.move_id.id,payment.amount_residual)
            due_amount = residual - payment.amount_to_pay
            payment.amount_remain = amount or 0.00
            payment.amount_due_remain = due_amount or 0.00

    name = fields.Char('Payment Name')
    move_id = fields.Many2one('account.move', 'Account Move')
    company_id = fields.Many2one(
        'res.company', related='move_id.company_id', store=True, string='Company', readonly=False)
    company_currency_id = fields.Many2one('res.currency', string="Company Currency",
                                          related='company_id.currency_id', readonly=True, help='Utility field to express amount currency')
    amount_to_pay = fields.Monetary(string='Amount to Pay', default=0.00)
    amount_remain = fields.Monetary(
        string='Remaining Amount for Payment', store=True, readonly=True,  compute='remain_amount_')
    amount_due_remain = fields.Monetary(
        string='Remaining Amount for Invoice', store=True, readonly=True, compute='remain_amount_')
    amount_total = fields.Monetary('Amount Total', default=0.00)
    amount_total_currency = fields.Monetary('Monto Total En moneda Pago', default=0.00)
    move_line_id = fields.Many2one('account.move.line', 'Account Move Line')
    payment_id = fields.Many2one(
        'account.payment', related='move_line_id.payment_id', store=True, string='Payment')
    currency_payment = fields.Many2one('res.currency', string="Moneda del Pago", related='payment_id.currency_id',
                                  readonly=True, help='Utility field to express amount currency')
    amount_residual = fields.Monetary(string='Amount Due', store=True, readonly=True, related="move_id.amount_residual")
    amount_residual_payment = fields.Monetary(string='Monto Residual Pago', store=True, readonly=True,)
    currency_id = fields.Many2one('res.currency', string="Currency", related='move_id.currency_id',
                                  readonly=True, help='Utility field to express amount currency')
    amount_currency = fields.Monetary('Amount In Currency')

    def partial_pay(self):
        for payment in self:
            payment_move_id = payment.move_line_id.move_id
            # reset the move id
            # payment_move_id.button_draft()

            partner_id = payment.move_line_id.partner_id

            remain_payment_move_vals = {}

            if payment.payment_id:
                date = payment.payment_id.date or fields.Date.context_today(
                    self)
            else:
                date = payment_move_id.invoice_date or fields.Date.context_today(
                    self)
            
            if payment.payment_id.currency_id != payment.currency_id:
                if payment.payment_id.manual_currency_rate_active:
                    
                    residual = payment.currency_id._convert_custom(
                        payment.amount_residual, payment.payment_id.currency_id, payment.company_id, date,rate= payment.payment_id.manual_currency_rate)
                else:
                    residual = payment.currency_id._convert(
                        payment.amount_residual, payment.payment_id.currency_id, payment.company_id, date)
            else:
                residual = payment.amount_residual
                
            if payment.amount_to_pay > residual:
                raise UserError(
                    _('You can not pay more then Remaining Amount. !!!'))

            if payment.amount_remain < 0.00:
                raise UserError(
                    _('You can not pay more then Remaining Amount. !!!'))

            last_line_number = self.env.user.company_id.last_line_number

            last_line_number += 1

            if payment.payment_id.currency_id != payment.currency_id:
                if payment.payment_id.manual_currency_rate_active:
                    
                    amount_to_pay = payment.payment_id.currency_id._convert_custom(
                        payment.amount_to_pay, payment.currency_id, payment.company_id, date,rate= payment.payment_id.manual_currency_rate)
                else:
                    amount_to_pay = payment.payment_id.currency_id._convert(
                        payment.amount_to_pay, payment.currency_id, payment.company_id, date)
            else:
                amount_to_pay = payment.amount_to_pay

            if payment.payment_id:

                do_payment_move_vals = payment.payment_id.with_context(
                    amount_to_pay=payment.amount_to_pay,
                    last_line_number=last_line_number,
                    currency_id=payment.payment_id.currency_id,
                    partner_id=partner_id)._prepare_move_line_default_vals()

            if not payment.payment_id:
                if payment.currency_id != payment.company_currency_id:

                    if payment.payment_id.manual_currency_rate_active:
                        
                        amount_to_pay = payment.payment_id.currency_id._convert_custom(
                            payment.amount_to_pay, payment.currency_id, payment.company_id, date,rate= payment.payment_id.manual_currency_rate)
                    else:
                        amount_to_pay = payment.payment_id.currency_id._convert(
                            payment.amount_to_pay, payment.currency_id, payment.company_id, date)
                 
                    
                    # amount_to_pay = payment.currency_id._convert(
                    #     payment.amount_to_pay, payment.company_currency_id, payment.company_id, date)
                    
                    
                    
                    
                    amount_currency = payment.amount_to_pay
                    currency_id = payment.payment_id.currency_id.id
                else:
                    amount_to_pay = payment.amount_to_pay
                    amount_currency = 0.0
                    currency_id = False

                do_payment_move_vals = payment.with_context(
                    amount_to_pay=amount_to_pay,
                    amount_currency=amount_currency,
                    currency_id=currency_id,
                    last_line_number=last_line_number,
                    partner_id=partner_id)._prepare_move_line_default_vals()

            do_last_number = last_line_number
            if payment.move_id.move_type not in ('in_refund', 'out_refund', 'in_receipt', 'out_receipt') and payment_move_id.move_type not in ('in_refund', 'out_refund', 'in_receipt', 'out_receipt'):
                
                if payment.amount_remain:
                    last_line_number += 1
                    self.env.user.company_id.write(
                        {'last_line_number': last_line_number})
                    if payment.payment_id:
                        if payment.currency_id:
                            if payment.payment_id.manual_currency_rate_active:
                                
                                amount_remain = payment.payment_id.currency_id._convert_custom(
                                    payment.amount_remain, payment.currency_id, payment.company_id, date,rate= payment.payment_id.manual_currency_rate)
                            else:
                                amount_remain = payment.payment_id.currency_id._convert(
                                    payment.amount_remain, payment.currency_id, payment.company_id, date)
                                
                                
                                # amount_remain = payment.currency_id._convert(
                                #     payment.amount_remain, payment.company_currency_id, payment.company_id, date)
                        else:
                            amount_remain = payment.amount_remain

                        remain_payment_move_vals = payment.payment_id.with_context(
                            amount_remain=payment.amount_remain,
                            last_line_number=last_line_number,
                            currency_id=payment.payment_id.currency_id,
                            partner_id=partner_id)._prepare_move_line_default_vals()

                    if not payment.payment_id:
                        if payment.currency_id != payment.company_currency_id:
                            if payment.payment_id.manual_currency_rate_active:
                                
                                amount_remain = payment.payment_id.currency_id._convert_custom(
                                payment.amount_remain, payment.currency_id, payment.company_id, date,rate= payment.payment_id.manual_currency_rate)
                            else:
                                amount_remain = payment.payment_id.currency_id._convert(
                                    payment.amount_remain, payment.currency_id, payment.company_id, date)
                            
                            
                                # amount_remain = payment.currency_id._convert(
                                #     payment.amount_remain, payment.company_currency_id, payment.company_id, date)
                                
                            
                            
                            
                            
                            
                            amount_currency = payment.amount_remain
                            currency_id = payment.payment_id.currency_id.id
                        else:
                            amount_remain = payment.amount_remain
                            amount_currency = 0.0
                            currency_id = False

                        remain_payment_move_vals = payment.with_context(
                            amount_remain=amount_remain,
                            amount_currency=amount_currency,
                            currency_id=currency_id,
                            last_line_number=last_line_number,
                            partner_id=partner_id)._prepare_move_line_default_vals()

                else:
                    self.env.user.company_id.write(
                        {'last_line_number': last_line_number})

                line_ids = []

                payment_line_ids = payment_move_id.line_ids.filtered(
                    lambda x: not x.in_payment and (x.partner_id == partner_id))
                if payment.move_id.is_inbound():
                    payment_line_ids = payment_line_ids.filtered(lambda x: (
                        x.credit > 0 and x.debit == 0) and not x.reconciled)
                else:
                    payment_line_ids = payment_line_ids.filtered(lambda x: (
                        x.credit == 0 and x.debit > 0) and not x.reconciled)

                for line in payment_line_ids:
                    if line == payment.move_line_id:
                        line_ids.append(line.id)
                if line_ids:
                    payment_move_id.with_context(force_delete=True, check_move_validity=False, skip_account_move_synchronization=True).write(
                        {'line_ids': [(2, line) for line in line_ids]})
                new_do_payment_move_vals = []
                for payment_line in do_payment_move_vals:
                    name = payment_line.get('name')
                    payment_line.update(
                        {'name': name + " for " + str(self.move_id.name)})
                    new_do_payment_move_vals.append(payment_line)

                if len(new_do_payment_move_vals) >= 1:
                    pay_mv_id = payment_move_id.with_context(
                        check_move_validity=False, skip_account_move_synchronization=True)
                    for vals in new_do_payment_move_vals:
                        vals.update({'move_id': payment_move_id.id})
                        pay_mv_id.line_ids.create(vals)
                    if payment.move_id.is_inbound():
                        lines = pay_mv_id.line_ids.filtered(lambda x: (x.credit > 0 and x.debit == 0) and (
                            x.partner_id == partner_id) and not x.reconciled and x.last_line_number == do_last_number)
                    else:
                        lines = pay_mv_id.line_ids.filtered(lambda x: (x.credit == 0 and x.debit > 0) and (
                            x.partner_id == partner_id) and not x.reconciled and x.last_line_number == do_last_number)

                    if lines:
                        lines += payment.move_id.line_ids.filtered(
                            lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                        if payment.amount_remain:
                            if len(remain_payment_move_vals) >= 1:
                                for vals in remain_payment_move_vals:
                                    vals.update({'move_id': payment_move_id.id})
                                    pay_mv_id.line_ids.create(vals)
                        lines.with_context(
                            orignal_amount=payment.amount_to_pay).reconcile()

                    else:
                        raise UserError(
                            _('Something Went Wrong. Reset Payment and Try again.'))
            else:
                if payment_move_id.amount_total != payment.amount_to_pay:
                    raise UserError(
                        _('Se se pueden emitir pagos parciales en notas de debito credito ni recibos.'))
                if payment.move_id.is_inbound():
                    if payment_move_id.move_type == 'out_refund':
                        lines = payment_move_id.line_ids.filtered(lambda x: (x.credit > 0 and x.debit == 0) and (x.account_id == partner_id.property_account_receivable_id))
                    else:
                        lines = payment_move_id.line_ids.filtered(lambda x: (x.credit > 0 and x.debit == 0) and (x.account_id == partner_id.property_account_payable_id))
                else:
                    if payment_move_id.move_type == 'in_refund':
                        lines = payment_move_id.line_ids.filtered(lambda x: (x.credit == 0 and x.debit > 0) and (x.account_id == partner_id.property_account_payable_id))
                    else:
                        lines = payment_move_id.line_ids.filtered(lambda x: (x.credit == 0 and x.debit > 0) and (x.account_id == partner_id.property_account_receivable_id))
                lines+= payment.move_id.line_ids.filtered(
                        lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                
                lines.with_context(
                        orignal_amount=payment.amount_to_pay).reconcile()
                
                
                    
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def _prepare_move_line_default_vals(self):
        for payment in self:
            if self._context.get('amount_to_pay'):
                amount = self._context.get('amount_to_pay')
                in_payment = True
            else:
                amount = self._context.get('amount_remain')
                in_payment = False

            currency_id = self.env.company.currency_id.id
            rec_pay_line_name = payment.name or payment.move_line_id.name
            debit = credit = 0.00

            current_balance = payment.move_line_id.debit - payment.move_line_id.credit

            account_id = payment.move_line_id.account_id.id
            partner_id = self._context.get(
                'partner_id').commercial_partner_id.id

            amount_currency = self._context.get('amount_currency')
            currency_id = self._context.get('currency_id')

            if current_balance < 0.0:
                credit = amount
                debit = 0.00
                amount_currency = -amount_currency

            if current_balance > 0.0:
                credit = 0.00
                debit = amount

            line_vals_list = [

                # Receivable / Payable.
                {
                    'name': rec_pay_line_name,
                    'date_maturity': fields.Date.context_today(self),
                    'amount_currency': amount_currency,
                    'currency_id': currency_id,
                    'debit': debit,
                    'credit': credit,
                    'partner_id': partner_id or False,
                    'account_id': account_id,
                    'in_payment': in_payment,
                    'payment_id': False,
                    'last_line_number': int(self._context.get('last_line_number', 0)),
                },
            ]
            return line_vals_list
