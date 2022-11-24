from odoo import fields, api, models, _
from odoo.exceptions import UserError, RedirectWarning
from datetime import datetime
import pytz
import base64
from pytz import timezone


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_mx_edi_get_invoice_cfdi_values(self, invoice):
        res = super(AccountEdiFormat, self)._l10n_mx_edi_get_invoice_cfdi_values(invoice)
        if invoice.currency_id.name == 'MXN':
            res['currency_conversion_rate'] = None
        else:  # assumes that invoice.company_id.country_id.code == 'MX', as checked in '_is_required_for_invoice'
            # res['currency_conversion_rate'] = abs(invoice.amount_total_signed) / abs(invoice.amount_total) if invoice.amount_total else 1.0

            ctx = dict(company_id=invoice.company_id.id, date=invoice.invoice_date)
            mxn = self.env.ref('base.MXN').with_context(ctx)
            invoice_currency = invoice.currency_id.with_context(ctx)
            res['currency_conversion_rate']  = round(invoice_currency._convert(1, mxn, invoice.company_id, invoice.invoice_date or fields.Date.today(), round=False),6) if invoice.currency_id.name != 'MXN' else 1.0
        return res

    def _is_compatible_with_journal(self, journal):
        # OVERRIDE
        self.ensure_one()
        if self.code != 'cfdi_3_3':
            return super()._is_compatible_with_journal(journal)
        return journal.type == 'sale' and journal.country_code == 'MX' 


    def _is_required_for_invoice(self, invoice):
        # OVERRIDE
        self.ensure_one()
        if self.code != 'cfdi_3_3':
            return super()._is_required_for_invoice(invoice)

        # Determine on which invoices the Mexican CFDI must be generated.
        return invoice.move_type in ('out_invoice', 'out_refund') and \
            invoice.country_code == 'MX'

