# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
import traceback
from odoo.tools.float_utils import float_round, float_is_zero
import re
from markupsafe import escape as html_escape
import json
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)

# Precisión para EQUIVALENCIADR en el XML del complemento de pago
EQUIVALENCIADR_PRECISION_DIGITS = 10

class AsAccountEdiFormatPayment(models.Model):
    _inherit = 'account.edi.format'
    
    def _as_debug_log(self, message, move=None):
        """
        Propósito: Función de utilidad para loguear mensajes de debug
        Parámetros: 
            message - mensaje a loguear
            move - movimiento contable opcional para loguear en su chatter
        """
        trace_id = f"PAYMENT-CFDI-{fields.Datetime.now():%Y%m%d%H%M%S}"
        _logger.info(f"[AS_MX_PAYMENT_DEBUG][{trace_id}] {message}")
        
        # Si se proporcionó un movimiento, registramos en su chatter
        if move and hasattr(move, 'message_post'):
            try:
                # Usar una variable de contexto para prevenir recursión
                if not self.env.context.get('skip_chatter_log'):
                    # Evitar que se llene el chatter con logs repetitivos usando un contexto modificado
                    ctx = dict(self.env.context, skip_chatter_log=True)
                    move.with_context(ctx).sudo().message_post(
                        body=f"<p><b>[CFDI Pago {trace_id}]:</b> {message}</p>",
                        subject="CFDI Complemento de Pago",
                        message_type='comment',
                        subtype_xmlid='mail.mt_note',
                        body_is_html=True
                    )
            except Exception as e:
                _logger.error(f"Error al postear en chatter: {e}. Continúa el proceso.")
        
    def _l10n_mx_edi_get_payment_cfdi_values(self, move):
        """
        Propósito: Sobrescribe el método para modificar el cálculo del tipo de cambio 
                para complementos de pago, permitiendo usar tasas manuales si están definidas.
        Parámetros:
            move: El movimiento contable (account.move) que representa el pago
        Retorno: Diccionario con los valores para generar el CFDI de pago
        """
        self._as_debug_log(f"Iniciando cálculo de valores CFDI para el pago {move.name} (ID: {move.id})", move)

        def get_tax_cfdi_name(tax_detail_vals):
            """Determina el nombre del impuesto CFDI"""
            tags = set()
            for detail in tax_detail_vals['group_tax_details']:
                for tag in detail['tax_repartition_line_id'].tag_ids:
                    tags.add(tag)
            tags = list(tags)
            if len(tags) == 1:
                return {'ISR': '001', 'IVA': '002', 'IEPS': '003'}.get(tags[0].name)
            elif tax_detail_vals['tax'].l10n_mx_tax_type == 'Exento':
                return '002'
            else:
                return None

        def divide_tax_details(invoice, tax_details, amount_paid):
            """Divide los detalles de impuestos proporcionalmente al pago"""
            percentage_paid = amount_paid / invoice.amount_total
            precision = invoice.currency_id.decimal_places
            sign = -1 if invoice.is_inbound() else 1
            for detail in tax_details['tax_details'].values():
                tax = detail['tax']
                tax_amount = abs(tax.amount) / 100.0 if tax.amount_type != 'fixed' else abs(detail['tax_amount_currency'] / detail['base_amount_currency'])
                base_val_proportion = float_round(detail['base_amount_currency'] * percentage_paid * sign, precision)
                tax_val_proportion = float_round(base_val_proportion * tax_amount, precision)
                detail.update({
                    'base_val_prop_amt_curr': base_val_proportion,
                    'tax_val_prop_amt_curr': tax_val_proportion if tax.l10n_mx_tax_type != 'Exento' else False,
                    'tax_class': get_tax_cfdi_name(detail),
                    'tax_amount': tax_amount,
                })
            return tax_details

        # Inicialización de variables
        tasa = 0
        
        # IMPORTANTE: Generamos logs de diagnóstico sobre el pago
        payment_info = {
            'Documento': move.name,
            'Estado': move.state,
            'Fecha': fields.Date.to_string(move.date),
            'Moneda': move.currency_id.name,
            'Cuenta bancaria': move.journal_id.bank_account_id.acc_number if move.journal_id.bank_account_id else 'No definida',
            'Método de pago': move.l10n_mx_edi_payment_method_id.name if move.l10n_mx_edi_payment_method_id else 'No definido'
        }
        payment_info_html = "<br/>".join([f"<b>{k}:</b> {v}" for k, v in payment_info.items()])
        self._as_debug_log(f"<b>INFORMACIÓN DEL PAGO:</b><br/>{payment_info_html}", move)
        
        # IMPORTANTE: Aquí está la modificación clave para usar tasa manual si existe
        if move.payment_id:
            currency = move.payment_id.currency_id
            total_amount = move.payment_id.amount
            
            # Registro detallado de la moneda del pago
            currency_info = {
                'Moneda de pago': currency.name,
                'Decimales': currency.decimal_places,
                'Es moneda mexicana': 'Sí' if currency.name == 'MXN' else 'No'
            }
            self._as_debug_log(f"<b>INFORMACIÓN DE MONEDA:</b><br/>{html_escape('<br/>'.join([f'{k}: {v}' for k, v in currency_info.items()]))}", move)
            
            if move.payment_id.manual_currency_rate > 0 and move.payment_id.manual_currency_rate_active:
                tasa = move.payment_id.manual_currency_rate
                self._as_debug_log(f"<b>USANDO TIPO DE CAMBIO MANUAL:</b> {tasa}<br/><em>(Campo manual_currency_rate activado)</em>", move)
            else:
                self._as_debug_log(f"No hay tipo de cambio manual configurado. Monto: {total_amount} {currency.name}", move)
        else:
            if move.statement_line_id.foreign_currency_id:
                total_amount = move.statement_line_id.amount_currency
                currency = move.statement_line_id.foreign_currency_id
                self._as_debug_log(f"Usando moneda extranjera de extracto bancario: {currency.name}, Monto: {total_amount}", move)
            else:
                total_amount = move.statement_line_id.amount
                currency = move.statement_line_id.currency_id
                self._as_debug_log(f"Usando moneda local de extracto bancario: {currency.name}, Monto: {total_amount}", move)

        # Process reconciled invoices.
        invoice_vals_list = []
        pay_rec_lines = move.line_ids.filtered(lambda line: line.account_internal_type in ('receivable', 'payable'))
        paid_amount = abs(sum(pay_rec_lines.mapped('amount_currency')))
        self._as_debug_log(f"Monto total pagado (amount_currency): {paid_amount} {move.currency_id.name}", move)

        mxn_currency = self.env["res.currency"].search([('name', '=', 'MXN')], limit=1)
        if move.currency_id == mxn_currency:
            rate_payment_curr_mxn = None
            paid_amount_comp_curr = paid_amount
            self._as_debug_log(f"El pago ya está en MXN. No se requiere conversión de moneda.", move)
        else:
            # Aquí usamos la tasa manual si está disponible
            if tasa > 0:
                self._as_debug_log(f"<b>APLICANDO TASA MANUAL</b>: 1 {move.currency_id.name} = {tasa} MXN", move)
                rate_payment_curr_mxn = tasa
            else:
                self._as_debug_log(f"Calculando tipo de cambio automático para {move.currency_id.name} a MXN", move)
                rate_payment_curr_mxn = move.currency_id._convert(1.0, mxn_currency, move.company_id, move.date, round=False)
                self._as_debug_log(f"<b>TIPO DE CAMBIO CALCULADO</b>: 1 {move.currency_id.name} = {rate_payment_curr_mxn} MXN", move)
                
            paid_amount_comp_curr = move.company_currency_id.round(paid_amount * rate_payment_curr_mxn)
            self._as_debug_log(f"Monto pagado en moneda de la compañía: {paid_amount_comp_curr} {move.company_currency_id.name}", move)

        # Análisis de las facturas conciliadas
        facturas_info = []
        for field1, field2 in (('debit', 'credit'), ('credit', 'debit')):
            for partial in pay_rec_lines[f'matched_{field1}_ids']:
                payment_line = partial[f'{field2}_move_id']
                invoice_line = partial[f'{field1}_move_id']
                invoice_amount = partial[f'{field1}_amount_currency']
                exchange_move = invoice_line.full_reconcile_id.exchange_move_id
                invoice = invoice_line.move_id

                if not invoice.l10n_mx_edi_cfdi_request:
                    self._as_debug_log(f"⚠️ La factura {invoice.name} no requiere CFDI. Omitiendo.", move)
                    continue

                # Registramos información básica de la factura
                facturas_info.append({
                    'Factura': invoice.name,
                    'UUID': invoice.l10n_mx_edi_cfdi_uuid or 'No timbrada',
                    'Moneda': invoice_line.currency_id.name,
                    'Monto pagado': invoice_amount
                })

                if exchange_move:
                    exchange_partial = invoice_line[f'matched_{field2}_ids']\
                        .filtered(lambda x: x[f'{field2}_move_id'].move_id == exchange_move)
                    if exchange_partial:
                        invoice_amount += exchange_partial[f'{field2}_amount_currency']
                        self._as_debug_log(f"Ajuste por diferencia cambiaria aplicado a {invoice.name}. Nuevo monto: {invoice_amount}", move)

                if invoice_line.currency_id == payment_line.currency_id:
                    # Same currency
                    amount_paid_invoice_curr = invoice_amount
                    exchange_rate = None
                    self._as_debug_log(f"Factura {invoice.name} y pago usan la misma moneda ({invoice_line.currency_id.name}). No se requiere tipo de cambio.", move)
                else:
                    # It needs to be how much invoice currency you pay for one payment currency
                    amount_paid_invoice_comp_curr = payment_line.company_currency_id.round(
                        total_amount * (partial.amount / paid_amount_comp_curr))
                    invoice_rate = abs(invoice_line.amount_currency) / abs(invoice_line.balance)
                    amount_paid_invoice_curr = invoice_line.currency_id.round(partial.amount * invoice_rate)
                    exchange_rate = amount_paid_invoice_curr / amount_paid_invoice_comp_curr
                    exchange_rate = float_round(exchange_rate, precision_digits=EQUIVALENCIADR_PRECISION_DIGITS, rounding_method='UP')
                    self._as_debug_log(f"<b>Conversión de moneda para factura {invoice.name}:</b><br/>"
                                       f"- Monto pagado (moneda factura): {amount_paid_invoice_curr} {invoice_line.currency_id.name}<br/>"
                                       f"- Factor de conversión (EquivalenciaDR): {exchange_rate}", move)

                # for CFDI 4.0
                cfdi_values = self._l10n_mx_edi_get_invoice_cfdi_values(invoice)
                tax_details_transferred = divide_tax_details(invoice, cfdi_values['tax_details_transferred'], amount_paid_invoice_curr)
                tax_details_withholding = divide_tax_details(invoice, cfdi_values['tax_details_withholding'], amount_paid_invoice_curr)

                invoice_vals_list.append({
                    'invoice': invoice,
                    'exchange_rate': exchange_rate,
                    'EQUIVALENCIADR_PRECISION_DIGITS': EQUIVALENCIADR_PRECISION_DIGITS,
                    'payment_policy': invoice.l10n_mx_edi_payment_policy,
                    'number_of_payments': len(invoice._get_reconciled_payments()) + len(invoice._get_reconciled_statement_lines()),
                    'amount_paid': amount_paid_invoice_curr,
                    'amount_before_paid': min(invoice.amount_residual + amount_paid_invoice_curr, invoice.amount_total),
                    'tax_details_transferred': tax_details_transferred,
                    'tax_details_withholding': tax_details_withholding,
                    **self._l10n_mx_edi_get_serie_and_folio(invoice),
                })

        # Mostramos resumen de facturas relacionadas
        if facturas_info:
            facturas_html = "<ul>" + "".join([f"<li>{factura['Factura']} - {factura['Monto pagado']} {factura['Moneda']} (UUID: {factura['UUID']})</li>" for factura in facturas_info]) + "</ul>"
            self._as_debug_log(f"<b>FACTURAS RELACIONADAS:</b>{facturas_html}", move)
        else:
            self._as_debug_log("⚠️ <b>NO SE ENCONTRARON FACTURAS VÁLIDAS</b> relacionadas a este pago", move)

        payment_method_code = move.l10n_mx_edi_payment_method_id.code
        is_payment_code_emitter_ok = payment_method_code in ('02', '03', '04', '05', '06', '28', '29', '99')
        is_payment_code_receiver_ok = payment_method_code in ('02', '03', '04', '05', '28', '29', '99')
        is_payment_code_bank_ok = payment_method_code in ('02', '03', '04', '28', '29', '99')

        self._as_debug_log(f"<b>MÉTODO DE PAGO:</b> {payment_method_code} - Validaciones: "
                           f"Emisor OK: {is_payment_code_emitter_ok}, "
                           f"Receptor OK: {is_payment_code_receiver_ok}, "
                           f"Banco OK: {is_payment_code_bank_ok}", move)

        bank_accounts = move.partner_id.commercial_partner_id.bank_ids.filtered(lambda x: x.company_id.id in (False, move.company_id.id))

        partner_bank = bank_accounts[:1].bank_id
        if partner_bank.country and partner_bank.country.code != 'MX':
            partner_bank_vat = 'XEXX010101000'
        else:  # if no partner_bank (e.g. cash payment), partner_bank_vat is not set.
            partner_bank_vat = partner_bank.l10n_mx_edi_vat

        payment_account_ord = re.sub(r'\s+', '', bank_accounts[:1].acc_number or '') or None
        payment_account_receiver = re.sub(r'\s+', '', move.journal_id.bank_account_id.acc_number or '') or None

        self._as_debug_log(f"<b>INFORMACIÓN BANCARIA:</b><br/>"
                         f"- Cuenta ordenante: {payment_account_ord or 'No definida'}<br/>"
                         f"- Cuenta beneficiaria: {payment_account_receiver or 'No definida'}<br/>"
                         f"- RFC Banco ordenante: {partner_bank_vat or 'No definido'}", move)

        # CFDI 4.0: prepare the tax summaries
        rate_payment_curr_mxn_40 = rate_payment_curr_mxn or 1
        total_taxes_paid = {}
        total_taxes_withheld = {
            '001': {'amount_curr': 0.0, 'amount_mxn': 0.0},
            '002': {'amount_curr': 0.0, 'amount_mxn': 0.0},
            '003': {'amount_curr': 0.0, 'amount_mxn': 0.0},
            None: {'amount_curr': 0.0, 'amount_mxn': 0.0},
        }
        
        # Procesar impuestos
        self._as_debug_log("<b>PROCESANDO IMPUESTOS PARA CFDI 4.0</b>", move)
        for inv_vals in invoice_vals_list:
            wht_detail = list(inv_vals['tax_details_withholding']['tax_details'].values())
            trf_detail = list(inv_vals['tax_details_transferred']['tax_details'].values())
            for detail in wht_detail + trf_detail:
                tax = detail['tax']
                tax_class = detail['tax_class']
                key = (float_round(tax.amount / 100, 6), tax.l10n_mx_tax_type, tax_class)
                base_val_pay_curr = detail['base_val_prop_amt_curr'] / (inv_vals['exchange_rate'] or 1.0)
                tax_val_pay_curr = detail['tax_val_prop_amt_curr'] / (inv_vals['exchange_rate'] or 1.0)
                if key in total_taxes_paid:
                    total_taxes_paid[key]['base_value'] += base_val_pay_curr
                    total_taxes_paid[key]['tax_value'] += tax_val_pay_curr
                elif tax.amount >= 0:
                    total_taxes_paid[key] = {
                        'base_value': base_val_pay_curr,
                        'tax_value': tax_val_pay_curr,
                        'tax_amount': float_round(detail['tax_amount'], 6),
                        'tax_type': tax.l10n_mx_tax_type,
                        'tax_class': tax_class,
                        'tax_spec': 'W' if tax.amount < 0 else 'T',
                    }
                else:
                    total_taxes_withheld[tax_class]['amount_curr'] += tax_val_pay_curr

        # CFDI 4.0: rounding needs to be done after all DRs are added
        # We round up for the currency rate and down for the tax values because we lost a lot of time to find out
        # that Finkok only accepts it this way. The other PACs accept either way and are reasonable.
        tax_summary_html = "<ul>"
        for k, v in total_taxes_paid.items():
            v['base_value'] = float_round(v['base_value'], move.currency_id.decimal_places, rounding_method='HALF-UP')
            v['tax_value'] = float_round(v['tax_value'], move.currency_id.decimal_places, rounding_method='HALF-UP')
            v['base_value_mxn'] = float_round(v['base_value'] * rate_payment_curr_mxn_40, mxn_currency.decimal_places)
            v['tax_value_mxn'] = float_round(v['tax_value'] * rate_payment_curr_mxn_40, mxn_currency.decimal_places)
            tax_summary_html += f"<li>Impuesto {v['tax_class'] or 'No definido'} ({v['tax_type']}): Base={v['base_value']}, Impuesto={v['tax_value']}</li>"
        
        for tax_class, v in total_taxes_withheld.items():
            if v['amount_curr'] != 0:
                v['amount_curr'] = float_round(v['amount_curr'], move.currency_id.decimal_places, rounding_method='HALF-UP')
                v['amount_mxn'] = float_round(v['amount_curr'] * rate_payment_curr_mxn_40, mxn_currency.decimal_places)
                tax_summary_html += f"<li>Retención {tax_class or 'No definida'}: {v['amount_curr']}</li>"
                
        tax_summary_html += "</ul>"
        if tax_summary_html != "<ul></ul>":
            self._as_debug_log(f"<b>RESUMEN DE IMPUESTOS:</b>{tax_summary_html}", move)
        else:
            self._as_debug_log("<b>NO HAY IMPUESTOS</b> aplicables en este pago", move)

        cfdi_values = {
            **self._l10n_mx_edi_get_common_cfdi_values(move),
            'invoice_vals_list': invoice_vals_list,
            'currency': currency,
            'amount': total_amount,
            'amount_mxn': float_round(total_amount * rate_payment_curr_mxn_40, mxn_currency.decimal_places),
            'rate_payment_curr_mxn': rate_payment_curr_mxn,
            'rate_payment_curr_mxn_40': rate_payment_curr_mxn_40,
            'emitter_vat_ord': is_payment_code_emitter_ok and partner_bank_vat,
            'bank_vat_ord': is_payment_code_bank_ok and partner_bank.name,
            'payment_account_ord': is_payment_code_emitter_ok and payment_account_ord,
            'receiver_vat_ord': is_payment_code_receiver_ok and move.journal_id.bank_account_id.bank_id.l10n_mx_edi_vat,
            'payment_account_receiver': is_payment_code_receiver_ok and payment_account_receiver,
            'cfdi_date': move.l10n_mx_edi_post_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'tax_summary': total_taxes_paid,
            'withholding_summary': total_taxes_withheld,
        }

        cfdi_payment_datetime = fields.Datetime.from_string(move.date)
        cfdi_values['cfdi_payment_date'] = cfdi_payment_datetime.strftime('%Y-%m-%dT%H:%M:%S')

        if cfdi_values['customer'].country_id.l10n_mx_edi_code != 'MEX':
            cfdi_values['customer_fiscal_residence'] = cfdi_values['customer'].country_id.l10n_mx_edi_code
        else:
            cfdi_values['customer_fiscal_residence'] = None
        
        if hasattr(self, '_l10n_mx_edi_get_40_values'):
            cfdi_values.update(self._l10n_mx_edi_get_40_values(move))
            
        cfdi_resumen = {
            'Moneda': cfdi_values['currency'].name,
            'Monto': cfdi_values['amount'],
            'Tipo de cambio': cfdi_values['rate_payment_curr_mxn_40'],
            'Monto en MXN': cfdi_values['amount_mxn'],
            'Fecha CFDI': cfdi_values['cfdi_date'],
            'Fecha Pago': cfdi_values['cfdi_payment_date']
        }
        cfdi_resumen_html = "<br/>".join([f"<b>{k}:</b> {v}" for k, v in cfdi_resumen.items()])
        self._as_debug_log(f"<b>RESUMEN CFDI COMPLEMENTO DE PAGO:</b><br/>{cfdi_resumen_html}", move)
        
        self._as_debug_log(f"Finalizado proceso de cálculo de valores CFDI para complemento de pago {move.name}", move)
        return cfdi_values 
    
class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        res = super().action_post()
        for payment in self:
            if payment.payment_type =='inbound':
                if payment.journal_id.type == 'bank' and self.l10n_mx_edi_payment_method_id.code in ('01'):
                    raise UserError(_(
                    "La forma de pago no puede ser en Efectivo y tiene seleccionado un diario de banco."
                    ))
                if payment.journal_id.type == 'cash' and self.l10n_mx_edi_payment_method_id.code not in ('01'):
                    raise UserError(_(
                    "La forma de pago no puede ser diferente de Efectivo, y tiene seleccionado un diario que no es de Efectivo."
                    ))
                if self.l10n_mx_edi_payment_method_id.code in ('99'):
                    raise UserError(_(
                    "La forma de pago no puede dejarse sin definir."
                    ))
                    
        return res

    def button_as_manual_cfdi_sign(self):
        for payment in self:
            payment.move_id.as_action_manual_l10n_mx_edi_cfdi_try_send()