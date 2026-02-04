from collections import defaultdict
from contextlib import contextmanager, ExitStack
from datetime import date
import logging
import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, RedirectWarning
from odoo.fields import Command, Domain
from odoo.tools import frozendict, float_compare, groupby, Query, SQL, OrderedSet
from odoo.addons.web.controllers.utils import clean_action

from odoo.addons.account.models.account_move import MAX_HASH_VERSION


_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def _create_exchange_difference_moves(self, exchange_diff_values_list):
        """ HEREDADA POR COMPLETO POR ERROR EN CODIGO ORIGINAL DE ODOO 19
        """
        # early return to prevent endless recursive computation of reconcile plan
        if not exchange_diff_values_list:
            return self.env['account.move']

        exchange_move_values_list = []
        journal_ids = set()
        for exchange_diff_values in exchange_diff_values_list:
            move_vals = exchange_diff_values['move_values']
            exchange_move_values_list.append(move_vals)

            if not move_vals['journal_id']:
                raise UserError(_(
                    "You have to configure the 'Exchange Gain or Loss Journal' in your company settings, to manage"
                    " automatically the booking of accounting entries related to differences between exchange rates."
                ))

            journal_ids.add(move_vals['journal_id'])

        # ==== Check the config ====
        journals = self.env['account.journal'].browse(list(journal_ids))
        for journal in journals:
            if not journal.company_id.expense_currency_exchange_account_id:
                raise UserError(_(
                    "You should configure the 'Loss Exchange Rate Account' in your company settings, to manage"
                    " automatically the booking of accounting entries related to differences between exchange rates."
                ))
            if not journal.company_id.income_currency_exchange_account_id.id:
                raise UserError(_(
                    "You should configure the 'Gain Exchange Rate Account' in your company settings, to manage"
                    " automatically the booking of accounting entries related to differences between exchange rates."
                ))

        # ==== Create the moves ====
        exchange_moves = self.env['account.move'].with_context(no_exchange_difference=True).create(exchange_move_values_list)
        # The reconciliation of exchange moves is now dealt thanks to the reconciled_lines_ids field

        # ==== See if the exchange moves need to be posted or not ====
        exchange_moves_to_post = self.env['account.move']
        for exchange_move, vals in zip(exchange_moves, exchange_diff_values_list):
            if 'to_post' in vals and vals['to_post']: #aca se hizo el cambio
                exchange_moves_to_post |= exchange_move

        if exchange_moves_to_post:
            exchange_moves_to_post._post(soft=False)

        return exchange_moves