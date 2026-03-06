# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
import base64
from collections import defaultdict
from werkzeug.urls import url_encode, url_quote_plus
from markupsafe import escape as html_escape
import traceback
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz
from odoo.tools.float_utils import float_is_zero, float_round
from odoo.tools.float_utils import float_round
_logger = logging.getLogger(__name__)
from odoo.addons.l10n_mx_edi.models.l10n_mx_edi_document import (
    CANCELLATION_REASON_SELECTION,
    CANCELLATION_REASON_DESCRIPTION,
    CFDI_CODE_TO_TAX_TYPE,
    CFDI_DATE_FORMAT,
    USAGE_SELECTION,
)
from odoo.tools import format_list, frozendict
from odoo.tools.float_utils import float_round
from odoo.tools.sql import column_exists, create_column
from odoo.addons.base.models.ir_qweb import keep_query
import re
# Configurar logger más específico para debugging
_debug_logger = logging.getLogger(__name__ + ".debug")
_debug_logger.setLevel(logging.DEBUG)

class AsAccountInvoice(models.Model):
    _inherit = "account.move"

    def _l10n_mx_edi_is_cfdi_document(self):
        """ reemplazada porque la compania no tiene la moneda en MXN
        """
        self.ensure_one()
        return self.country_code == 'MX' 
    
    def sd_l10n_mx_edi_cfdi_try_sat(self):
        for inv in self:
            inv.l10n_mx_edi_cfdi_try_sat()
        
    def _l10n_mx_edi_cfdi_payment_get_reconciled_invoice_values(self):
        """ Compute the amounts to send to the PAC from the current payments.

        :return: A mapping payment => dictionary containing:
            * invoices:         The reconciled invoices.
            * invoice_results:  A list of payment values, see '_l10n_mx_edi_cfdi_invoice_get_reconciled_payments_values'.
        """
        # Find all invoices linked to the current payments.
        results = {}
        payments = self.filtered(lambda x: x._l10n_mx_edi_is_cfdi_payment() and x.l10n_mx_edi_cfdi_state != 'cancel')
        all_invoices = self.env['account.move']
        exchange_move_map = {}
        exchange_move_balances = defaultdict(lambda: defaultdict(lambda: 0.0))
        for payment in payments:
            # Only the fully reconciled payments need to be sent.
            pay_rec_lines = payment.line_ids\
                .filtered(lambda line: line.account_type in ('asset_receivable', 'liability_payable'))
            if any(not x.reconciled for x in pay_rec_lines):
                continue

            # The payments must only be sent when all reconciled invoices are sent.
            skip = False
            invoices = self.env['account.move']
            for field in ('debit', 'credit'):
                for partial in pay_rec_lines[f'matched_{field}_ids'].sorted(lambda x: not x.exchange_move_id):
                    counterpart_line = partial[f'{field}_move_id']
                    counterpart_move = counterpart_line.move_id
                    if counterpart_move.journal_id.type == 'sale':
                        if counterpart_move in exchange_move_map:
                            exchange_move_balances[payment][exchange_move_map[counterpart_move]] += partial.amount
                            continue

                        if not counterpart_move.is_invoice() or not counterpart_move.l10n_mx_edi_cfdi_state:
                            skip = True
                            break

                        if partial.exchange_move_id:
                            exchange_move_map[partial.exchange_move_id] = counterpart_move

                        invoices |= counterpart_move

            if skip:
                continue

            all_invoices |= invoices

            reconciled_amls = pay_rec_lines.matched_debit_ids.debit_move_id \
                              + pay_rec_lines.matched_credit_ids.credit_move_id
            invoices = reconciled_amls.move_id.filtered(lambda x: x.l10n_mx_edi_is_cfdi_needed and x.is_invoice())
            if any(
                not invoice.l10n_mx_edi_cfdi_state
                for invoice in invoices
            ):
                continue

            all_invoices |= invoices
            results[payment] = {
                'invoices': invoices,
                'invoice_results': [],
            }

        # Compute the amounts to send for each invoice.
        reconciled_invoice_values = all_invoices._l10n_mx_edi_cfdi_invoice_get_reconciled_payments_values()
        for invoice, pay_results_list in reconciled_invoice_values.items():
            for pay_results in pay_results_list:
                payment = pay_results['payment']
                if payment not in results:
                    continue

                pay_results['payment_exchange_balance'] = exchange_move_balances[payment][invoice]

                results[payment]['invoice_results'].append(pay_results)

        return results
  
    def detectar_moneda(self,moneda, invoices):
        igual = True
        for inv in invoices:
            if inv.currency_id == moneda:
                igual = True
            else:
                igual = False
        return igual
    
    def _l10n_mx_edi_add_payment_cfdi_values(self, cfdi_values, pay_results):
        """ Prepare the values to render the payment cfdi.

        :param cfdi_values: Prepared cfdi_values.
        :param pay_results: The amounts to consider for each invoice.
                            See '_l10n_mx_edi_cfdi_payment_get_reconciled_invoice_values'.
        :return: The dictionary to render the xml.
        """
        self.ensure_one()
        Document = self.env['l10n_mx_edi.document']

        self._l10n_mx_edi_add_common_cfdi_values(cfdi_values)
        company = cfdi_values['company']
        company_curr = self.env['res.currency'].search([('name', '=', 'MXN')],limit=1)

        # Misc.
        cfdi_values['exportacion'] = '01'
        cfdi_values['forma_de_pago'] = (self.l10n_mx_edi_payment_method_id.code or '').replace('NA', '01').replace('99', '01')
        cfdi_values['moneda'] = self.currency_id.name
        cfdi_values['num_operacion'] = self.ref

        # Amounts.
        #parche para pagos en caso de la moneda d ela compañia ser diferente a MXN
        total_in_payment_curr = sum(x['payment_amount_currency'] for x in pay_results['invoice_results'])
        total_in_company_curr = sum(x['balance'] + x['payment_exchange_balance'] for x in pay_results['invoice_results'])
        # total_in_company_curr = self.converter_curr_mxn(total_in_company_curr)
        cambio = 1
        is_usd = False
        if self.currency_id == company_curr:
            if self.company_id.currency_id.name == 'MXN':
                cfdi_values['monto'] = total_in_company_curr
            else:
                cfdi_values['monto'] = total_in_payment_curr
                cambio = total_in_payment_curr/total_in_company_curr
                total_in_company_curr = total_in_company_curr * cambio
                
        else:
            cfdi_values['monto'] = total_in_payment_curr
            if self.detectar_moneda(self.currency_id,  pay_results['invoices']):
                cambio = 1
                if self.currency_id.name == 'USD':
                    is_usd = True
            else:
                if self.origin_payment_id.manual_currency_rate_active:
                    cambio = self.origin_payment_id.manual_currency_rate
                else:
                    cambio = company_curr.rate
            total_in_company_curr = total_in_company_curr * cambio

        # Exchange rate.
        # 'tipo_cambio' is a conditional attribute used to express the exchange rate of the currency on the date the
        # payment was made.
        # The value must reflect the number of Mexican pesos that are equivalent to a unit of the currency indicated
        # in the 'moneda' attribute.
        # It is required when the MonedaP attribute is different from MXN.
        cfdi_values['tipo_cambio_dp'] = 6
        if self.currency_id == company_curr:
            payment_rate = None
        else:
            raw_payment_rate = abs(total_in_company_curr / total_in_payment_curr) if total_in_payment_curr else 0.0
            payment_rate = float_round(raw_payment_rate, precision_digits=cfdi_values['tipo_cambio_dp'])

            # Finkok/SwSapien CRP20211: MontoTotalPagos must be exactly equal to round(total_in_payment_curr * payment_rate)
            if cfdi_values['root_company'].l10n_mx_edi_pac in {'finkok', 'sw'}:
                total_in_company_curr = company_curr.round(total_in_payment_curr * payment_rate)

        if is_usd:
            if self.origin_payment_id.manual_currency_rate_active:
                inverse_change = self.origin_payment_id.manual_currency_rate
            else:
                inverse_change = company_curr.rate
            payment_rate = float_round(inverse_change, precision_digits=cfdi_values['tipo_cambio_dp'])
            total_in_company_curr = total_in_company_curr * payment_rate
        cfdi_values.update({
            'tipo_cambio': payment_rate,
            'monto_total_pagos': total_in_company_curr,
            'mxn_digits': company_curr.decimal_places,
        })

        # === Create the list of invoice data ===
        invoice_values_list = []
        for invoice_values in pay_results['invoice_results']:
            invoice = invoice_values['invoice']

            inv_cfdi_values = Document._get_company_cfdi_values(invoice.company_id)
            Document._add_certificate_cfdi_values(inv_cfdi_values)
            invoice._l10n_mx_edi_add_invoice_cfdi_values(inv_cfdi_values)

            # Apply the percentage paid to the tax amounts.
            if invoice.amount_total:
                percentage_paid = abs(invoice_values['reconciled_amount'] / invoice.amount_total)
            else:
                percentage_paid = 0.0
            for key in (
                'retenciones_list',
                'traslados_list',
                'local_traslados_list',
                'local_retenciones_list',
            ):
                for tax_values in inv_cfdi_values[key]:
                    for tax_key in ('base', 'importe'):
                        if tax_values[tax_key] is not None:
                            tax_values[tax_key] = invoice.currency_id.round(tax_values[tax_key] * percentage_paid)

                    # Handle the case where the rounding method was changed between Odoo versions.
                    # This applies when an invoice's CFDI, generated in the previous version, is processed
                    # after the upgrade in the new version, resulting in the use of a deprecated rounding method.
                    if all(tax_values[key] is not None for key in ('base', 'importe', 'tasa_o_cuota')):
                        post_amounts_map = self.env['l10n_mx_edi.document']._get_post_fix_tax_amounts_map(
                            base_amount=tax_values['base'],
                            tax_amount=tax_values['importe'],
                            tax_rate=tax_values['tasa_o_cuota'],
                            precision_digits=invoice.currency_id.decimal_places,
                        )
                        tax_values['importe'] = post_amounts_map['new_tax_amount']
                        tax_values['base'] = post_amounts_map['new_base_amount']

            # 'equivalencia' (rate) is a conditional attribute used to express the exchange rate according to the currency
            # registered in the document related. It is required when the currency of the related document is different
            # from the payment currency.
            # The number of units of the currency must be recorded indicated in the related document that are
            # equivalent to a unit of the currency of the payment.
            def calculate_rate(invoice_amount, payment_amount):
                if not payment_amount:
                    return 0.0
                return abs(invoice_amount / payment_amount)

            if invoice.currency_id == self.currency_id:
                # Same currency.
                computed_rate = None
            elif invoice.currency_id == company_curr != self.currency_id:
                # Adapt the payment rate to find the reconciled amount of the invoice but expressed in payment currency.
                balance = (invoice_values['balance'] + invoice_values['invoice_exchange_balance']) * cambio
                computed_rate = calculate_rate(balance,invoice_values['payment_amount_currency'])
            elif self.currency_id == company_curr != invoice.currency_id:
                # Adapt the invoice rate to find the reconciled amount of the payment but expressed in invoice currency.
                balance = (invoice_values['balance'] + invoice_values['payment_exchange_balance']) * cambio
                computed_rate = calculate_rate(invoice_values['invoice_amount_currency'], balance)
            else:
                # Both are expressed in different currencies.
                computed_rate = calculate_rate(invoice_values['invoice_amount_currency'], invoice_values['payment_amount_currency'])
            currency_precision = company_curr.l10n_mx_edi_decimal_places
            if self.currency_id == company_curr:
                if self.company_id.currency_id.name != 'MXN':
                    currency_precision = 6
            def format_float_custom(amount, precision=currency_precision):
                if amount is None or amount is False:
                    return None
                # Avoid things like -0.0, see: https://stackoverflow.com/a/11010869
                amount = float_round(amount, precision_digits=precision)
                return '%.*f' % (precision, amount if not float_is_zero(amount, precision_digits=precision) else 0.0)
            # 'objeto_imp' has to be set on the invoice but is computed for each lines.
            all_tax_objected = {line['objeto_imp'] for line in inv_cfdi_values['conceptos_list']}
            all_tax_objected.discard('04')
            objeto_imp = all_tax_objected.pop() if len(all_tax_objected) == 1 else '02'
            
            invoice_values_list.append({
                **inv_cfdi_values,
                'objeto_imp': objeto_imp or '02',
                'id_documento': invoice.l10n_mx_edi_cfdi_uuid,
                'equivalencia': computed_rate,
                'inv_rate': computed_rate,
                'num_parcialidad': invoice_values['number_of_payments'],
                'imp_pagado': invoice_values['reconciled_amount'],
                'imp_saldo_ant': invoice_values['amount_residual_before'],
                'imp_saldo_insoluto': invoice_values['amount_residual_after'],
                'format_float_custom': format_float_custom,
            })
        cfdi_values['docto_relationado_list'] = invoice_values_list
        
        # Customer.
        rfcs = set(x['receptor']['rfc'] for x in invoice_values_list)
        if len(rfcs) > 1:
            cfdi_values['errors'] = [_("You can't register a payment for invoices having different RFCs.")]
            return

        customer_values = invoice_values_list[0]['receptor']
        customer = customer_values['customer']
        cfdi_values['receptor'] = customer_values
        cfdi_values['lugar_expedicion'] = cfdi_values['issued_address'].zip

        # Date.
        cfdi_date = datetime.combine(fields.Datetime.from_string(self.date), datetime.strptime('12:00:00', '%H:%M:%S').time())
        cfdi_values['fecha'] = Document._get_datetime_now_with_mx_timezone(cfdi_values, journal=self.journal_id).strftime(CFDI_DATE_FORMAT)
        cfdi_values['fecha_pago'] = cfdi_date.strftime(CFDI_DATE_FORMAT)

        # Bank information.
        payment_method_code = self.l10n_mx_edi_payment_method_id.code
        is_payment_code_emitter_ok = payment_method_code in ('02', '03', '04', '05', '06', '28', '29', '99')
        is_payment_code_receiver_ok = payment_method_code in ('02', '03', '04', '05', '28', '29', '99')
        is_payment_code_bank_ok = payment_method_code in ('02', '03', '04', '28', '29', '99')

        bank_account = customer.bank_ids.filtered(lambda x: x.company_id.id in (False, company.id))[:1]

        partner_bank = bank_account.bank_id
        if partner_bank.country and partner_bank.country.code != 'MX':
            partner_bank_vat = 'XEXX010101000'
        else:  # if no partner_bank (e.g. cash payment), partner_bank_vat is not set.
            partner_bank_vat = partner_bank.l10n_mx_edi_vat

        payment_account_ord = re.sub(r'\s+', '', bank_account.acc_number or '') or None
        for pay in self.payment_ids:
            if pay.sd_partner_bank_id:
                payment_account_ord = re.sub(r'\s+', '', pay.sd_partner_bank_id.acc_number or '') or None

        payment_account_receiver = re.sub(r'\s+', '', self.journal_id.bank_account_id.acc_number or '') or None

        cfdi_values.update({
            'rfc_emisor_cta_ord': is_payment_code_emitter_ok and partner_bank_vat,
            'nom_banco_ord_ext': is_payment_code_bank_ok and partner_bank.name,
            'cta_ordenante': is_payment_code_emitter_ok and payment_account_ord,
            'rfc_emisor_cta_ben': is_payment_code_receiver_ok and self.journal_id.bank_account_id.bank_id.l10n_mx_edi_vat,
            'cta_beneficiario': is_payment_code_receiver_ok and payment_account_receiver,
        })

        # Taxes.
        def update_tax_amount(key, amount):
            if key not in cfdi_values:
                cfdi_values[key] = 0.0
            cfdi_values[key] += amount

        def check_transferred_tax_values(tax_values, tag, tax_class, amount):
            return (
                tax_values['impuesto'] == tag
                and tax_values['tipo_factor'] == tax_class
                and company_curr.compare_amounts(tax_values['tasa_o_cuota'] or 0.0, amount) == 0
            )
        
        withholding_values_map = defaultdict(lambda: {'importe': 0.0})
        transferred_values_map = defaultdict(lambda: {'base': 0.0, 'importe': 0.0})
        local_retenciones_values_map = defaultdict(lambda: {'base': 0.0, 'importe': 0.0})
        local_traslados_values_map = defaultdict(lambda: {'base': 0.0, 'importe': 0.0})
        pay_rate = cfdi_values['tipo_cambio'] or 1.0
        for cfdi_inv_values in invoice_values_list:
            inv_rate = round(cfdi_inv_values.pop('inv_rate', False) or 1.0,10)
            to_mxn_rate = pay_rate / inv_rate
            for result_dict, key in (
                (withholding_values_map, 'retenciones_list'),
                (local_retenciones_values_map, 'local_retenciones_list'),
            ):
                for tax_values in cfdi_inv_values[key]:
                    tax_key = frozendict({
                        'impuesto': tax_values['impuesto'],
                        'tipo_factor': tax_values['tipo_factor'],
                        'tasa_o_cuota': tax_values['tasa_o_cuota'],
                        # 'local_tax_name': tax_values['local_tax_name'],
                    })
                    result_dict[tax_key]['importe'] += tax_values['importe'] / inv_rate

                    tax_amount_mxn = tax_values['importe'] * to_mxn_rate
                    if tax_values['impuesto'] == '001':
                        update_tax_amount('total_retenciones_isr', tax_amount_mxn)
                    elif tax_values['impuesto'] == '002':
                        update_tax_amount('total_retenciones_iva', tax_amount_mxn)
                    elif tax_values['impuesto'] == '003':
                        update_tax_amount('total_retenciones_ieps', tax_amount_mxn)

            for result_dict, key in (
                (transferred_values_map, 'traslados_list'),
                (local_traslados_values_map, 'local_traslados_list'),
            ):
                for tax_values in cfdi_inv_values[key]:
                    tax_key = frozendict({
                        'impuesto': tax_values['impuesto'],
                        'tipo_factor': tax_values['tipo_factor'],
                        'tasa_o_cuota': tax_values['tasa_o_cuota'],
                        # 'local_tax_name': tax_values['local_tax_name'],
                    })
                    tax_amount = tax_values['importe'] or 0.0

                    if self.currency_id == company_curr:
                        if self.company_id.currency_id.name == 'MXN':
                            result_dict[tax_key]['base'] += tax_values['base'] / inv_rate
                            result_dict[tax_key]['importe'] += tax_amount / inv_rate
                            base_amount_mxn = tax_values['base'] * to_mxn_rate
                            tax_amount_mxn = tax_amount * to_mxn_rate
                        else:
                            montos = self.extraer_montos_decimales(tax_values)
                            tax_values['base'] = montos[0]
                            result_dict[tax_key]['base'] += round(montos[0] / inv_rate,6)
                            result_dict[tax_key]['importe'] += round(montos[1] / inv_rate,6)
                            base_amount_mxn = round(montos[0] * to_mxn_rate,6)
                            tax_amount_mxn = round(montos[1] * to_mxn_rate,6)
                            tax_values['importe'] = montos[1]
                            
                            
                    else:
                        result_dict[tax_key]['base'] += tax_values['base'] / inv_rate
                        result_dict[tax_key]['importe'] += tax_amount / inv_rate
                        base_amount_mxn = company_curr.round(tax_values['base'] / inv_rate)*inv_rate
                        tax_amount_mxn = company_curr.round(tax_amount  / inv_rate)*inv_rate
                    
                    
                    if check_transferred_tax_values(tax_values, '002', 'Tasa', 0.0):
                        update_tax_amount('total_traslados_base_iva0', base_amount_mxn)
                        update_tax_amount('total_traslados_impuesto_iva0', tax_amount_mxn)
                    elif check_transferred_tax_values(tax_values, '002', 'Exento', 0.0):
                        update_tax_amount('total_traslados_base_iva_exento', base_amount_mxn)
                    elif check_transferred_tax_values(tax_values, '002', 'Tasa', 0.08):
                        update_tax_amount('total_traslados_base_iva8', base_amount_mxn)
                        update_tax_amount('total_traslados_impuesto_iva8', tax_amount_mxn)
                    elif check_transferred_tax_values(tax_values, '002', 'Tasa', 0.16):
                        if is_usd:
                            update_tax_amount('total_traslados_base_iva16', base_amount_mxn*to_mxn_rate)
                            update_tax_amount('total_traslados_impuesto_iva16', tax_amount_mxn*to_mxn_rate)
                        else:
                            update_tax_amount('total_traslados_base_iva16', base_amount_mxn)
                            update_tax_amount('total_traslados_impuesto_iva16', tax_amount_mxn)
            
        # Rounding global tax amounts.
        for dictionary in (
            withholding_values_map,
            transferred_values_map,
            local_retenciones_values_map,
            local_traslados_values_map,
        ):
            for values in dictionary.values():
                if 'base' in values:
                    values['base'] = self.currency_id.round(values['base'])
                values['importe'] = self.currency_id.round(values['importe'])

        for key in (
            'total_traslados_base_iva0',
            'total_traslados_impuesto_iva0',
            'total_traslados_base_iva_exento',
            'total_traslados_base_iva8',
            'total_traslados_impuesto_iva8',
            'total_traslados_base_iva16',
            'total_traslados_impuesto_iva16',
            'total_retenciones_isr',
            'total_retenciones_iva',
            'total_retenciones_ieps',
        ):
            if key in cfdi_values:
                cfdi_values[key] = company_curr.round(cfdi_values[key])
            else:
                cfdi_values[key] = None

        for target_key, source_dict in (
            ('retenciones_list', withholding_values_map),
            ('traslados_list', transferred_values_map),
            ('local_retenciones_list', local_retenciones_values_map),
            ('local_traslados_list', local_traslados_values_map),
        ):
            cfdi_values[target_key] = [
                {**k, **v}
                for k, v in source_dict.items()
            ]

        # Cleanup attributes for Exento taxes.
        for key in (
            'traslados_list',
            'local_traslados_list',
        ):
            for tax_values in cfdi_values[key]:
                if tax_values['tipo_factor'] == 'Exento':
                    tax_values['importe'] = None


        
    def extraer_montos_decimales(self,tax_values):
        total = tax_values['base']+tax_values['importe']
        base = round(total/(1+tax_values['tasa_o_cuota']),6)
        impuesto = round(base*tax_values['tasa_o_cuota'],6)
        return (base,impuesto)

    # def _l10n_mx_edi_add_payment_cfdi_values(self, cfdi_values, pay_results):
    #     """ Prepare the values to render the payment cfdi.

    #     :param cfdi_values: Prepared cfdi_values.
    #     :param pay_results: The amounts to consider for each invoice.
    #                         See '_l10n_mx_edi_cfdi_payment_get_reconciled_invoice_values'.
    #     :return: The dictionary to render the xml.
    #     """
    #     self.ensure_one()
    #     Document = self.env['l10n_mx_edi.document']

    #     self._l10n_mx_edi_add_common_cfdi_values(cfdi_values)
    #     company = cfdi_values['company']
    #     company_curr = self.env['res.currency'].search([('name', '=', 'MXN')],limit=1)

    #     # Misc.
    #     cfdi_values['exportacion'] = '01'
    #     cfdi_values['forma_de_pago'] = (self.l10n_mx_edi_payment_method_id.code or '').replace('NA', '01').replace('99', '01')
    #     cfdi_values['moneda'] = self.currency_id.name
    #     cfdi_values['num_operacion'] = self.ref

    #     # Amounts.
    #     total_in_payment_curr = sum(x['payment_amount_currency'] for x in pay_results['invoice_results'])
    #     total_in_company_curr = sum(x['balance'] + x['payment_exchange_balance'] for x in pay_results['invoice_results'])
    #     if self.currency_id == company_curr:
    #         cfdi_values['monto'] = total_in_payment_curr
    #     else:
    #         cfdi_values['monto'] = total_in_company_curr

    #     # Exchange rate.
    #     # 'tipo_cambio' is a conditional attribute used to express the exchange rate of the currency on the date the
    #     # payment was made.
    #     # The value must reflect the number of Mexican pesos that are equivalent to a unit of the currency indicated
    #     # in the 'moneda' attribute.
    #     # It is required when the MonedaP attribute is different from MXN.
    #     cfdi_values['tipo_cambio_dp'] = 6
    #     if self.currency_id == company_curr:
    #         payment_rate = None
    #     else:
    #         raw_payment_rate = abs(company_curr.rate) if total_in_payment_curr else 0.0
    #         payment_rate = float_round(raw_payment_rate, precision_digits=cfdi_values['tipo_cambio_dp'])

    #         # Finkok/SwSapien CRP20211: MontoTotalPagos must be exactly equal to round(total_in_payment_curr * payment_rate)
    #         if cfdi_values['root_company'].l10n_mx_edi_pac in {'finkok', 'sw'}:
    #             total_in_company_curr = company_curr.round(total_in_payment_curr)

    #     cfdi_values.update({
    #         'tipo_cambio': payment_rate,
    #         'monto_total_pagos': cfdi_values['monto'],
    #         'mxn_digits': company_curr.decimal_places,
    #     })

    #     # === Create the list of invoice data ===
    #     invoice_values_list = []
    #     for invoice_values in pay_results['invoice_results']:
    #         invoice = invoice_values['invoice']

    #         inv_cfdi_values = Document._get_company_cfdi_values(invoice.company_id)
    #         Document._add_certificate_cfdi_values(inv_cfdi_values)
    #         invoice._l10n_mx_edi_add_invoice_cfdi_values(inv_cfdi_values)

    #         # Apply the percentage paid to the tax amounts.
    #         if invoice.amount_total:
    #             percentage_paid = abs(invoice_values['reconciled_amount'] / invoice.amount_total)
    #         else:
    #             percentage_paid = 0.0
    #         for key in (
    #             'retenciones_list',
    #             'traslados_list',
    #             'local_traslados_list',
    #             'local_retenciones_list',
    #         ):
    #             for tax_values in inv_cfdi_values[key]:
    #                 for tax_key in ('base', 'importe'):
    #                     if tax_values[tax_key] is not None:
    #                         tax_values[tax_key] = invoice.currency_id.round(tax_values[tax_key] * percentage_paid)

    #                 # Handle the case where the rounding method was changed between Odoo versions.
    #                 # This applies when an invoice's CFDI, generated in the previous version, is processed
    #                 # after the upgrade in the new version, resulting in the use of a deprecated rounding method.
    #                 if all(tax_values[key] is not None for key in ('base', 'importe', 'tasa_o_cuota')):
    #                     post_amounts_map = self.env['l10n_mx_edi.document']._get_post_fix_tax_amounts_map(
    #                         base_amount=tax_values['base'],
    #                         tax_amount=tax_values['importe'],
    #                         tax_rate=tax_values['tasa_o_cuota'],
    #                         precision_digits=invoice.currency_id.decimal_places,
    #                     )
    #                     tax_values['importe'] = post_amounts_map['new_tax_amount']
    #                     tax_values['base'] = post_amounts_map['new_base_amount']

    #         # 'equivalencia' (rate) is a conditional attribute used to express the exchange rate according to the currency
    #         # registered in the document related. It is required when the currency of the related document is different
    #         # from the payment currency.
    #         # The number of units of the currency must be recorded indicated in the related document that are
    #         # equivalent to a unit of the currency of the payment.
    #         def calculate_rate(invoice_amount, payment_amount):
    #             if not payment_amount:
    #                 return 0.0
    #             return abs(invoice_amount / payment_amount)

    #         if invoice.currency_id == self.currency_id:
    #             # Same currency.
    #             computed_rate = None
    #         elif invoice.currency_id == company_curr != self.currency_id:
    #             # Adapt the payment rate to find the reconciled amount of the invoice but expressed in payment currency.
    #             balance = invoice_values['balance'] + invoice_values['invoice_exchange_balance']
    #             computed_rate = calculate_rate(balance, invoice_values['payment_amount_currency'])
    #         elif self.currency_id == company_curr != invoice.currency_id:
    #             # Adapt the invoice rate to find the reconciled amount of the payment but expressed in invoice currency.
    #             balance = invoice_values['balance'] + invoice_values['payment_exchange_balance']
    #             computed_rate = calculate_rate(invoice_values['invoice_amount_currency'], balance)
    #         else:
    #             # Both are expressed in different currencies.
    #             computed_rate = calculate_rate(invoice_values['invoice_amount_currency'], invoice_values['payment_amount_currency'])
    #         monto_mxn = invoice_values['reconciled_amount']
    #         if self.currency_id != company_curr:
    #             monto_mxn = invoice_values['reconciled_amount'] / payment_rate 
    #             computed_rate = payment_rate
    #         invoice_values_list.append({
    #             **inv_cfdi_values,
    #             'id_documento': invoice.l10n_mx_edi_cfdi_uuid,
    #             'equivalencia': computed_rate,
    #             'inv_rate': computed_rate,
    #             'num_parcialidad': invoice_values['number_of_payments'],
    #             'imp_pagado': monto_mxn,
    #             'imp_saldo_ant': invoice_values['amount_residual_before']/payment_rate,
    #             'imp_saldo_insoluto': invoice_values['amount_residual_after']/payment_rate,
    #         })
    #     cfdi_values['docto_relationado_list'] = invoice_values_list

    #     # Customer.
    #     rfcs = set(x['receptor']['rfc'] for x in invoice_values_list)
    #     if len(rfcs) > 1:
    #         cfdi_values['errors'] = [_("You can't register a payment for invoices having different RFCs.")]
    #         return

    #     customer_values = invoice_values_list[0]['receptor']
    #     customer = customer_values['customer']
    #     cfdi_values['receptor'] = customer_values
    #     cfdi_values['lugar_expedicion'] = cfdi_values['issued_address'].zip

    #     # Date.
    #     cfdi_date = datetime.combine(fields.Datetime.from_string(self.date), datetime.strptime('12:00:00', '%H:%M:%S').time())
    #     cfdi_values['fecha'] = Document._get_datetime_now_with_mx_timezone(cfdi_values, journal=self.journal_id).strftime(CFDI_DATE_FORMAT)
    #     cfdi_values['fecha_pago'] = cfdi_date.strftime(CFDI_DATE_FORMAT)

    #     # Bank information.
    #     payment_method_code = self.l10n_mx_edi_payment_method_id.code
    #     is_payment_code_emitter_ok = payment_method_code in ('02', '03', '04', '05', '06', '28', '29', '99')
    #     is_payment_code_receiver_ok = payment_method_code in ('02', '03', '04', '05', '28', '29', '99')
    #     is_payment_code_bank_ok = payment_method_code in ('02', '03', '04', '28', '29', '99')

    #     bank_account = customer.bank_ids.filtered(lambda x: x.company_id.id in (False, company.id))[:1]

    #     partner_bank = bank_account.bank_id
    #     if partner_bank.country and partner_bank.country.code != 'MX':
    #         partner_bank_vat = 'XEXX010101000'
    #     else:  # if no partner_bank (e.g. cash payment), partner_bank_vat is not set.
    #         partner_bank_vat = partner_bank.l10n_mx_edi_vat

    #     payment_account_ord = re.sub(r'\s+', '', bank_account.acc_number or '') or None
    #     payment_account_receiver = re.sub(r'\s+', '', self.journal_id.bank_account_id.acc_number or '') or None

    #     cfdi_values.update({
    #         'rfc_emisor_cta_ord': is_payment_code_emitter_ok and partner_bank_vat,
    #         'nom_banco_ord_ext': is_payment_code_bank_ok and partner_bank.name,
    #         'cta_ordenante': is_payment_code_emitter_ok and payment_account_ord,
    #         'rfc_emisor_cta_ben': is_payment_code_receiver_ok and self.journal_id.bank_account_id.bank_id.l10n_mx_edi_vat,
    #         'cta_beneficiario': is_payment_code_receiver_ok and payment_account_receiver,
    #     })

    #     # Taxes.
    #     def update_tax_amount(key, amount):
    #         if key not in cfdi_values:
    #             cfdi_values[key] = 0.0
    #         cfdi_values[key] += amount

    #     def check_transferred_tax_values(tax_values, tag, tax_class, amount):
    #         return (
    #             tax_values['impuesto'] == tag
    #             and tax_values['tipo_factor'] == tax_class
    #             and company_curr.compare_amounts(tax_values['tasa_o_cuota'] or 0.0, amount) == 0
    #         )

    #     withholding_values_map = defaultdict(lambda: {'importe': 0.0})
    #     transferred_values_map = defaultdict(lambda: {'base': 0.0, 'importe': 0.0})
    #     local_retenciones_values_map = defaultdict(lambda: {'base': 0.0, 'importe': 0.0})
    #     local_traslados_values_map = defaultdict(lambda: {'base': 0.0, 'importe': 0.0})
    #     pay_rate = cfdi_values['tipo_cambio'] or 1.0
    #     for cfdi_inv_values in invoice_values_list:
    #         inv_rate = cfdi_inv_values.pop('inv_rate', False) or 1.0
    #         if self.currency_id == company_curr:
    #             to_mxn_rate = pay_rate / inv_rate
    #         else:
    #             to_mxn_rate = 1 / inv_rate
    #         for result_dict, key in (
    #             (withholding_values_map, 'retenciones_list'),
    #             (local_retenciones_values_map, 'local_retenciones_list'),
    #         ):
    #             for tax_values in cfdi_inv_values[key]:
    #                 tax_key = frozendict({
    #                     'impuesto': tax_values['impuesto'],
    #                     'tipo_factor': tax_values['tipo_factor'],
    #                     'tasa_o_cuota': tax_values['tasa_o_cuota'],
    #                     'local_tax_name': tax_values['local_tax_name'],
    #                 })
    #                 result_dict[tax_key]['importe'] += tax_values['importe'] / inv_rate

    #                 tax_amount_mxn = tax_values['importe'] * to_mxn_rate
    #                 if tax_values['impuesto'] == '001':
    #                     update_tax_amount('total_retenciones_isr', tax_amount_mxn)
    #                 elif tax_values['impuesto'] == '002':
    #                     update_tax_amount('total_retenciones_iva', tax_amount_mxn)
    #                 elif tax_values['impuesto'] == '003':
    #                     update_tax_amount('total_retenciones_ieps', tax_amount_mxn)

    #         for result_dict, key in (
    #             (transferred_values_map, 'traslados_list'),
    #             (local_traslados_values_map, 'local_traslados_list'),
    #         ):
    #             for tax_values in cfdi_inv_values[key]:
    #                 tax_key = frozendict({
    #                     'impuesto': tax_values['impuesto'],
    #                     'tipo_factor': tax_values['tipo_factor'],
    #                     'tasa_o_cuota': tax_values['tasa_o_cuota'],
    #                     'local_tax_name': tax_values['local_tax_name'],
    #                 })
    #                 tax_amount = tax_values['importe'] or 0.0
    #                 result_dict[tax_key]['base'] += tax_values['base'] / inv_rate
    #                 result_dict[tax_key]['importe'] += tax_amount / inv_rate

    #                 base_amount_mxn = tax_values['base'] * to_mxn_rate
    #                 tax_amount_mxn = tax_amount * to_mxn_rate
    #                 if check_transferred_tax_values(tax_values, '002', 'Tasa', 0.0):
    #                     update_tax_amount('total_traslados_base_iva0', base_amount_mxn)
    #                     update_tax_amount('total_traslados_impuesto_iva0', tax_amount_mxn)
    #                 elif check_transferred_tax_values(tax_values, '002', 'Exento', 0.0):
    #                     update_tax_amount('total_traslados_base_iva_exento', base_amount_mxn)
    #                 elif check_transferred_tax_values(tax_values, '002', 'Tasa', 0.08):
    #                     update_tax_amount('total_traslados_base_iva8', base_amount_mxn)
    #                     update_tax_amount('total_traslados_impuesto_iva8', tax_amount_mxn)
    #                 elif check_transferred_tax_values(tax_values, '002', 'Tasa', 0.16):
    #                     update_tax_amount('total_traslados_base_iva16', base_amount_mxn)
    #                     update_tax_amount('total_traslados_impuesto_iva16', tax_amount_mxn)

    #     # Rounding global tax amounts.
    #     for dictionary in (
    #         withholding_values_map,
    #         transferred_values_map,
    #         local_retenciones_values_map,
    #         local_traslados_values_map,
    #     ):
    #         for values in dictionary.values():
    #             if 'base' in values:
    #                 values['base'] = self.currency_id.round(values['base'])
    #             values['importe'] = self.currency_id.round(values['importe'])

    #     for key in (
    #         'total_traslados_base_iva0',
    #         'total_traslados_impuesto_iva0',
    #         'total_traslados_base_iva_exento',
    #         'total_traslados_base_iva8',
    #         'total_traslados_impuesto_iva8',
    #         'total_traslados_base_iva16',
    #         'total_traslados_impuesto_iva16',
    #         'total_retenciones_isr',
    #         'total_retenciones_iva',
    #         'total_retenciones_ieps',
    #     ):
    #         if key in cfdi_values:
    #             cfdi_values[key] = company_curr.round(cfdi_values[key])
    #         else:
    #             cfdi_values[key] = None

    #     for target_key, source_dict in (
    #         ('retenciones_list', withholding_values_map),
    #         ('traslados_list', transferred_values_map),
    #         ('local_retenciones_list', local_retenciones_values_map),
    #         ('local_traslados_list', local_traslados_values_map),
    #     ):
    #         cfdi_values[target_key] = [
    #             {**k, **v}
    #             for k, v in source_dict.items()
    #         ]

    #     # Cleanup attributes for Exento taxes.
    #     for key in (
    #         'traslados_list',
    #         'local_traslados_list',
    #     ):
    #         for tax_values in cfdi_values[key]:
    #             if tax_values['tipo_factor'] == 'Exento':
    #                 tax_values['importe'] = None

    # -------------------------------------------------------------------------
    # CFDI: DOCUMENTS
    # ----
    

    def _as_debug_log(self, message):
        """
        Propósito: Función de utilidad para loguear mensajes de debug con ID de factura
        Parámetros: message - mensaje a loguear
        """
        try:
            # Generar un ID único para esta sesión de logs
            trace_id = f"INVOICE-{self.id}-{int(time.time())}"
            
            # Asegurar que message es un string para evitar errores
            if not isinstance(message, str):
                message = str(message)
            
            # Loguear a nivel INFO para asegurar que sea visible
            _logger.info(f"[DEBUG-MX-INVOICE][{trace_id}] {message}")
            _debug_logger.info(f"[{trace_id}] {message}")
            
            # También añadir al chatter para mayor visibilidad (solo si no estamos en un cálculo recursivo)
            # Verificamos si estamos dentro de una transacción ya en progreso para evitar errores
            try:
                # Usar una variable de contexto para prevenir recursión
                if not self.env.context.get('skip_chatter_log'):
                    # Crear un nuevo entorno con el contexto modificado para la siguiente llamada
                    ctx = dict(self.env.context, skip_chatter_log=True)
                    # self.with_context(ctx).sudo().message_post(
                    #     body=f"<p><b>DEBUG [{trace_id}]:</b> {message}</p>",
                    #     subject="DEBUG Log",
                    #     message_type='comment',
                    #     subtype_xmlid='mail.mt_note',
                    #     body_is_html=True
                    # )
            except Exception as e:
                _logger.error(f"Error al postear en chatter: {e}. Continúa el proceso.")
        except Exception as general_error:
            # Asegurar que el logging no interrumpe el flujo principal
            _logger.error(f"Error general en _as_debug_log: {general_error}")
        
        # Siempre retornamos para no interrumpir el flujo
        return None
    
    def as_get_name_invoice(self):
        """
        Propósito: Método que retorna el nombre formateado de la factura para usar en reportes PDF
                  y correos electrónicos.
        Retorno: String con el nombre de la factura.
        """
        self.ensure_one()
        self._as_debug_log(f"Llamada a as_get_name_invoice para factura {self.name} (tipo: {self.move_type}, estado: {self.state})")
        
        if self.move_type == 'out_invoice' and self.state == 'posted':
            result = f"{self.journal_id.code}-{self.payment_reference or self.name}-MX-Invoice.pdf".replace('/', '')
        else:
            result = f"INV{self.name or ''}.pdf".replace('/','')
            
        self._as_debug_log(f"Nombre generado para la factura: {result}")
        return result

    def action_invoice_print(self):
        """
        Propósito: Imprime la factura usando el reporte estándar de Odoo.
        Retorno: Acción para imprimir la factura.
        """
        self.ensure_one()
        
        # Usar directamente el reporte estándar, omitiendo la referencia al reporte personalizado
        # que está causando errores
        report = self.env.ref('account.account_invoices')
            
        return report.report_action(self)

    def button_process_edi_web_services(self):
        """
        Propósito: Procesa los servicios web EDI y genera el PDF de la factura.
        Retorno: Resultado del procesamiento EDI.
        """
        # Llamar al método original primero
        res = super().button_process_edi_web_services()
        
        # Procesar la generación de PDF para cada factura
        for invoice in self:
            try:
                # Generar nombre del archivo
                cfdi_filename = f"{invoice.journal_id.code}-{invoice.payment_reference or invoice.name}-MX-Invoice-3.3.xml".replace('/', '')
                
                if not cfdi_filename:
                    continue
                    
                # Buscar si ya existe un adjunto PDF
                name = cfdi_filename.split('.')[0]
                existing_attachments = self.env['ir.attachment'].search([
                    ('name', '=', name and _("%s.pdf") % name),
                    ('res_id', '=', invoice.id),
                    ('res_model', '=', 'account.move')
                ])
                
                # Si no existe, crear el adjunto PDF
                if not existing_attachments:
                    try:
                        # Usar el reporte estándar
                        report = self.env.ref('account.account_invoices')
                        
                        # Renderizar el PDF
                        content = report._render_qweb_pdf(invoice.id)[0]
                        
                        # Crear el adjunto
                        self.env['ir.attachment'].create({
                            'name': name and _("%s.pdf") % name or _("Factura_.pdf"),
                            'type': 'binary',
                            'datas': base64.b64encode(content),
                            'res_model': 'account.move',
                            'res_id': invoice.id,
                        })
                        _logger.info("[button_process_edi_web_services] PDF adjunto creado para factura %s", invoice.name)
                    except Exception as attachment_error:
                        _logger.error("[button_process_edi_web_services] Error al crear adjunto de factura %s: %s", 
                                     invoice.name, attachment_error)
            except Exception as invoice_error:
                _logger.error("[button_process_edi_web_services] Error procesando factura %s: %s", 
                             invoice.name if hasattr(invoice, 'name') else 'desconocido', invoice_error)
                
        return res
            
    @api.model
    def l10n_mx_edi_retrieve_attachments(self):
        """
        Propósito: Recupera todos los adjuntos CFDI generados para esta factura.
        Retorno: Un recordset de ir.attachment.
        """
        self.ensure_one()
        if not self.l10n_mx_edi_cfdi_name:
            return []
        domain = [
            ('res_id', '=', self.id),
            ('res_model', '=', self._name),
            ('name', '=', self.l10n_mx_edi_cfdi_name)]
        return self.env['ir.attachment'].search(domain)

    def l10n_mx_edi_amount_to_text(self):
        """
        Propósito: Transforma un monto flotante a texto en formato mexicano para facturas.
        Retorno: String con el monto en palabras.
        """
        self.ensure_one()
        currency = self.currency_id.name.upper()
        # M.N. = Moneda Nacional (National Currency)
        # M.E. = Moneda Extranjera (Foreign Currency)
        if currency == 'MXN':
            currency_type = 'M.N'
        elif currency == 'USD':
            currency_type = 'USD'
        else:
            currency_type = 'M.E.'
        # Split integer and decimal part
        amount_i, amount_d = divmod(self.amount_total, 1)
        amount_d = round(amount_d, 2)
        amount_d = int(round(amount_d * 100, 2))
        words = self.currency_id.with_context(lang=self.partner_id.lang or 'es_ES').amount_to_text(amount_i).upper()
        invoice_words = f"{words} {amount_d:02d}/100 {currency_type}"
        return invoice_words
            
    @api.model
    def _get_invoice_in_payment_state(self):
        """
        Propósito: Sobrescribe el método para habilitar el estado 'in_payment' en facturas.
        Retorno: Estado 'paid' para la factura.
        """
        # OVERRIDE to enable the 'in_payment' state on invoices.
        return 'paid'

    # def _reverse_moves(self, default_values_list=None, cancel=False):
    #     """
    #     Propósito: Procesa las contramovimientos contables.
    #     Parámetros: 
    #         default_values_list: Lista de valores predeterminados
    #         cancel: Indica si se debe cancelar el movimiento
    #     Retorno: Movimientos invertidos
    #     """
    #     if not default_values_list:
    #         default_values_list = [{} for move in self]

    #     if cancel:
    #         lines = self.mapped('line_ids')
    #         # Avoid maximum recursion depth.
    #         if lines:
    #             lines.remove_move_reconcile()

    #     reverse_type_map = {
    #         'entry': 'entry',
    #         'out_invoice': 'out_refund',
    #         'out_refund': 'entry',
    #         'in_invoice': 'in_refund',
    #         'in_refund': 'entry',
    #         'out_receipt': 'entry',
    #         'in_receipt': 'entry',
    #     }

    #     move_vals_list = []
    #     for move, default_values in zip(self, default_values_list):
    #         default_values.update({
    #             'move_type': reverse_type_map[move.move_type],
    #             'reversed_entry_id': move.id,
    #         })
    #         move_vals_list.append(move.with_context(move_reverse_cancel=cancel)._reverse_move_vals(default_values, cancel=cancel))

    #     reverse_moves = self.env['account.move'].create(move_vals_list)
    #     # Crear un container para la validación de balance
    #     container = {'records': reverse_moves}
    #     reverse_moves._check_balanced(container)

    #     # Reconcile moves together to cancel the previous one.
    #     if cancel:
    #         reverse_moves.with_context(move_reverse_cancel=cancel)._post(soft=False)
    #         for move, reverse_move in zip(self, reverse_moves):
    #             group = defaultdict(list)
    #             for line in (move.line_ids + reverse_move.line_ids).filtered(lambda l: not l.reconciled):
    #                 group[(line.account_id, line.currency_id)].append(line.id)
    #             for (account, dummy), line_ids in group.items():
    #                 if account.reconcile or account.internal_type == 'liquidity':
    #                     self.env['account.move.line'].browse(line_ids).with_context(move_reverse_cancel=cancel).reconcile()

    #     return reverse_moves

    def _get_invoiced_lot_values1(self, product_id):
        """ 
        Propósito: Obtiene y prepara datos para mostrar tabla de lotes facturados en el reporte.
        Parámetros:
            product_id: ID del producto a filtrar
        Retorno: Lista de valores de lotes
        """
        self.ensure_one()
        from odoo.tools import float_is_zero

        if self.state == 'draft':
            return []  # Corregido: Retorna lista vacía en lugar de variable indefinida

        sale_lines = self.invoice_line_ids.sale_line_ids
        sale_orders = sale_lines.order_id
        stock_move_lines = sale_lines.move_ids.filtered(lambda r: r.state == 'done').move_line_ids

        # Get the other customer invoices and refunds.
        ordered_invoice_ids = sale_orders.mapped('invoice_ids')\
            .filtered(lambda i: i.state not in ['draft', 'cancel'])\
            .sorted(lambda i: (i.invoice_date, i.id))

        # Get the position of self in other customer invoices and refunds.
        self_index = None
        i = 0
        for invoice in ordered_invoice_ids:
            if invoice.id == self.id:
                self_index = i
                break
            i += 1

        # Get the previous invoices if any.
        previous_invoices = ordered_invoice_ids[:self_index]

        # Get the incoming and outgoing sml between self.invoice_date and the previous invoice (if any) of the related product.
        write_dates = [wd for wd in self.invoice_line_ids.mapped('write_date') if wd]
        self_datetime = max(write_dates) if write_dates else None
        last_invoice_datetime = dict()
        for product in self.invoice_line_ids.product_id:
            last_invoice = previous_invoices.filtered(lambda inv: product in inv.invoice_line_ids.product_id)
            last_invoice = last_invoice[-1] if len(last_invoice) else None
            last_write_dates = last_invoice and [wd for wd in last_invoice.invoice_line_ids.mapped('write_date') if wd]
            last_invoice_datetime[product] = max(last_write_dates) if last_write_dates else None

        def _filter_incoming_sml1(ml):
            if ml.state == 'done' and ml.location_id.usage == 'customer' and ml.lot_id:
                last_date = last_invoice_datetime.get(ml.product_id)
                if last_date:
                    return last_date <= ml.date <= self_datetime
                else:
                    return ml.date <= self_datetime
            return False

        def _filter_outgoing_sml1(ml):
            if ml.state == 'done' and ml.location_dest_id.usage == 'customer' and ml.lot_id:
                last_date = last_invoice_datetime.get(ml.product_id)
                if last_date:
                    return last_date <= ml.date <= self_datetime
                else:
                    return ml.date <= self_datetime
            return False

        incoming_sml = stock_move_lines.filtered(_filter_incoming_sml1)
        outgoing_sml = stock_move_lines.filtered(_filter_outgoing_sml1)

        # Prepare and return lot_values
        qties_per_lot = defaultdict(lambda: 0)
        if self.move_type == 'out_refund':
            for ml in outgoing_sml:
                qties_per_lot[ml.lot_id] -= ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
            for ml in incoming_sml:
                qties_per_lot[ml.lot_id] += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
        else:
            for ml in outgoing_sml:
                qties_per_lot[ml.lot_id] += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
            for ml in incoming_sml:
                qties_per_lot[ml.lot_id] -= ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
        lot_values = []
        for lot_id, qty in qties_per_lot.items():
            if lot_id.product_id == product_id:
                if float_is_zero(qty, precision_rounding=lot_id.product_id.uom_id.rounding):
                    continue
                lot_values.append({
                    'product_name': lot_id.product_id.display_name,
                    'quantity': self.env['ir.qweb.field.float'].value_to_html(qty, {'precision': self.env['decimal.precision'].precision_get('Product Unit of Measure')}),
                    'uom_name': lot_id.product_uom_id.name,
                    'lot_name': lot_id.name,
                    # The lot id is needed by localizations to inherit the method and add custom fields on the invoice's report.
                    'lot_id': lot_id.id
                })
        return lot_values

    def _onchange_terms(self):
        """
        Propósito: Obtiene los términos de factura desde la compañía.
        Retorno: Términos de factura de la compañía.
        """
        invoice_terms = self.company_id.invoice_terms
        return invoice_terms

    def action_post(self):
        """
        Propósito: Procesa la publicación de la factura y registra historiales de promoción.
        Retorno: Resultado de publicación.
        """
        sale_order = self.env['sale.order'].search([('name', '=', self.invoice_origin)], limit=1)
        line_sale = False
        if sale_order and self.move_type == 'out_refund':
            #recorremos las lineas de la factura
            for line in self.invoice_line_ids:
                for line_so in sale_order.order_line:
                    if line.product_id == line_so.product_id:
                        line_sale = line_so
                        break
                        
                tf_partner_id = self.env['tf.res.partner']
                for x in sale_order.partner_id.tf_vendor_parameter_ids:
                    if line_sale and x.category_id.id == line_sale.product_id.categ_id.id:
                        tf_partner_id = x
                        break
                        
                if not tf_partner_id:
                    continue
                    
                #se realizan los calculos 
                moneda_mxn = self.env['res.currency'].search([('id', '=', 33)])
                moneda_usd = self.env['res.currency'].search([('id', '=', 2)])
                price_unit = line.price_unit
                
                RECALCULATED_PRICE_UNIT = line.move_id.currency_id._convert_nimax(
                    price_unit, moneda_usd, self.env.user.company_id, fields.Date.today(), line_sale.id)
                monto_mxp = line.move_id.currency_id._convert_nimax(
                    price_unit, moneda_mxn, self.env.user.company_id, fields.Date.today(), line_sale.id)
                NIMAX_PRICE_MXP = monto_mxp
                COST_NIMAX_USD = line.move_id.currency_id._convert_nimax(
                    line_sale.COST_NIMAX_USD, moneda_usd, self.env.user.company_id, fields.Date.today(), line_sale.id)
                COST_NIMAX_MXP = line.move_id.currency_id._convert_nimax(
                    line_sale.COST_NIMAX_USD, moneda_mxn, self.env.user.company_id, fields.Date.today(), line_sale.id)
                    
                MARGIN_MXP = (NIMAX_PRICE_MXP * line.quantity) - (COST_NIMAX_MXP * line.quantity)
                MARGIN_USD = (RECALCULATED_PRICE_UNIT * line.quantity) - (COST_NIMAX_USD * line.quantity)
                TOTAL_USD = RECALCULATED_PRICE_UNIT * line.quantity
                TOTAL_MXP = NIMAX_PRICE_MXP * line.quantity
              
                #creamos el registro en el historico de promociones 
                self.env['tf.history.promo'].create({
                    'vendor_id': tf_partner_id.partner_id.id,
                    'product_id': line_sale.product_id.id,
                    'customer_id': line_sale.order_id.partner_id.id,
                    'customer_type': tf_partner_id.partner_type.id,
                    'category_id': line_sale.product_id.categ_id.id,
                    'qty': line.quantity,
                    'recalculated_price_unit': RECALCULATED_PRICE_UNIT,
                    'recalculated_price_unit_mxp': NIMAX_PRICE_MXP,
                    'recalculated_cost_nimax_usd': COST_NIMAX_USD,
                    'recalculated_cost_nimax_mxp': COST_NIMAX_MXP,
                    'margin_mxp': MARGIN_MXP * -1,
                    'margin_usd': MARGIN_USD * -1,
                    'total_usd': TOTAL_USD * -1,
                    'total_mxp': TOTAL_MXP * -1,
                    'salesman_id': line.move_id.user_id.id,
                    'sale_id': sale_order.id,
                    'sale_order_line': line_sale.id,
                })

                #se marca la utima action desde factura 
                self.env.cr.execute("""
                    SELECT id FROM tf_history_promo 
                    WHERE
                      sale_id = %s AND 
                      product_id = %s AND 
                      sale_order_line = %s
                    ORDER BY create_date DESC LIMIT 1
                """, (sale_order.id, line.product_id.id, line_sale.id))
                
                history_table = [j[0] for j in self.env.cr.fetchall()]
                tf_history_id = self.env['tf.history.promo'].browse(history_table)
                if tf_history_id:
                    tf_history_id.last_applied_promo = True
                    
        res = super().action_post()
        return res

    def get_promocion(self, line_id):
        """
        Propósito: Obtiene la promoción aplicada a una línea de factura.
        Parámetros:
            line_id: ID de la línea de factura
        Retorno: Nombre de la promoción aplicada
        """
        self.env.cr.execute("""
            SELECT order_line_id FROM sale_order_line_invoice_rel 
            WHERE invoice_line_id = %s
        """, (line_id,))
        
        ids = [k[0] for k in self.env.cr.fetchall()]
        name = ''
        
        if ids:
            line = self.env['sale.order.line'].search([('id', 'in', ids)], limit=1)
            ultima_promo = self.env['tf.history.promo'].search([
                ('sale_id', '=', line.order_id.id),
                ('product_id', '=', line.product_id.id),
                ('last_applied_promo', '=', True)
            ], order="write_date desc", limit=1)
            
            if ultima_promo:
                name = f"{ultima_promo.promo_id.id} : {ultima_promo.promo_id.name}"
            else:
                name = ' '
                
        return name
    
    def detalle_pagos(self):
        xml = self._l10n_mx_edi_get_extra_invoice_report_values()
        return {
            'payment_method': xml.get('payment_method', ''),
            'forma_pago': self.l10n_mx_edi_payment_method_id.code or '99',
            'uso_cfdi': xml.get('cfdi_node', {}).get('Receptor', {}).get('UsoCFDI', ''),
            'currency_name': self.currency_id.name,

        }

    def detalle_folio(self):
        xml = self._l10n_mx_edi_get_extra_invoice_report_values()
        return {
            'certificate_sat_number': xml.get('certificate_sat_number', ''),
            'certificate_number': xml.get('certificate_number', ''),
            'emission_date_string':  xml.get('emission_date_str', ''),
            'folio_fiscal': xml.get('uuid', ''),
            'stamp_date': xml.get('stamp_date', ''),
            'uuid': xml.get('uuid', ''),
            'sello': xml.get('sello', ''),
            'sello_sat': xml.get('sello_sat', ''),
            'barcode_src': xml.get('barcode_src', ''),
            'cfdi_values': xml.get('cfdi_values', {}),
            'expedition': xml.get('expedition', {}),
            'fiscal_regime': xml.get('fiscal_regime', ''),
            'emision_date': xml.get('emission_date', ''),
            'stamp_date': xml.get('stamp_date', ''),
          
            

        } 
        
        
    def get_tasa_xml(self, product_id):
        """
        Propósito: Obtiene la tasa de impuesto desde el XML CFDI para un producto.
        Parámetros:
            product_id: ID del producto
        Retorno: Lista con información de impuestos
        """
        xml = self._l10n_mx_edi_get_extra_invoice_report_values()
        impuestos = []
        
        if xml is not None and 'cfdi_node' in xml:
            conceptos = xml['cfdi_node'].findall("{*}Conceptos/{*}Concepto")
            for product in conceptos:
                product = product.attrib
                if product.get('NoIdentificacion') == product_id and 'Impuestos' in product:
                    for translado in product.Impuestos.Traslados.Traslado:
                        if translado.attrib:
                            vals = {
                                'Tasa': translado.attrib['TasaOCuota'],
                                'Base': round(float(translado.attrib['Base']), 2),
                                'Impuesto': translado.attrib['Impuesto'],
                                'Importe': round(float(translado.attrib['Importe']), 2),
                            }
                            impuestos.append(vals)
                            break  # Optimizado: reemplaza la bandera con break

        return impuestos

    def get_product_lot(self, product_id,line_id):
        """
        Propósito: Obtiene los lotes de un producto en la factura.
        Parámetros:
            product_id: ID del producto
        Retorno: String con nombres de lotes
        """
        names = ''
        for move in line_id.lot_ped_ids:
            name = move.name.split(' / ')[0] if len(move.name.split(' / ')) > 1 else move.name
            names += f"{name}, "
                    
        return names
    
    def depurar_lotes(self,lotes):
        lotes = self.env['stock.lot'].browse(lotes)
        return lotes
    
        
    def get_referencia_pedido(self):
        sale_order = self.env['sale.order'].search([('name','=',self.invoice_origin)],limit=1)
        if sale_order and 'x_studio_orden_de_compra' in sale_order:
            return sale_order.x_studio_orden_de_compra
        else:
            return 'N/A'

    def adjuntar_factura_model(self, invoice):
        """
        Propósito: Adjunta la factura al modelo.
        Parámetros:
            invoice: Objeto de factura
        Retorno: String vacío
        """
        # TODO: Implementar lógica para adjuntar factura o eliminar método si no es necesario
        _logger.info("[adjuntar_factura_model] Método no implementado")
        return ''    

    # --- Botón Timbrar Manual --- 
    def button_as_manual_cfdi_sign(self):
        """
        Función para el botón que dispara manualmente el timbrado CFDI
        """
        self.ensure_one()
        if self.state != 'posted':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('La factura debe estar en estado "Publicado" para timbrar el CFDI.'),
                    'sticky': True,
                    'type': 'danger',
                }
            }
            
        if not self.l10n_mx_edi_is_cfdi_needed:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Esta factura no requiere CFDI.'),
                    'sticky': True,
                    'type': 'danger',
                }
            }
            
        if self.l10n_mx_edi_cfdi_state:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Esta factura ya tiene un estado CFDI: %s') % self.l10n_mx_edi_cfdi_state,
                    'sticky': True,
                    'type': 'danger',
                }
            }
            
        # Si no hay errores, intentamos timbrar
        try:
            _logger.info("AS: Iniciando timbrado manual para factura %s (ID: %s)", self.name, self.id)
            
            # Ejecutar el mismo método que la acción automática
            if self.move_type == 'entry':
                self.l10n_mx_edi_cfdi_payment_force_try_send()
            else:
                self._l10n_mx_edi_cfdi_invoice_try_send()
            
            # Devolver mensaje de éxito (aunque esto no garantiza que el timbrado fue exitoso)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Proceso iniciado'),
                    'message': _('Se ha iniciado el proceso de timbrado CFDI. Verifica el estado en unos momentos.'),
                    'sticky': False,
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error("Error durante el timbrado manual CFDI: %s", str(e))
            _logger.error(traceback.format_exc())
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error en timbrado'),
                    'message': str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }    
    def button_as_manual_cfdi_sign_payment(self):
        """
        Función para el botón que dispara manualmente el timbrado CFDI
        """
        self.ensure_one()
        if self.state != 'posted':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('La factura debe estar en estado "Publicado" para timbrar el CFDI.'),
                    'sticky': True,
                    'type': 'danger',
                }
            }
            
        if not self.l10n_mx_edi_is_cfdi_needed:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Esta factura no requiere CFDI.'),
                    'sticky': True,
                    'type': 'danger',
                }
            }
            
        if self.l10n_mx_edi_cfdi_state:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Esta factura ya tiene un estado CFDI: %s') % self.l10n_mx_edi_cfdi_state,
                    'sticky': True,
                    'type': 'danger',
                }
            }
            
        # Si no hay errores, intentamos timbrar
        try:
            _logger.info("AS: Iniciando timbrado manual para factura %s (ID: %s)", self.name, self.id)
            
            # Ejecutar el mismo método que la acción automática
            self.button_as_manual_cfdi_sign_payment()
            
            # Devolver mensaje de éxito (aunque esto no garantiza que el timbrado fue exitoso)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Proceso iniciado'),
                    'message': _('Se ha iniciado el proceso de timbrado CFDI. Verifica el estado en unos momentos.'),
                    'sticky': False,
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error("Error durante el timbrado manual CFDI: %s", str(e))
            _logger.error(traceback.format_exc())
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error en timbrado'),
                    'message': str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }


    def as_action_manual_l10n_mx_edi_cfdi_try_send(self):
        """
        Método para el botón que intenta timbrar manualmente desde el botón
        de Timbrar MX (Manual)
        """
        self.ensure_one()
        if self.state != 'posted' or not self.l10n_mx_edi_is_cfdi_needed:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('La factura debe estar publicada y requerir CFDI.'),
                    'sticky': True,
                    'type': 'danger',
                }
            }
            
        try:
            _logger.info("[AS_MX_INV] Iniciando timbrado manual para factura %s (ID: %s)", self.name, self.id)

            if self.move_type == 'entry':
                self.l10n_mx_edi_cfdi_payment_force_try_send()
            else:
                self._l10n_mx_edi_cfdi_invoice_try_send()

            # Ejecutar el mismo método que la acción automática
            
            
            # self.message_post(
            #     body=_("<p><b>Proceso de timbrado iniciado manualmente</b></p><p>Verificando resultados en unos momentos...</p>"),
            #     subject="Timbrado Manual CFDI (AS)",
            #     message_type='comment',
            #     subtype_xmlid='mail.mt_note',
            #     body_is_html=True
            # )
            
            # Actualizar vista
            return True
        except Exception as e:
            _logger.error("[AS_MX_INV] Error durante el timbrado manual CFDI: %s", str(e))
            error_details = traceback.format_exc()
            _logger.error(error_details)
            
            # Postear el error en el chatter para diagnóstico
            # self.message_post(
            #     body=f"""<p><b>⚠️ Error al iniciar timbrado manual CFDI</b></p>
            #         <p>Detalles del error:</p>
            #         <pre>{str(e)}</pre>
            #         <p>Traza completa (para debug):</p>
            #         <pre>{error_details}</pre>
            #     """,
            #     subject="ERROR en Timbrado Manual CFDI (AS)",
            #     message_type='comment',
            #     subtype_xmlid='mail.mt_note',
            #     body_is_html=True
            # )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error en timbrado'),
                    'message': str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }

    def as_action_check_pac_config(self):
        """
        Método para el botón que verifica la configuración PAC
        """
        self.ensure_one()
        try:
            # Llamar al método desde el modelo check_pac
            result = self.env['as_mx_invoice.check_pac'].create({}).action_check_pac_config()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Verificación PAC'),
                    'message': _('Verificación de PAC completada y añadida al chatter.'),
                    'sticky': False,
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error("[AS_MX_INV] Error durante verificación PAC: %s", str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error en verificación'),
                    'message': str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }

    def as_action_fix_edi_documents(self):
        """
        Método para el botón que repara documentos EDI con problemas
        """
        self.ensure_one()
        try:
            # Llamar al método desde el modelo check_pac
            result = self.env['as_mx_invoice.check_pac'].action_fix_edi_documents()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Reparación EDI'),
                    'message': _('Reparación de documentos EDI completada y añadida al chatter.'),
                    'sticky': False,
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error("[AS_MX_INV] Error durante reparación EDI: %s", str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error en reparación'),
                    'message': str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }

    def as_action_retry_l10n_mx_edi_cfdi_with_current_date(self):
        """
        Método para reintentar timbrado del CFDI con la fecha y hora actuales.
        Este método actualiza el campo l10n_mx_edi_post_time a la hora actual
        y luego intenta timbrar nuevamente la factura.
        """
        self.ensure_one()
        if self.state != 'posted' or not self.l10n_mx_edi_is_cfdi_needed:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('La factura debe estar publicada y requerir CFDI.'),
                    'sticky': True,
                    'type': 'danger',
                }
            }
            
        try:
            # Actualizar la fecha/hora de timbrado a la hora actual
            current_datetime = fields.Datetime.now()
            self.l10n_mx_edi_post_time = current_datetime
            
            _logger.info(f"[AS_MX_INV_RETRY] Actualizando fecha/hora para factura {self.name} a {current_datetime}")
            
            # Mostrar detalles detallados del rango de fechas
            # Obtener zona horaria de México
            mexico_tz = pytz.timezone('America/Mexico_City')
            now_utc = datetime.now(pytz.UTC)
            now_mx = now_utc.astimezone(mexico_tz)
            
            # Calcular límites de fecha permitidos
            min_allowed_date = now_mx - timedelta(hours=72)
            max_allowed_date = now_mx + timedelta(minutes=5)
            
            # Convertir fecha actual de timbrado a zona horaria de México
            current_post_time_utc = pytz.UTC.localize(current_datetime.replace(tzinfo=None))
            current_post_time_mx = current_post_time_utc.astimezone(mexico_tz)
            
            # Formatear mensaje
            date_info = f"""
<b>ACTUALIZACIÓN DE FECHA DE TIMBRADO CFDI PARA REINTENTO:</b><br/>
<hr/>
<b>Fecha/Hora actual en México:</b> {now_mx.strftime('%Y-%m-%d %H:%M:%S %Z')}<br/>
<b>Rango permitido para timbrado:</b><br/>
- Mínimo: {min_allowed_date.strftime('%Y-%m-%d %H:%M:%S')} (72 horas atrás)<br/>
- Máximo: {max_allowed_date.strftime('%Y-%m-%d %H:%M:%S')} (5 minutos adelante)<br/>
<br/>
<b>Nueva Fecha/Hora de timbrado:</b> {current_post_time_mx.strftime('%Y-%m-%d %H:%M:%S %Z')}<br/>
<br/>
<b>✅ La fecha ha sido actualizada y está dentro del rango permitido.</b><br/>
<hr/>
<i>Nota: El SAT requiere que la fecha de timbrado esté entre -72 horas y +5 minutos respecto a la hora actual de México.</i>
            """
            
            # Buscar documentos EDI existentes para la factura y marcarlos para reintento
            edi_docs = self.env['l10n_mx_edi.document'].search([('move_id', '=', self.id)])
            if edi_docs:
                # Actualizar el estado del documento para permitir un nuevo intento
                for doc in edi_docs:
                    if doc.state in ('invoice_sent_failed'):
                        doc.state = 'invoice_sent_failed'  # Forzar estado de error para permitir reintento
                        doc.message = f"Reintento solicitado con nueva fecha/hora: {current_datetime}"
                        _logger.info(f"[AS_MX_INV_RETRY] Documento EDI ID {doc.id} marcado para reintento")
            
            # Ejecutar el mismo método que la acción automática
            self._l10n_mx_edi_cfdi_invoice_try_send()
            
            # self.message_post(
            #     body=date_info,
            #     subject="Reintento de Timbrado CFDI con Fecha Actual (AS)",
            #     message_type='comment',
            #     subtype_xmlid='mail.mt_note',
            #     body_is_html=True
            # )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Reintento iniciado'),
                    'message': _('Se ha reiniciado el proceso de timbrado con la fecha/hora actual.'),
                    'sticky': False,
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error("[AS_MX_INV_RETRY] Error durante el reintento de timbrado: %s", str(e))
            error_details = traceback.format_exc()
            _logger.error(error_details)
            
            # Postear el error en el chatter para diagnóstico
            # self.message_post(
            #     body=f"""<p><b>⚠️ Error al reintentar timbrado CFDI con fecha actual</b></p>
            #         <p>Detalles del error:</p>
            #         <pre>{str(e)}</pre>
            #         <p>Traza completa (para debug):</p>
            #         <pre>{error_details}</pre>
            #     """,
            #     subject="ERROR en Reintento de Timbrado CFDI (AS)",
            #     message_type='comment',
            #     subtype_xmlid='mail.mt_note',
            #     body_is_html=True
            # )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error en reintento'),
                    'message': str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }

    # --- Sobreescritura del Cálculo de Necesidad CFDI ---    
    @api.depends('move_type', 'company_id.currency_id', 'origin_payment_id', 'statement_line_id', 'country_code')
    def _compute_l10n_mx_edi_is_cfdi_needed(self):
        """
        OVERRIDE: Modificado en as_mx_invoice.
        Permite CFDI aunque la moneda de la compañía NO sea MXN (¡OJO! Esto puede no ser estándar SAT).
        Loguea las condiciones al chatter.
        """
        _logger_compute = logging.getLogger(__name__ + ".compute_cfdi_needed")

        for move in self:
            cond1_country_is_mx = move.country_code == 'MX'
            cond2_company_currency_is_mxn = True # Forzado
            company_currency_name = move.company_currency_id.name
            is_payment = move._l10n_mx_edi_is_cfdi_payment()
            cond3_move_type_ok = move.move_type in ('out_invoice', 'out_refund') or is_payment
            final_result = cond1_country_is_mx and cond2_company_currency_is_mxn and cond3_move_type_ok
            move.l10n_mx_edi_is_cfdi_needed = final_result

            try:
                message = f"""
<b>Verificación Condiciones para Necesidad CFDI (MODIFICADO POR AS)</b><br/>
--------------------------------------------------<br/>
1. País Factura == 'MX': {cond1_country_is_mx} (Valor: {move.country_code})<br/>
2. Moneda Compañía == 'MXN': <b style='color:orange;'>IGNORADO POR AS</b> (Moneda Real: {company_currency_name})<br/>
3. Tipo Documento OK (Fact/Rectif Cliente o Pago): {cond3_move_type_ok} (Tipo: {move.move_type}, Es Pago: {is_payment})<br/>
--------------------------------------------------<br/>
<b>Resultado Final (Necesita CFDI): {final_result}</b>
                """
                # if move.move_type in ('out_invoice', 'out_refund') or is_payment:
                #      move.message_post(
                #         body=message,
                #         subject="Detalle Cálculo Necesidad CFDI (AS Modificado)",
                #         message_type='comment',
                #         subtype_xmlid='mail.mt_note',
                #         body_is_html=True
                #      )
            except Exception as e:
                _logger_compute.warning(f"No se pudo postear detalle de cálculo CFDI (AS Mod) para {move.name}: {e}", exc_info=False)

    # --- Sobreescritura del Post (Logueo DB - Corregido) --- 
    def _post(self, soft=True):
        res = super()._post(soft=soft)
        for move in self.filtered(
            lambda m: m.state == 'posted' 
                      and m.country_code == 'MX' 
                      and (m.move_type in ('out_invoice', 'out_refund') or m._l10n_mx_edi_is_cfdi_payment())
        ):
            _logger.info(f"[AS_MX_INV_DEBUG] Posting CFDI data check to chatter for invoice {move.name} (ID: {move.id}) - Filtro Directo OK")
            try:
                cr = self.env.cr
                company = move.company_id
                company_partner = company.partner_id
                company_id = company.id
                cr.execute("""
                    SELECT c.name AS company_name, c.l10n_mx_edi_fiscal_regime
                    FROM res_company c WHERE c.id = %s;
                """, (company_id,))
                company_data = cr.dictfetchone() or {}
                company_name = company_data.get('company_name', 'Error')
                company_regimen = company_data.get('l10n_mx_edi_fiscal_regime', '¡¡FALTA!!')
                company_rfc = company_partner.vat or 'No encontrado'
                company_zip = company_partner.zip or '¡¡FALTA!!'

                # -- 2. Certificados CSD (usando ORM como antes) --
                valid_certificates = self.env['certificate.certificate'].search_count([
                    ('company_id', '=', company_id),
                    ('is_valid', '=', True)
                ])
                csd_ok_str = 'Sí' if valid_certificates > 0 else '¡¡NO!!'

                # -- 3. Configuración PAC - QUITADO TEMPORALMENTE POR AttributeError --
                pac_ok_str = "(No verificado - Campos PAC ausentes en res.company)"
                test_mode_str = "(No verificado)"
                pac_name = "(No verificado)"
                # Quitamos el intento de leer los campos PAC que no existen:
                # pac_name = company.l10n_mx_edi_pac_name or 'No configurado'
                # pac_username = company.l10n_mx_edi_pac_username or 'No config.'
                # pac_password_set = bool(company.l10n_mx_edi_pac_password)
                # pac_test_mode = company.l10n_mx_edi_pac_test_env
                # pac_ok_str = 'Sí' if pac_name != 'No configurado' and pac_username != 'No config.' and pac_password_set else '¡¡NO!! Faltan datos PAC en Compañía'
                # test_mode_str = 'Sí' if pac_test_mode else 'NO'

                partner_id = move.partner_id.id
                partner_data = {}
                if partner_id:
                    cr.execute("SELECT name AS c_name, vat AS c_rfc, l10n_mx_edi_fiscal_regime AS c_reg, zip AS c_zip FROM res_partner WHERE id = %s;", (partner_id,))
                    partner_data = cr.dictfetchone() or {}
                customer_name = partner_data.get('c_name', 'Error')
                customer_rfc = partner_data.get('c_rfc', 'No enc.')
                customer_regimen = partner_data.get('c_reg', '¡¡FALTA!!')
                customer_zip = partner_data.get('c_zip', '¡¡FALTA!!')

                payment_policy = move.l10n_mx_edi_payment_policy or 'N/C'
                payment_method_id = move.l10n_mx_edi_payment_method_id.id
                payment_method_code = 'Err'
                if payment_method_id:
                    cr.execute("SELECT code FROM l10n_mx_edi_payment_method WHERE id = %s;", (payment_method_id,))
                    pm_res = cr.fetchone()
                    payment_method_code = pm_res[0] if pm_res else '¡¡FALTA!!'
                else:
                    payment_method_code = '¡¡FALTA!!'
                invoice_usage = move.l10n_mx_edi_usage or '¡¡FALTA!!'
                currency_name = move.currency_id.name
                currency_rate = move.invoice_currency_rate if move.currency_id != move.company_currency_id else 'N/A'

                cr.execute("""
                    SELECT
                        aml.name AS DescripcionLinea
                        /* Quitamos referencias a unspsc_code que no existe en esta BD */
                        /*
                        usc_prod.code AS ClaveProdServ,
                        usc_uom.code AS ClaveUnidad
                        */
                    FROM account_move_line aml
                    LEFT JOIN product_product pp ON aml.product_id = pp.id
                    LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                    /* Quitamos LEFT JOINs a tablas que no existen */
                    /*  
                    LEFT JOIN unspsc_code usc_prod ON pt.unspsc_code_id = usc_prod.id
                    LEFT JOIN uom_uom uom ON aml.product_uom_id = uom.id
                    LEFT JOIN unspsc_code usc_uom ON uom.unspsc_code_id = usc_uom.id
                    */
                    WHERE aml.move_id = %s AND aml.display_type = 'product' AND aml.quantity != 0
                    ORDER BY aml.sequence, aml.id;
                """, (move.id,))
                lines_data = cr.dictfetchall()
                line_details_html = []
                if lines_data:
                    for line in lines_data:
                        # Quitamos referencias a campos que ya no existen en la consulta
                        # clave_prod_serv_str = line.get('claveprodserv') or '¡¡FALTA!!'
                        # clave_unidad_str = line.get('claveunidad') or '¡¡FALTA!!'
                        # line_details_html.append(f"<li>L: '{line.get('descripcionlinea', '')[:20]}...' CPS: {clave_prod_serv_str} CU: {clave_unidad_str}</li>")
                        line_details_html.append(f"<li>L: '{line.get('descripcionlinea', '')[:20]}...'</li>")
                    line_details_html = "\n".join(line_details_html)
                else:
                    line_details_html = "<li>No hay líneas válidas para CFDI</li>"

                # --- INICIO: Logueo Búsqueda de Certificado --- 
                # Quitamos la llamada al método inexistente y hacemos nuestra propia búsqueda
                # certificate_found = self.env['l10n_mx_edi.document']._get_edi_certificate(company)
                
                # Buscamos el certificado válido para la compañía
                certificate_found = None
                try:
                    # Primero buscamos cualquier certificado válido para la compañía
                    certificates = self.env['certificate.certificate'].search([
                        ('company_id', '=', company.id),
                        ('is_valid', '=', True)
                    ], limit=1)
                    
                    # Si no encontramos ninguno, buscamos cualquier certificado para la compañía
                    if not certificates:
                        certificates = self.env['certificate.certificate'].search([
                            ('company_id', '=', company.id),
                        ], limit=1)
                    
                    if certificates:
                        certificate_found = certificates[0]
                    
                    # --- VALIDACIONES DEL CERTIFICADO ---
                    cert_validation_details = []
                    
                    # 1. ¿Existe el certificado?
                    exists = certificate_found and certificate_found.exists()
                    cert_id = certificate_found.id if exists else "N/A"
                    cert_validation_details.append(f"1. Certificado ID {cert_id} existe: {'✅ SÍ' if exists else '❌ NO'}")
                    
                    if exists:
                        # 2. ¿Está asignado a la compañía correcta?
                        company_match = certificate_found.company_id.id == company.id
                        cert_validation_details.append(f"2. Asignado a compañía correcta: {'✅ SÍ' if company_match else f'❌ NO (está asignado a {certificate_found.company_id.name}, debería ser {company.name})'}")
                        
                        # 3. ¿Tiene contenido del certificado (archivo .cer)?
                        has_certificate = bool(certificate_found.pem_certificate)
                        cert_validation_details.append(f"3. Tiene contenido de certificado (.cer): {'✅ SÍ' if has_certificate else '❌ NO'}")
                        
                        # 4. ¿Tiene clave privada (archivo .key)?
                        has_private_key = certificate_found.private_key_id.id if certificate_found.private_key_id else False
                        cert_validation_details.append(f"4. Tiene clave privada (.key): {'✅ SÍ' if has_private_key else '❌ NO'}")
                        
                        # 5. ¿Está activo?
                        is_active = certificate_found.active
                        cert_validation_details.append(f"5. Certificado activo: {'✅ SÍ' if is_active else '❌ NO'}")
                        
                        # 6. ¿Está dentro del rango de validez?
                        now = fields.Datetime.now()
                        valid_from_date = certificate_found.date_start if hasattr(certificate_found, 'date_start') else False
                        valid_to_date = certificate_found.date_end if hasattr(certificate_found, 'date_end') else False
                        
                        date_valid = False
                        date_reason = ""
                        if not valid_from_date or not valid_to_date:
                            date_reason = "(⚠️ Fechas no especificadas)"
                        elif valid_from_date > now:
                            date_reason = f"(⚠️ Aún no válido, inicia en {fields.Datetime.to_string(valid_from_date)})"
                        elif valid_to_date < now:
                            date_reason = f"(⚠️ Ya expiró el {fields.Datetime.to_string(valid_to_date)})"
                        else:
                            date_valid = True
                        
                        cert_validation_details.append(f"6. Fechas de validez correctas: {'✅ SÍ' if date_valid else f'❌ NO {date_reason}'}")
                        
                        # 7. ¿Tiene is_valid = True?
                        is_valid_flag = certificate_found.is_valid
                        cert_validation_details.append(f"7. Campo is_valid = True: {'✅ SÍ' if is_valid_flag else '❌ NO'}")
                        
                        # 8. ¿Hubo error al cargar?
                        loading_error = certificate_found.loading_error if hasattr(certificate_found, 'loading_error') else None
                        if loading_error:
                            cert_validation_details.append(f"8. Error al cargar certificado: ❌ SÍ - {loading_error}")
                        else:
                            cert_validation_details.append(f"8. Error al cargar certificado: ✅ NO")
                    
                    # Agrega los detalles de validación al mensaje de certificado que se mostrará después
                    cert_validations_msg = "<br/>".join(cert_validation_details)
                    
                    # Log si se encontró certificado
                    if exists:
                        _logger.info(f"[AS_MX_INV_DEBUG] Usando certificado con ID {cert_id}")
                    else:
                        _logger.error("[AS_MX_INV_DEBUG] No se encontró ningún certificado válido para la compañía")
                except Exception as e:
                    _logger.error(f"[AS_MX_INV_DEBUG] Error al buscar certificado: {e}")
                    cert_validations_msg = f"Error al validar certificado: {e}"
                
                cert_details_msg = ""
                if certificate_found and certificate_found.exists():
                    cert_id = certificate_found.id
                    cert_name = certificate_found.name or "(Sin nombre)"
                    # Los campos que existen en certificate.certificate
                    cert_from = fields.Date.to_string(certificate_found.date_start) if hasattr(certificate_found, 'date_start') and certificate_found.date_start else "N/A"
                    cert_to = fields.Date.to_string(certificate_found.date_end) if hasattr(certificate_found, 'date_end') and certificate_found.date_end else "N/A"
                    cert_details_msg = (
                        f"Certificado Encontrado: Sí<br/>"
                        f"- ID: {cert_id}<br/>"
                        f"- Nombre: {html_escape(cert_name)}<br/>"
                        f"- Válido Desde: {cert_from}<br/>"
                        f"- Válido Hasta: {cert_to}<br/>"
                        f"<br/><b>Validaciones del Certificado:</b><br/>"
                        f"{cert_validations_msg}"
                    )
                    _logger.info(f"[AS_MX_INV_DEBUG] Certificado encontrado: ID {cert_id}, Vigencia: {cert_from} - {cert_to}")
                else:
                    cert_details_msg = "Certificado Encontrado: ¡NO! (Ninguno válido/vigente para la compañía)"
                    if 'cert_validations_msg' in locals():
                        cert_details_msg += f"<br/><br/><b>Validaciones del Certificado:</b><br/>{cert_validations_msg}"
                    _logger.warning(f"[AS_MX_INV_DEBUG] No se encontró certificado válido para la compañía {company.id}")
                # --- FIN: Logueo Búsqueda de Certificado --- 

                # Construir mensaje HTML principal (incluyendo info de certificado)
                message = f'''
<b>Verificación Datos CFDI 4.0 (AS - desde DB - v4 PAC Omitido)</b><br/>
--------------------------------------------------<br/>
<b>Emisor (Compañía: {company_name}):</b><br/>
- RFC: {company_rfc or 'No encontrado'}<br/>
- Nombre Fiscal: {company_name or 'No encontrado'}<br/>
- Régimen Fiscal: {company_regimen}<br/>
- Código Postal Fiscal: {company_zip}<br/>
- PAC Configurado: {pac_ok_str}<br/>
<br/>
<b>Certificado CSD Buscado:</b><br/>
{cert_details_msg}<br/> 
<br/>
<b>Receptor (Cliente: {customer_name}):</b><br/>
- RFC: {customer_rfc or 'No encontrado'}<br/>
- Nombre Fiscal: {customer_name or 'No encontrado'}<br/>
- Régimen Fiscal: {customer_regimen}<br/>
- Código Postal Fiscal: {customer_zip}<br/>
- Uso CFDI: {invoice_usage}<br/>
<br/>
<b>Factura:</b><br/>
- Método Pago (PUE/PPD): {payment_policy}<br/>
- Forma Pago (Código SAT): {payment_method_code}<br/>
- Moneda: {currency_name}<br/>
- Tipo Cambio (vs MXN): {currency_rate}<br/>
<br/>
<b>Líneas de Factura:</b><br/>
<ul>{line_details_html}</ul>
<br/>
--------------------------------------------------<br/>
<i>Revise estos datos con cuidado. Errores aquí impiden el timbrado.</i>
                '''
                # move.message_post(body=message, subject="Check CFDI v4 (AS - DB)", message_type='comment', subtype_xmlid='mail.mt_note', body_is_html=True)
                _logger.info(f"[AS_MX_INV_DEBUG] Posted check v4 (DB - PAC Omitted) to chatter for {move.name}")
            except Exception as e:
                _logger.error(f"[AS_MX_INV_DEBUG] Failed DB query/post chatter v4 for {move.name}: {e}", exc_info=True)
                # move.message_post(body=f"Error check CFDI v4 (AS): {e}")

        return res 

    def _l10n_mx_edi_add_invoice_cfdi_values(self, cfdi_values):
        """
        Hereda la función para agregar valores al diccionario CFDI.
        Propósito: Añadir un mensaje al chatter con los datos clave procesados y corregir
                   el tipo de cambio para facturas en USD.
        Parámetros:
            cfdi_values (dict): El diccionario que se está poblando con valores CFDI.
        Resultado:
            Llama a super() y luego postea un mensaje en el chatter del registro actual (self).
        """
        _logger.info("[AS_MX_INVOICE_DEBUG] Entrando a _l10n_mx_edi_add_invoice_cfdi_values heredado")

        # Log inicial con información de la factura
        self._as_debug_log(f"INICIO Procesamiento CFDI para factura {self.name} ({self.id})")
        self._as_debug_log(f"Moneda factura: {self.currency_id.name}, Moneda compañía: {self.company_currency_id.name}")
        self._as_debug_log(f"Tipo de cambio actual: {self.invoice_currency_rate}")
        self._as_debug_log(f"Fecha factura: {self.invoice_date}")
        
        # --- ANÁLISIS DE RANGO DE FECHA PERMITIDO PARA TIMBRADO ---
        # Según la documentación, la fecha del comprobante no puede ser menor a 72 horas 
        # de antigüedad ni mayor a 5 minutos con respecto a la fecha actual
        # Obtener zona horaria de México
        mexico_tz = pytz.timezone('America/Mexico_City')
        now_utc = datetime.now(pytz.UTC)
        now_mx = now_utc.astimezone(mexico_tz)
        
        # Calcular límites de fecha permitidos
        min_allowed_date = now_mx - timedelta(hours=72)
        max_allowed_date = now_mx + timedelta(minutes=5)
        
        # Obtener fecha actual de timbrado
        current_post_time = self.l10n_mx_edi_post_time
        if current_post_time:
            # Convertir a zona horaria de México si tiene zona horaria
            if current_post_time.tzinfo:
                current_post_time_mx = current_post_time.astimezone(mexico_tz)
            else:
                # Si no tiene zona horaria, asumir que está en UTC y convertir
                current_post_time_utc = pytz.UTC.localize(current_post_time)
                current_post_time_mx = current_post_time_utc.astimezone(mexico_tz)
        else:
            current_post_time_mx = None
        
        # Verificar si está en rango
        in_range = True
        reason = "En rango permitido"
        
        if current_post_time_mx:
            if current_post_time_mx < min_allowed_date:
                in_range = False
                reason = f"La fecha de timbrado es más de 72 horas en el pasado ({(now_mx - current_post_time_mx).total_seconds()/3600:.2f} horas)"
            elif current_post_time_mx > max_allowed_date:
                in_range = False
                reason = f"La fecha de timbrado es más de 5 minutos en el futuro ({(current_post_time_mx - now_mx).total_seconds()/60:.2f} minutos)"
        
        # Log detallado de fechas
        date_info = f"""
<b>ANÁLISIS DE FECHA DE TIMBRADO CFDI:</b><br/>
<hr/>
<b>Fecha/Hora actual en México:</b> {now_mx.strftime('%Y-%m-%d %H:%M:%S %Z')}<br/>
<b>Rango permitido para timbrado:</b><br/>
- Mínimo: {min_allowed_date.strftime('%Y-%m-%d %H:%M:%S')} (72 horas atrás)<br/>
- Máximo: {max_allowed_date.strftime('%Y-%m-%d %H:%M:%S')} (5 minutos adelante)<br/>
<br/>
<b>Fecha/Hora actual de timbrado:</b> {current_post_time_mx.strftime('%Y-%m-%d %H:%M:%S %Z') if current_post_time_mx else 'No definida'}<br/>
<b>Fecha/Hora en campo post_time:</b> {self.l10n_mx_edi_post_time if self.l10n_mx_edi_post_time else 'No definida'}<br/>
<br/>
<b>Resultado:</b> {'✅ ' if in_range else '❌ '}{reason}<br/>
<hr/>
<i>Nota: Se actualizará la fecha automáticamente para sincronizar con la hora actual de México.</i>
        """
        
        # self.message_post(
        #     body=date_info,
        #     subject="Análisis Fecha Timbrado CFDI",
        #     message_type='comment',
        #     subtype_xmlid='mail.mt_note',
        #     body_is_html=True
        # )
        
        # FIX: Asegurar que l10n_mx_edi_post_time sea la hora actual para evitar problemas
        # de "Fecha y hora de generación fuera de rango"
        _logger.info(f"[AS_MX_INVOICE_DEBUG] Actualizando l10n_mx_edi_post_time a hora actual")
        
        # AJUSTE ESPECÍFICO: Solución para problema de zona horaria (diferencia de 6 horas)
        # Aseguramos que la fecha siempre esté en la zona horaria correcta de México
        now_utc = datetime.now(pytz.UTC)
        now_mx = now_utc.astimezone(mexico_tz)
        
        # Log detallado para debug de zonas horarias
        _logger.info(f"[AS_MX_TIMEZONE_DEBUG] Factura ID: {self.id}, Nombre: {self.name}")
        _logger.info(f"[AS_MX_TIMEZONE_DEBUG] Hora UTC actual: {now_utc}")
        _logger.info(f"[AS_MX_TIMEZONE_DEBUG] Hora México actual: {now_mx}")
        _logger.info(f"[AS_MX_TIMEZONE_DEBUG] Diferencia horaria: {(now_utc - now_mx).total_seconds() / 3600} horas")
        _logger.info(f"[AS_MX_TIMEZONE_DEBUG] Valor anterior de l10n_mx_edi_post_time: {self.l10n_mx_edi_post_time}")
        
        # Actualizamos el campo post_time directamente con la hora de México (sin convertir a UTC)
        # Ya que el SAT espera la hora de México, no UTC
        self.l10n_mx_edi_post_time = now_mx.replace(tzinfo=None)
        
        # Log confirmación de actualización
        _logger.info(f"[AS_MX_TIMEZONE_DEBUG] NUEVO valor de l10n_mx_edi_post_time: {self.l10n_mx_edi_post_time}")
        _logger.info(f"[AS_MX_TIMEZONE_DEBUG] Timezone info eliminado: {self.l10n_mx_edi_post_time.tzinfo is None}")
        
        # Verificar si ya existe una fecha en cfdi_values y guardarla para debug
        if 'fecha' in cfdi_values:
            _logger.info(f"[AS_MX_TIMEZONE_DEBUG] Valor existente de 'fecha' en cfdi_values: {cfdi_values['fecha']}")
            
        # Forzar la fecha directamente en cfdi_values para asegurar que se use la de México
        fecha_formateada = now_mx.strftime('%Y-%m-%dT%H:%M:%S')
        cfdi_values['fecha'] = fecha_formateada
        _logger.info(f"[AS_MX_TIMEZONE_DEBUG] FORZANDO fecha en cfdi_values: {fecha_formateada}")
        
        # Log avanzado con la corrección específica
        tz_correction_info = f"""
<b>⚠️ CORRECCIÓN DE ZONA HORARIA APLICADA:</b><br/>
<hr/>
<b>Problema:</b> Se detectó una diferencia de zona horaria que causa el error "401 Fecha y hora de generación fuera de rango"<br/>
<b>Causa:</b> El sistema está usando UTC mientras que el SAT verifica con hora México (diferencia de 6 horas)<br/>
<br/>
<b>Hora actual UTC:</b> {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}<br/>
<b>Hora actual México:</b> {now_mx.strftime('%Y-%m-%d %H:%M:%S %Z')}<br/>
<b>Hora asignada para timbrado:</b> {self.l10n_mx_edi_post_time.strftime('%Y-%m-%d %H:%M:%S %Z')}<br/>
<hr/>
<i>La fecha ha sido corregida explícitamente para coincidir con la zona horaria de México requerida por el SAT.</i>
        """
        
        # self.message_post(
        #     body=tz_correction_info,
        #     subject="Corrección de Zona Horaria para CFDI",
        #     message_type='comment',
        #     subtype_xmlid='mail.mt_note',
        #     body_is_html=True
        # )
        
        self._as_debug_log(f"l10n_mx_edi_post_time actualizado a: {self.l10n_mx_edi_post_time}")
            
        # Capturar los valores CFDI antes de ejecutar el método original
        tipo_cambio_original = cfdi_values.get('tipo_cambio', 'No definido')
        self._as_debug_log(f"Valor tipo_cambio ANTES de super(): {tipo_cambio_original}")
        
        # Primero, dejamos que la función original haga todo su trabajo
        super()._l10n_mx_edi_add_invoice_cfdi_values(cfdi_values)
        
        # Verificar el valor después del super()
        tipo_cambio_despues = cfdi_values.get('tipo_cambio', 'No definido')
        self._as_debug_log(f"Valor tipo_cambio DESPUÉS de super(): {tipo_cambio_despues}")
        
        # Log para verificar la fecha que se está usando en el CFDI
        fecha_cfdi = cfdi_values.get('fecha', 'No definido')
        _logger.info(f"[AS_MX_TIMEZONE_DEBUG] FECHA FINAL EN CFDI: {fecha_cfdi}")
        _logger.info(f"[AS_MX_TIMEZONE_DEBUG] Comparación: l10n_mx_edi_post_time = {self.l10n_mx_edi_post_time}")

        # Ahora, corregir el tipo de cambio para monedas que no son MXN
        if self.currency_id.name != 'MXN':
            _logger.info(f"[AS_MX_INVOICE_DEBUG] Corrigiendo tipo de cambio para {self.currency_id.name}")
            
            # Información de monedas y contexto
            ctx = dict(company_id=self.company_id.id, date=self.invoice_date)
            mxn = self.env.ref('base.MXN').with_context(ctx)
            invoice_currency = self.currency_id.with_context(ctx)
            
            self._as_debug_log(f"Contexto para conversión: company_id={self.company_id.id}, date={self.invoice_date}")
            self._as_debug_log(f"ID Moneda MXN: {mxn.id}, ID Moneda factura: {invoice_currency.id}")
            
            try:
                # Calcular el tipo de cambio (MXN por 1 unidad de moneda de factura)
                exchange_rate = invoice_currency._convert(
                    1.0, 
                    mxn, 
                    self.company_id, 
                    self.invoice_date or fields.Date.today(),
                    round=False
                )
                self._as_debug_log(f"Tipo de cambio calculado: {exchange_rate} (sin redondear)")
                
                # Redondear a 6 decimales
                exchange_rate_rounded = round(exchange_rate, 6)
                self._as_debug_log(f"Tipo de cambio redondeado a 6 decimales: {exchange_rate_rounded}")
                
                # Actualizar el valor en cfdi_values
                cfdi_values["tipo_cambio"] = exchange_rate_rounded
                self._as_debug_log(f"ACTUALIZADO tipo_cambio en cfdi_values a: {cfdi_values['tipo_cambio']}")
                
                # Verificar el valor de invoice_currency_rate
                self._as_debug_log(f"Valor actual de invoice_currency_rate: {self.invoice_currency_rate}")
                calculated_invoice_rate = 1.0 / exchange_rate_rounded if exchange_rate_rounded else 0
                self._as_debug_log(f"invoice_currency_rate calculado inverso (1/TC): {calculated_invoice_rate}")
                
                # Mensaje de éxito
                self._as_debug_log(f"✅ Corrección de tipo de cambio completada exitosamente")
                
            except Exception as e:
                error_detalle = traceback.format_exc()
                self._as_debug_log(f"❌ ERROR al calcular tipo de cambio: {str(e)}")
                _logger.error(f"[AS_MX_INVOICE_DEBUG] Error al calcular tipo de cambio: {str(e)}\n{error_detalle}")
        else:
            self._as_debug_log(f"No se requiere corrección de tipo de cambio para moneda MXN")

        # Recolectar y mostrar los datos clave para mostrar
        # Usamos .get() para evitar errores si alguna clave falta
        data_to_log = {
            "Emisor RFC": cfdi_values.get('emitter', {}).get('rfc'),
            "Receptor RFC": cfdi_values.get('receiver', {}).get('rfc'),
            "Fecha CFDI": cfdi_values.get('fecha'),
            "Moneda": cfdi_values.get('moneda'),
            "Tipo Cambio": cfdi_values.get('tipo_cambio'),
            "SubTotal": cfdi_values.get('subtotal'),
            "Descuento": cfdi_values.get('discount'),
            "Total": cfdi_values.get('total'),
            "Forma Pago": cfdi_values.get('forma_pago'),
            "Método Pago": cfdi_values.get('metodo_pago'),
            "Uso CFDI": cfdi_values.get('usage'),
            "Régimen Fiscal Receptor": cfdi_values.get('receiver', {}).get('fiscal_regime'),
            "Código Postal Lugar Expedición": cfdi_values.get('lugar_expedicion'),
            "Número Certificado": cfdi_values.get('certificate_number'),
            "Número Conceptos": len(cfdi_values.get('concepts', [])),
            "Impuestos Trasladados (resumen)": cfdi_values.get('taxes', {}).get('traslados'),
            "Impuestos Retenidos (resumen)": cfdi_values.get('taxes', {}).get('retenciones'),
            "CFDI Relacionado (Tipo)": cfdi_values.get('related_cfdi', [{}])[0].get('type'),
            "CFDI Relacionado (UUIDs)": ', '.join(cfdi_values.get('related_cfdi', [{}])[0].get('related_uuids', [])),
            "Errores Detectados (si los hay)": '<br/>'.join(cfdi_values.get('errors', [])),
        }

        # Formateamos como HTML para el chatter
        chatter_message = "<b>[AS] Datos CFDI Procesados:</b><br/>----------------------------------<br/>"
        for key, value in data_to_log.items():
            # Escapamos el valor por seguridad, por si tiene caracteres HTML
            safe_value = html_escape(str(value)) if value is not None else '<i>N/A</i>'
            chatter_message += f"<b>{html_escape(key)}:</b> {safe_value}<br/>"

        _logger.info(f"[AS_MX_INVOICE_DEBUG] Posteando datos CFDI en chatter para {self.name}")
        self._as_debug_log(f"FIN Procesamiento CFDI para factura {self.name} ({self.id})")
        
        # try:
        #     # self.message_post(
        #     #     body=chatter_message,
        #     #     subject=f"Datos CFDI Procesados para {self.name}",
        #     #     message_type='comment',
        #     #     subtype_xmlid='mail.mt_note',
        #     #     body_is_html=True
        #     # )
        # except Exception as chatter_err:
        #     _logger.error("[AS_MX_INVOICE_DEBUG] Fallo al postear datos CFDI en chatter: %s", chatter_err, exc_info=True)

        _logger.info("[AS_MX_INVOICE_DEBUG] Saliendo de _l10n_mx_edi_add_invoice_cfdi_values heredado")
        # No necesitamos devolver nada explícitamente, super() ya modificó cfdi_values in-place
        
    def l10n_mx_edi_get_xml_etree(self):
        """
        Propósito: Obtiene el árbol XML del CFDI de la factura.
        Retorno: Objeto ElementTree con el XML del CFDI, o False si no existe.
        """
        self.ensure_one()
        # Si no tenemos UUID, no hay XML
        if not self.l10n_mx_edi_cfdi_uuid:
            return False
            
        # Buscar adjuntos con el CFDI
        attachment = self.env['ir.attachment'].search([
            ('res_id', '=', self.id),
            ('res_model', '=', self._name),
            ('name', 'like', '%.xml')
        ], limit=1)
            
        if not attachment:
            return False
            
        # Intentar analizar el XML
        try:
            import base64
            from lxml import etree
            xml_content = base64.b64decode(attachment.datas)
            return etree.fromstring(xml_content)
        except Exception as e:
            _logger.error("Error al parsear XML del CFDI: %s", e)
            return False
    
    def l10n_mx_edi_get_tfd_etree(self, xml_etree):
        """
        Propósito: Obtiene el nodo TimbreFiscalDigital del XML del CFDI.
        Parámetros:
            xml_etree: ElementTree del XML del CFDI.
        Retorno: Diccionario con los atributos del nodo TimbreFiscalDigital, o un diccionario vacío si no existe.
        """
        if xml_etree is False:
            return {}
            
        try:
            # Definir namespace para buscar nodos en el XML
            namespaces = {
                'cfdi': 'http://www.sat.gob.mx/cfd/3',
                'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
            }
            
            # Buscar el nodo TimbreFiscalDigital
            node = xml_etree.xpath("//tfd:TimbreFiscalDigital", namespaces=namespaces)
            if not node:
                return {}
                
            # Devolver atributos como diccionario
            return node[0].attrib
        except Exception as e:
            _logger.error("Error al obtener TimbreFiscalDigital del CFDI: %s", e)
            return {}
    
    def get_l10n_mx_edi_qr_code_url(self):
        """
        Propósito: Genera la URL para el código QR del CFDI siguiendo el estándar del SAT.
        Retorno: URL completa para generar el código QR o cadena vacía si no hay datos suficientes.
        """
        self.ensure_one()
        
        _logger.info(f"[QR_DEBUG] Inicio generación QR para factura {self.id}, UUID: {self.l10n_mx_edi_cfdi_uuid}")
        
        if not self.l10n_mx_edi_cfdi_uuid:
            _logger.warning(f"[QR_DEBUG] No hay UUID para la factura {self.id}")
            return ''
            
        try:
            # Solo necesitamos los últimos 8 caracteres del sello
            xml = self.l10n_mx_edi_get_xml_etree()
            if not xml:
                _logger.warning(f"[QR_DEBUG] No se pudo obtener el XML para la factura {self.id}")
                return ''
                
            # Extraer y registrar datos básicos del XML
            _logger.info(f"[QR_DEBUG] XML obtenido correctamente. Nombre del nodo raíz: {xml.tag}")
            
            # Obtener el sello del XML
            sello = xml.get('Sello', '')
            if sello:
                sello_truncado = sello[-8:]
                _logger.info(f"[QR_DEBUG] Sello encontrado, longitud: {len(sello)}, últimos 8 caracteres: {sello_truncado}")
            else:
                _logger.warning(f"[QR_DEBUG] No se encontró el sello en el XML de la factura {self.id}")
                
                # Intento alternativo: buscar en el nodo TFD
                tfd = self.l10n_mx_edi_get_tfd_etree(xml)
                if tfd and 'SelloSAT' in tfd:
                    sello = tfd.get('SelloSAT', '')[-8:]
                    _logger.info(f"[QR_DEBUG] Usando SelloSAT como alternativa: {sello}")
                else:
                    _logger.warning(f"[QR_DEBUG] No se encontró el SelloSAT tampoco")
                    return ''
            
            # Verificar los valores de las variables para la URL
            supplier_rfc = self.l10n_mx_edi_cfdi_supplier_rfc
            customer_rfc = self.l10n_mx_edi_cfdi_customer_rfc
            amount = self.l10n_mx_edi_cfdi_amount
            
            _logger.info(f"[QR_DEBUG] Supplier RFC: {supplier_rfc}")
            _logger.info(f"[QR_DEBUG] Customer RFC: {customer_rfc}")
            _logger.info(f"[QR_DEBUG] Amount: {amount}")
            
            # Si alguno de los valores críticos no está disponible, buscarlos directamente en el XML
            if not supplier_rfc or not customer_rfc or not amount:
                _logger.info(f"[QR_DEBUG] Valores faltantes, intentando extraer del XML...")
                try:
                    # Intentar extraer RFC del emisor
                    if not supplier_rfc and xml.get('Emisor') is not None:
                        supplier_rfc = xml.find('.//Emisor').get('Rfc', '')
                        _logger.info(f"[QR_DEBUG] Supplier RFC extraído del XML: {supplier_rfc}")
                    
                    # Intentar extraer RFC del receptor
                    if not customer_rfc and xml.get('Receptor') is not None:
                        customer_rfc = xml.find('.//Receptor').get('Rfc', '')
                        _logger.info(f"[QR_DEBUG] Customer RFC extraído del XML: {customer_rfc}")
                    
                    # Intentar extraer el monto total
                    if not amount:
                        amount_str = xml.get('Total', '0.0')
                        try:
                            amount = float(amount_str)
                            _logger.info(f"[QR_DEBUG] Amount extraído del XML: {amount}")
                        except ValueError:
                            _logger.warning(f"[QR_DEBUG] No se pudo convertir el monto '{amount_str}' a float")
                    
                except Exception as xml_extract_error:
                    _logger.error(f"[QR_DEBUG] Error extrayendo datos del XML: {xml_extract_error}")
            
            # Formatear los parámetros con los datos necesarios
            qr_params = {
                'id': self.l10n_mx_edi_cfdi_uuid or '',
                're': supplier_rfc or '',
                'rr': customer_rfc or '',
                'tt': "{:.6f}".format(amount or 0.0),
            }
            
            # Log para depurar los parámetros
            _logger.info(f"[QR_DEBUG] Parámetros QR: {qr_params}")
            
            # Construir la URL base
            url_base = "https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?"
            
            # Construir la cadena de parámetros
            params = []
            for key, value in qr_params.items():
                params.append(f"{key}={value}")
            
            # Agregar el sello al final
            params.append(f"fe={sello_truncado if 'sello_truncado' in locals() else sello}")
            
            # Construir la URL completa
            url = url_base + "&".join(params)
            _logger.info(f"[QR_DEBUG] URL completa antes de codificar: {url}")
            
            # Generar la URL para el código de barras
            barcode_url = f'/report/barcode/?barcode_type=QR&width=120&height=120&value={url_quote_plus(url)}'
            _logger.info(f"[QR_DEBUG] URL final del código de barras: {barcode_url}")
            
            return barcode_url
            
        except Exception as e:
            _logger.error(f"[QR_DEBUG] Error al generar URL para QR CFDI: {str(e)}")
            _logger.error(traceback.format_exc())
            return ''
    
    def l10n_mx_edi_get_et_etree(self, xml_etree):
        """
        Propósito: Obtiene información adicional del XML del CFDI (uso futuro).
        Parámetros:
            xml_etree: ElementTree del XML del CFDI.
        Retorno: Diccionario con información adicional o un diccionario vacío si no existe.
        """
        # Por ahora, retorna un diccionario vacío ya que no se utiliza en el reporte
        return {}
        
    def _get_l10n_mx_edi_cadena(self):
        """
        Propósito: Obtiene la cadena original del CFDI para verificación.
        Retorno: Cadena original del CFDI o cadena vacía si no se puede obtener.
        """
        self.ensure_one()
        xml_etree = self.l10n_mx_edi_get_xml_etree()
        if not xml_etree:
            return ""
            
        try:
            # Aquí iría la lógica para generar la cadena original
            # Como es complejo y requiere XSLT del SAT, simplemente retornamos una cadena que indica que
            # se necesitaría implementar o usar el método nativo de Odoo si existe
            if hasattr(self, '_l10n_mx_edi_get_cadena'):
                return self._l10n_mx_edi_get_cadena()
            return "Cadena original (requiere implementación)"
        except Exception as e:
            _logger.error("Error al generar cadena original del CFDI: %s", e)
            return ""
        
    def _l10n_mx_edi_get_invoice_cfdi_values(self, edi_format):
        """Sobrescribe el método original para corregir el tipo de cambio cuando la moneda es USD.
        En lugar de devolver 1.0 hardcodeado, calcula el tipo de cambio real.
        """
        # Logging detallado para rastreo
        self._as_debug_log(f"INICIO _l10n_mx_edi_get_invoice_cfdi_values para factura {self.name}")
        self._as_debug_log(f"Moneda: {self.currency_id.name}, Fecha: {self.invoice_date}")
        self._as_debug_log(f"Método ejecutándose en: {self._name}.{self.id}")
        
        # Obtener los valores originales
        try:
            self._as_debug_log("Llamando a super()._l10n_mx_edi_get_invoice_cfdi_values")
            vals = super()._l10n_mx_edi_get_invoice_cfdi_values(edi_format)
            self._as_debug_log(f"Retorno de super(): {vals.get('currency_conversion_rate', 'No existe la clave')}")
        except Exception as e:
            error_trace = traceback.format_exc()
            self._as_debug_log(f"❌ ERROR al llamar super(): {str(e)}")
            _logger.error(f"[AS_MX_INVOICE_DEBUG] Error en super()._l10n_mx_edi_get_invoice_cfdi_values: {e}\n{error_trace}")
            raise
        
        # Corregir el tipo de cambio para USD y otras monedas extranjeras
        if self.currency_id.name != 'MXN':
            self._as_debug_log(f"Corrigiendo currency_conversion_rate para {self.currency_id.name}")
            try:
                ctx = dict(company_id=self.company_id.id, date=self.invoice_date)
                mxn = self.env.ref('base.MXN').with_context(ctx)
                invoice_currency = self.currency_id.with_context(ctx)
                
                # Calculando tipo de cambio
                old_rate = vals.get('currency_conversion_rate', 'No definido')
                self._as_debug_log(f"Tipo de cambio actual en vals: {old_rate}")
                
                # Redondear a 6 decimales como en el módulo original
                new_rate = round(
                    invoice_currency._convert(1, mxn, self.company_id, self.invoice_date or fields.Date.today(), round=False),
                    6
                )
                vals['currency_conversion_rate'] = new_rate
                self._as_debug_log(f"✅ Tipo de cambio USD calculado correctamente: {new_rate}")
            except Exception as e:
                error_trace = traceback.format_exc()
                self._as_debug_log(f"❌ ERROR al calcular tipo de cambio: {str(e)}")
                _logger.error(f"[AS_MX_INVOICE_DEBUG] Error al calcular tipo de cambio: {e}\n{error_trace}")
        else:
            self._as_debug_log(f"No se requiere corrección de tipo de cambio para moneda MXN")
        
        self._as_debug_log(f"FIN _l10n_mx_edi_get_invoice_cfdi_values, retornando vals")
        return vals

    # Agregar método para la corrección directa del tipo de cambio
    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        """
        Propósito: Sobrescribe el método estándar de _get_conversion_rate para
                   asegurar que se use el tipo de cambio correcto del día.
        
        Retorno: Tipo de cambio correcto.
        """
        # Añadir logs para entender el flujo
        self._as_debug_log(f"[_get_conversion_rate] INICIO - From: {from_currency.name}, To: {to_currency.name}, Date: {date}")
        
        try:
            # Llamar al método original
            conversion_rate = super()._get_conversion_rate(from_currency, to_currency, company, date)
            self._as_debug_log(f"[_get_conversion_rate] Tipo original: {conversion_rate}")
            
            # Corregir solo para monedas extranjeras (no MXN)
            if from_currency.name == 'MXN' and to_currency.name != 'MXN':
                self._as_debug_log(f"[_get_conversion_rate] Corrección necesaria para {to_currency.name}")
                
                # El tipo correcto debe ser: MXN -> Divisa
                # Pero en el contexto de Odoo, es: Divisa -> MXN (precio en divisa * tipo = precio en MXN)
                # Por tanto necesitamos el inverso
                correct_rate = to_currency._convert(1.0, from_currency, company, date, round=False)
                inverse_rate = 1.0 / correct_rate if correct_rate else 0.0
                self._as_debug_log(f"[_get_conversion_rate] Tipo correcto calculado: {inverse_rate}")
                
                return inverse_rate
            
            self._as_debug_log(f"[_get_conversion_rate] Retornando tipo sin cambios: {conversion_rate}")
            return conversion_rate
        except Exception as e:
            self._as_debug_log(f"[_get_conversion_rate] ERROR: {e}")
            # En caso de error, devolvemos el resultado del método original
            return super()._get_conversion_rate(from_currency, to_currency, company, date)

    # # Sobrescribir _compute_invoice_currency_rate para asegurarnos que las facturas USD
    # # tienen el tipo de cambio correcto
    # @api.depends('currency_id', 'company_currency_id', 'company_id', 'date')
    # def _compute_invoice_currency_rate(self):
    #     """
    #     Propósito: Sobrescribe el método de cálculo del tipo de cambio para 
    #                asegurar que se aplique el valor correcto para facturas en USD.
    #     """
    #     self._as_debug_log(f"[_compute_invoice_currency_rate] INICIO - Moneda: {self.currency_id.name}")
        
    #     # Llamar primero al método original
    #     super()._compute_invoice_currency_rate()
        
    #     # Verificar el valor calculado
    #     self._as_debug_log(f"[_compute_invoice_currency_rate] Valor después de super(): {self.invoice_currency_rate}")
        
    #     # Corregir solo para facturas en USD u otras divisas que no sean MXN
    #     if self.is_invoice(include_receipts=True) and self.currency_id and self.currency_id.name != 'MXN':
    #         self._as_debug_log(f"[_compute_invoice_currency_rate] Corrigiendo tipo de cambio para {self.currency_id.name}")
    #         try:
    #             # Fecha en formato correcto
    #             date = self.invoice_date or fields.Date.context_today(self)
                
    #             # Calcular el tipo correcto directamente
    #             ctx = dict(company_id=self.company_id.id, date=date)
    #             mxn = self.env.ref('base.MXN').with_context(ctx)
    #             invoice_currency = self.currency_id.with_context(ctx)
                
    #             # Tipo de cambio CORRECTO es: Cuántos MXN equivalen a 1 USD
    #             correct_rate = invoice_currency._convert(1.0, mxn, self.company_id, date, round=False)
                
    #             # Valor de invoice_currency_rate debe ser: Cuántos USD equivalen a 1 MXN
    #             # Por eso necesitamos el inverso
    #             inverse_rate = 1.0 / correct_rate if correct_rate else 0.0
                
    #             # Actualizar solo si hay diferencia significativa
    #             if abs(self.invoice_currency_rate - inverse_rate) > 0.00001:
    #                 self._as_debug_log(f"[_compute_invoice_currency_rate] Valor original: {self.invoice_currency_rate}, Nuevo: {inverse_rate}")
    #                 self.invoice_currency_rate = inverse_rate
    #             else:
    #                 self._as_debug_log(f"[_compute_invoice_currency_rate] No hay cambio significativo")
    #         except Exception as e:
    #             self._as_debug_log(f"[_compute_invoice_currency_rate] ERROR: {e}")
    #     else:
    #         self._as_debug_log(f"[_compute_invoice_currency_rate] No requiere corrección")
        
    #     self._as_debug_log(f"[_compute_invoice_currency_rate] FIN - Valor final: {self.invoice_currency_rate}")

    def _extract_cfdi_values_from_attachment(self):
        """
        Propósito: Extrae los valores del CFDI directamente del archivo XML adjunto.
        Retorno: Diccionario con los valores extraídos o diccionario vacío si hay error.
        """
        self.ensure_one()
        result = {}
        
        if not self.l10n_mx_edi_cfdi_uuid or not self.l10n_mx_edi_cfdi_attachment_id:
            return result
            
        try:
            _logger.info(f"[CFDI_EXTRACT] Intentando extraer valores CFDI de adjunto para factura {self.id}")
            
            # Intentamos decodificar el contenido XML
            attachment = self.l10n_mx_edi_cfdi_attachment_id
            xml_content = base64.b64decode(attachment.datas)
            
            # Parseamos el XML
            from lxml import etree
            tree = etree.fromstring(xml_content)
            
            # Definimos los namespaces
            nsmap = {
                'cfdi': 'http://www.sat.gob.mx/cfd/3',
                'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
            }
            
            # Extraemos UUID
            tfd_node = tree.xpath("//tfd:TimbreFiscalDigital", namespaces=nsmap)
            if tfd_node:
                result['uuid'] = tfd_node[0].get('UUID')
                result['sello_sat'] = tfd_node[0].get('SelloSAT')
                result['sello_cfd'] = tfd_node[0].get('SelloCFD')
                result['fecha_timbrado'] = tfd_node[0].get('FechaTimbrado')
                _logger.info(f"[CFDI_EXTRACT] TFD encontrado con UUID: {result.get('uuid')}")
            
            # Extraemos información del emisor
            emisor_node = tree.xpath("//cfdi:Emisor", namespaces=nsmap)
            if emisor_node:
                result['rfc_emisor'] = emisor_node[0].get('Rfc')
                result['nombre_emisor'] = emisor_node[0].get('Nombre')
                _logger.info(f"[CFDI_EXTRACT] Emisor encontrado: {result.get('rfc_emisor')}")
            
            # Extraemos información del receptor
            receptor_node = tree.xpath("//cfdi:Receptor", namespaces=nsmap)
            if receptor_node:
                result['rfc_receptor'] = receptor_node[0].get('Rfc')
                result['nombre_receptor'] = receptor_node[0].get('Nombre')
                _logger.info(f"[CFDI_EXTRACT] Receptor encontrado: {result.get('rfc_receptor')}")
            
            # Extraemos información del comprobante
            result['total'] = tree.get('Total')
            result['subtotal'] = tree.get('SubTotal')
            result['sello'] = tree.get('Sello')
            result['fecha'] = tree.get('Fecha')
            result['tipo_comprobante'] = tree.get('TipoDeComprobante')
            
            _logger.info(f"[CFDI_EXTRACT] Valores extraídos: Total={result.get('total')}, Fecha={result.get('fecha')}")
            
            return result
            
        except Exception as e:
            _logger.error(f"[CFDI_EXTRACT] Error al extraer valores CFDI: {str(e)}")
            _logger.error(traceback.format_exc())
            return {}
    
    def get_l10n_mx_edi_qr_code_url_alternative(self):
        """
        Propósito: Método alternativo para generar la URL del código QR si el método principal falla.
        Retorno: URL para el código QR o cadena vacía.
        """
        self.ensure_one()
        
        _logger.info(f"[QR_DEBUG_ALT] Intentando método alternativo para QR de factura {self.id}")
        
        try:
            # Extraer directamente los valores del XML
            cfdi_values = self._extract_cfdi_values_from_attachment()
            
            if not cfdi_values:
                _logger.warning(f"[QR_DEBUG_ALT] No se pudieron extraer valores CFDI para la factura {self.id}")
                return ''
            
            _logger.info(f"[QR_DEBUG_ALT] Valores CFDI extraídos: {cfdi_values}")
            
            # Verificar que tenemos los valores necesarios
            uuid = cfdi_values.get('uuid')
            rfc_emisor = cfdi_values.get('rfc_emisor')
            rfc_receptor = cfdi_values.get('rfc_receptor')
            total = cfdi_values.get('total')
            sello = cfdi_values.get('sello') or cfdi_values.get('sello_cfd')
            
            if not uuid or not rfc_emisor or not rfc_receptor or not total or not sello:
                _logger.warning(f"[QR_DEBUG_ALT] Faltan valores requeridos para generar QR")
                return ''
            
            # Formatear la URL
            try:
                total_float = float(total)
                total_formatted = "{:.6f}".format(total_float)
            except ValueError:
                _logger.warning(f"[QR_DEBUG_ALT] No se pudo convertir el total '{total}' a float")
                total_formatted = "0.000000"
            
            # Obtener los últimos 8 caracteres del sello
            sello_truncado = sello[-8:] if len(sello) >= 8 else sello
            
            # Construir URL base
            url_base = "https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?"
            
            # Construir parámetros
            params = [
                f"id={uuid}",
                f"re={rfc_emisor}",
                f"rr={rfc_receptor}",
                f"tt={total_formatted}",
                f"fe={sello_truncado}"
            ]
            
            # Construir URL completa
            url = url_base + "&".join(params)
            _logger.info(f"[QR_DEBUG_ALT] URL completa: {url}")
            
            # Generar URL del código de barras
            barcode_url = f'/report/barcode/?barcode_type=QR&width=120&height=120&value={url_quote_plus(url)}'
            _logger.info(f"[QR_DEBUG_ALT] URL código de barras: {barcode_url}")
            
            return barcode_url
            
        except Exception as e:
            _logger.error(f"[QR_DEBUG_ALT] Error generando URL alternativa: {str(e)}")
            _logger.error(traceback.format_exc())
            return ''

    # def action_invoice_sent(self):
    #     """
    #     Propósito: Hereda action_invoice_sent para agregar logging del template de email usado.
    #     Retorno: Resultado de la función original
    #     """
    #     self.ensure_one()
        
    #     # Obtener el template que se va a usar
    #     template = self.env.ref('as_sale_pricelist.email_template_edi_invoice2', raise_if_not_found=False)
    #     if template:
    #         _logger.info("[action_invoice_sent] Template ID: %s, Template Name: %s, Invoice: %s", 
    #                     template.id, template.name, self.name)
    #     else:
    #         _logger.error("[action_invoice_sent] No se encontró template account.email_template_edi_invoice para factura: %s", 
    #                      self.name)
        
    #     # Llamar a la función original
    #     return super().action_invoice_sent()

