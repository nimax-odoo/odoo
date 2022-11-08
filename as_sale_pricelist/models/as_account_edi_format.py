from odoo import fields, api, models, _
from odoo.exceptions import UserError, RedirectWarning
from datetime import datetime
import pytz
import base64
from pytz import timezone


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'
    
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

