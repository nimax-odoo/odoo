from collections import defaultdict
from contextlib import contextmanager, ExitStack
from datetime import date
import logging
import re
from odoo.tools import float_round
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, RedirectWarning
from odoo.fields import Command, Domain
from odoo.tools import frozendict, float_compare, groupby, Query, SQL, OrderedSet
from odoo.addons.web.controllers.utils import clean_action

from odoo.addons.account.models.account_move import MAX_HASH_VERSION


_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    lot_ped_ids = fields.Many2many('stock.lot', string='Lotes', compute='_compute_lot_ids')
    
    def _compute_lot_ids(self):

        for line in self:
            line.lot_ped_ids = [Command.clear()]

            if line.display_type != 'product':
                continue

            sale_lines = line.sale_line_ids

            # Nota de crédito creada desde una factura
            if not sale_lines and line.move_id.reversed_entry_id:
                origin_lines = (
                    line.move_id.reversed_entry_id.invoice_line_ids
                    .filtered(
                        lambda x: x.product_id == line.product_id
                    )
                )
                sale_lines = origin_lines.mapped('sale_line_ids')

            if not sale_lines:
                continue

            moves = sale_lines.move_ids.filtered(
                lambda m: (
                    m.state == 'done'
                    and m.product_id == line.product_id
                )
            )

            if line.move_id.move_type == 'out_refund':

                # Entregas originales
                outgoing = moves.filtered(
                    lambda m: m.location_dest_id.usage == 'customer'
                )

                # Devoluciones relacionadas
                returns = self.env['stock.move'].search([
                    ('origin_returned_move_id', 'in', outgoing.ids),
                    ('state', '=', 'done'),
                    ('location_id.usage', '=', 'customer'),
                    ('product_id', '=', line.product_id.id),
                ])

                # Líneas de lotes devueltos
                return_lines = returns.move_line_ids.filtered(
                    lambda ml: ml.lot_id
                ).sorted(lambda ml: (
                    ml.move_id.date,
                    ml.id,
                ))

                # Todas las notas de crédito de la misma venta
                refunds = sale_lines.mapped(
                    'invoice_lines'
                ).filtered(
                    lambda il: (
                        il.move_id.move_type == 'out_refund'
                        and il.move_id.state != 'cancel'
                        and il.product_id == line.product_id
                    )
                )

                # Incluir notas creadas por reversión
                original_invoices = sale_lines.mapped(
                    'invoice_lines.move_id'
                ).filtered(
                    lambda inv: inv.move_type == 'out_invoice'
                )

                reversed_refunds = self.search([
                    ('move_id.move_type', '=', 'out_refund'),
                    ('move_id.state', '!=', 'cancel'),
                    ('move_id.reversed_entry_id', 'in',
                     original_invoices.ids),
                    ('product_id', '=', line.product_id.id),
                    ('display_type', '=', 'product'),
                ])

                refunds |= reversed_refunds

                refunds = refunds.sorted(
                    lambda il: (
                        il.move_id.invoice_date
                        or il.move_id.date,
                        il.move_id.id,
                        il.id,
                    )
                )

                # Asignar lotes secuencialmente
                position = 0
                assigned = []

                for refund in refunds:

                    qty = int(float_round(
                        abs(refund.quantity),
                        precision_digits=0,
                        rounding_method='UP',
                    ))

                    current = return_lines[
                        position:position + qty
                    ]

                    if refund.id == line.id:
                        assigned = current.mapped('lot_id').ids
                        break

                    position += qty

                line.lot_ped_ids = [Command.set(assigned)]

            else:

                # Facturas normales
                outgoing = moves.filtered(
                    lambda m: (
                        m.location_dest_id.usage == 'customer'
                    )
                )

                move_lines = outgoing.move_line_ids.filtered(
                    lambda ml: ml.lot_id
                )

                line.lot_ped_ids = [
                    Command.set(move_lines.mapped('lot_id').ids)
                ]

                

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