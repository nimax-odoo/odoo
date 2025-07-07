# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _,Command
from odoo.exceptions import UserError, ValidationError


class account_payment(models.TransientModel):
    _inherit = 'account.payment.register'
    

    sd_partner_bank_id = fields.Many2one(
        comodel_name='res.partner.bank',
        string="Cuenta Ordenante",
        readonly=False,
        store=True,
        domain="[('id', 'in', ordenante_partner_bank_ids)]",
    )
    
    ordenante_partner_bank_ids = fields.Many2many(
        comodel_name='res.partner.bank',
        compute='_compute_ordenante_partner_bank_ids',
    )
    
    @api.depends('can_edit_wizard', 'journal_id')
    def _compute_ordenante_partner_bank_ids(self):
        for wizard in self:
            batch = wizard.batches[0]
            wizard.ordenante_partner_bank_ids = wizard._get_ordenante_partner_banks(batch, wizard.journal_id)


    @api.model
    def _get_ordenante_partner_banks(self, batch_result, journal):
        company = min(batch_result['lines'].company_id, key=lambda c: len(c.sudo().parent_ids))
        # Sending money to a bank account owned by a partner.
        return batch_result['lines'].partner_id.bank_ids.filtered(lambda x: x.company_id.id in (False, company.id))._origin

    def _create_payment_vals_from_wizard(self,batch_result):
        res = super(account_payment, self)._create_payment_vals_from_wizard(batch_result)
        res.update({'sd_partner_bank_id': self.sd_partner_bank_id.id, 
                    'ordenante_partner_bank_ids': self.sd_partner_bank_id.ids})
        return res

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    sd_partner_bank_id = fields.Many2one(
        comodel_name='res.partner.bank',
        string="Cuenta Ordenante",
        readonly=False,
        store=True,
        domain="[('id', 'in', ordenante_partner_bank_ids)]",
    )
    
    ordenante_partner_bank_ids = fields.Many2many(
        comodel_name='res.partner.bank',
        compute='_compute_ordenante_partner_bank_ids',
    )
    
    @api.depends('journal_id')
    def _compute_ordenante_partner_bank_ids(self):
        for wizard in self:
            wizard.ordenante_partner_bank_ids = wizard._get_ordenante_partner_banks(wizard.journal_id)


    @api.model
    def _get_ordenante_partner_banks(self, journal):
        return self.partner_id.bank_ids.filtered(lambda x: x.company_id.id in (False, self.company_id.id))._origin
    