# Asegúrate de que este archivo se importe en el __init__.py de la carpeta 'models'
# Ejemplo: from . import as_mx_invoice_move

# ... (resto del archivo si existe) ...
# Agregar '// ... existing code ...' si es necesario para indicar dónde insertar esto
# Si el archivo no existe, este será el contenido completo.
# Si el archivo existe, buscar la clase que hereda de 'account.move' o crearla.

# ... (resto del archivo si existe) ... 

class AsMailRenderMixin(models.AbstractModel):
    """
    Propósito: Hereda mail.render.mixin para agregar logging específico en el renderizado de templates.
    """
    _inherit = 'mail.render.mixin'

    @api.model
    def _render_template_qweb(self, template_src, model, res_ids, add_context=None, options=None):
        """
        Propósito: Sobrescribe _render_template_qweb para agregar logging detallado del template que se está renderizando.
        Parámetros:
            template_src: Código fuente del template QWeb
            model: Modelo de los registros
            res_ids: IDs de los registros
            add_context: Contexto adicional
            options: Opciones de renderizado
        Retorno: Resultado del renderizado
        """
        # Loguear información del template antes del renderizado
        _logger.info("[_render_template_qweb] Iniciando renderizado para modelo: %s, registros: %s", model, res_ids)
        
        if template_src:
            # Extraer información útil del template
            template_preview = template_src[:200] + "..." if len(template_src) > 200 else template_src
            _logger.info("[_render_template_qweb] Template preview: %s", template_preview)
            
            # Buscar si contiene payment_state incorrectos
            if 'invoice_payment_state' in template_src:
                _logger.error("[_render_template_qweb] ¡CAMPO INCORRECTO DETECTADO! Template contiene 'invoice_payment_state' en lugar de 'payment_state'")
        
        try:
            # Llamar al método original
            result = super()._render_template_qweb(template_src, model, res_ids, add_context, options)
            _logger.info("[_render_template_qweb] Renderizado completado exitosamente para %s registros", len(res_ids))
            return result
        except Exception as e:
            _logger.error("[_render_template_qweb] Error en renderizado: %s", str(e))
            _logger.error("[_render_template_qweb] Template que falló: %s", template_src[:500] if template_src else "Sin template")
            _logger.error("[_render_template_qweb] Modelo: %s, IDs: %s", model, res_ids)
            raise

class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    def button_as_manual_cfdi_sign(self):
        for payment in self:
            payment.move_id.as_action_manual_l10n_mx_edi_cfdi_try_send()
            
    def tasa_cambio(self):
        for payment in self:
            if payment.manual_currency_rate_active:
                cambio = payment.manual_currency_rate
            else:
                if payment.currency_id == payment.company_id.currency_id:
                    cambio = self.compute_rate_xml()
                else:
                    cambio = payment.amount/payment.amount_company_currency_signed
            return cambio

    def compute_rate_xml(self):
        """
        Extracts exchange rate from EDI XML document
        Updated for CFDI 4.0 namespace handling
        """
        for payment in self:
            rate = 1.0
            if payment.l10n_mx_edi_payment_document_ids and payment.l10n_mx_edi_payment_document_ids[0].attachment_id:
                try:
                    xml_content = base64.b64decode(payment.l10n_mx_edi_payment_document_ids[0].attachment_id.datas).decode()
                    root = ET.fromstring(xml_content)
                    namespaces = {
                        'cfdi': 'http://www.sat.gob.mx/cfd/4',
                        'pago20': 'http://www.sat.gob.mx/Pagos20'
                    }
                    docto = root.find('.//pago20:Pago', namespaces)
                    if docto is not None:
                        rate = float(docto.get('TipoCambioP', '1.0'))
                except Exception as e:
                    rate = 1.0
            return rate