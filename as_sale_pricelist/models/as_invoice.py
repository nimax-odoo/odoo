# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
from collections import defaultdict
import logging
from odoo.tools import float_is_zero
import json

_logger = logging.getLogger(__name__)

class as_accountinvoice(models.Model):
    _inherit = "account.move"  

    @api.model
    def _get_invoice_in_payment_state(self):
        # OVERRIDE to enable the 'in_payment' state on invoices.
        return 'paid'

    def _reverse_moves(self, default_values_list=None, cancel=False):
        if not default_values_list:
            default_values_list = [{} for move in self]

        if cancel:
            lines = self.mapped('line_ids')
            # Avoid maximum recursion depth.
            if lines:
                lines.remove_move_reconcile()

        reverse_type_map = {
            'entry': 'entry',
            'out_invoice': 'out_refund',
            'out_refund': 'entry',
            'in_invoice': 'in_refund',
            'in_refund': 'entry',
            'out_receipt': 'entry',
            'in_receipt': 'entry',
        }

        move_vals_list = []
        for move, default_values in zip(self, default_values_list):
            default_values.update({
                'move_type': reverse_type_map[move.move_type],
                'reversed_entry_id': move.id,
            })
            move_vals_list.append(move.with_context(move_reverse_cancel=cancel)._reverse_move_vals(default_values, cancel=cancel))

        reverse_moves = self.env['account.move'].create(move_vals_list)
        # for move, reverse_move in zip(self, reverse_moves.with_context(check_move_validity=False, move_reverse_cancel=cancel)):
        #     # Update amount_currency if the date has changed.
        #     if move.date != reverse_move.date:
        #         for line in reverse_move.line_ids:
        #             if line.currency_id:
        #                 line._onchange_currency()
        #     reverse_move._recompute_dynamic_lines(recompute_all_taxes=False)
        reverse_moves._check_balanced()

        # Reconcile moves together to cancel the previous one.
        if cancel:
            reverse_moves.with_context(move_reverse_cancel=cancel)._post(soft=False)
            for move, reverse_move in zip(self, reverse_moves):
                group = defaultdict(list)
                for line in (move.line_ids + reverse_move.line_ids).filtered(lambda l: not l.reconciled):
                    group[(line.account_id, line.currency_id)].append(line.id)
                for (account, dummy), line_ids in group.items():
                    if account.reconcile or account.internal_type == 'liquidity':
                        self.env['account.move.line'].browse(line_ids).with_context(move_reverse_cancel=cancel).reconcile()

        return reverse_moves

    def button_process_edi_web_services(self):
        res = super().button_process_edi_web_services()

        for invoice in self:
            # == Create the attachment ==
            cfdi_filename = ('%s-%s-MX-Invoice-3.3.xml' % (invoice.journal_id.code, invoice.payment_reference or invoice.name)).replace('/', '')


            if cfdi_filename:
                name = str(cfdi_filename).split('.')[0]
                invoices = self.env['ir.attachment'].search([('name', '=', name and _("%s.pdf") % name),('res_id','=',self.id)])
                if not invoices:
                    modelo = 'account.move'
                    content = self.env.ref('as_sale_pricelist.as_account_invoices_new_mx')._render_qweb_pdf(invoice.id)[0]
                    cfdi_attachment = self.env['ir.attachment'].create({
                        'name': name and _("%s.pdf") % name or _("Factura_.pdf"),
                        'type': 'binary',
                        'datas': base64.b64encode(content),
                        'res_model': modelo,
                        'res_id': invoice.id,
                    })
        return res

    def _get_invoiced_lot_values1(self,product_id):
        """ Get and prepare data to show a table of invoiced lot on the invoice's report. """
        self.ensure_one()

        if self.state == 'draft':
            return res

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

    def as_get_name_invoice(self):
        for inv in self:
            as_name = ''
            if inv.move_type == 'out_invoice' and inv.state == 'posted':
                as_name = ('%s-%s-MX-Invoice-3.3.xml' % (inv.journal_id.code, inv.payment_reference)).replace('/', '')+'.pdf'
            else:
                as_name = ('INV'+(inv.name or '')).replace('/','')+'.pdf'
            return as_name

    def _onchange_terms(self):
        invoice_terms =  self.company_id.invoice_terms
        return invoice_terms

    def action_post(self):
        sale_order = self.env['sale.order'].search([('name','=',self.invoice_origin)],limit=1)
        line_sale = False
        if sale_order and self.move_type=='out_refund':
            #recorremos las lineas d ela factura
            for line in self.invoice_line_ids:
                for line_sale in sale_order.order_line:
                    if line.product_id == line_sale.product_id:
                        line_sale = line_sale
                tf_partner_id = self.env['tf.res.partner']
                for x in sale_order.partner_id.tf_vendor_parameter_ids:
                    if x.category_id.id == line_sale.product_id.categ_id.id:
                        tf_partner_id = x
                if not tf_partner_id:
                    continue
                #se realizan los calculos 
                moneda_mxn = self.env['res.currency'].search([('id','=',33)])
                moneda_usd = self.env['res.currency'].search([('id','=',2)])
                price_unit = line.price_unit
                RECALCULATED_PRICE_UNIT = line.move_id.currency_id._convert_nimax(price_unit, moneda_usd, self.env.user.company_id, fields.Date.today(),line_sale.id)
                monto_mxp=line.move_id.currency_id._convert_nimax(price_unit, moneda_mxn, self.env.user.company_id, fields.Date.today(),line_sale.id)
                NIMAX_PRICE_MXP = monto_mxp
                COST_NIMAX_USD = line.move_id.currency_id._convert_nimax(line_sale.COST_NIMAX_USD, moneda_usd, self.env.user.company_id, fields.Date.today(),line_sale.id)
                COST_NIMAX_MXP = line.move_id.currency_id._convert_nimax(line_sale.COST_NIMAX_USD, moneda_mxn, self.env.user.company_id, fields.Date.today(),line_sale.id)
                MARGIN_MXP = (NIMAX_PRICE_MXP*line.quantity)-(COST_NIMAX_MXP*line.quantity)
                MARGIN_USD = (RECALCULATED_PRICE_UNIT*line.quantity)-(COST_NIMAX_USD*line.quantity)
                TOTAL_USD = RECALCULATED_PRICE_UNIT*line.quantity
                TOTAL_MXP = NIMAX_PRICE_MXP * line.quantity
                partner=False
              
                #creamos el registro en el historico de promociones 
                self.env['tf.history.promo'].create(dict(
                    # promotion_id=,
                    vendor_id=tf_partner_id.partner_id.id,
                    product_id=line_sale.product_id.id,
                    customer_id=line_sale.order_id.partner_id.id,
                    customer_type=tf_partner_id.partner_type.id,
                    # as_pricelist_id = self.sh_pricelist_id.id,
                    category_id=line_sale.product_id.categ_id.id,
                    qty=line.quantity,
                    recalculated_price_unit=RECALCULATED_PRICE_UNIT,
                    recalculated_price_unit_mxp=NIMAX_PRICE_MXP,
                    recalculated_cost_nimax_usd=COST_NIMAX_USD,
                    recalculated_cost_nimax_mxp=COST_NIMAX_MXP,
                    margin_mxp=MARGIN_MXP*-1,
                    margin_usd=MARGIN_USD*-1,
                    total_usd=TOTAL_USD*-1,
                    total_mxp=TOTAL_MXP*-1,
                    # last_applied_promo=,
                    salesman_id=line.move_id.user_id.id,

                    sale_id=sale_order.id,
                    sale_order_line=line_sale.id,
                ))

                #se marca la utima action desde factura 
                query_ids = ("""
                SELECT id FROM tf_history_promo tf 
                where
                tf.sale_id = """+str(sale_order.id)+""" and tf.product_id = """+str(line.product_id.id)+""" and sale_order_line= """+str(line_sale.id)+""" 
                order by tf.create_date desc limit 1
                """)
                self.env.cr.execute(query_ids)
                history_table = [j for j in self.env.cr.fetchall()]
                tf_history_id = self.env['tf.history.promo'].search([('id', 'in', history_table)])
                if tf_history_id:
                    tf_history_id.last_applied_promo = True
        res = super(as_accountinvoice, self).action_post()
        return res

    @api.model
    def l10n_mx_edi_retrieve_attachments(self):
        '''Retrieve all the cfdi attachments generated for this invoice.

        :return: An ir.attachment recordset
        '''
        self.ensure_one()
        if not self.l10n_mx_edi_cfdi_name:
            return []
        domain = [
            ('res_id', '=', self.id),
            ('res_model', '=', self._name),
            ('name', '=', self.l10n_mx_edi_cfdi_name)]
        return self.env['ir.attachment'].search(domain)

    def action_invoice_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        cfdi_filename = ('%s-%s-MX-Invoice-3.3.pdf' % (self.journal_id.code, self.payment_reference or self.name)).replace('/', '')
        if cfdi_filename:
            name = str(cfdi_filename).split('.')[0]
            invoices = self.env['ir.attachment'].search([('name', '=', name and _("%s.pdf") % name)])
            if not invoices:
                modelo = 'account.move'
                content = self.env.ref('as_sale_pricelist.as_account_invoices_new_mx')._render_qweb_pdf(self.id)[0]
                self.env['ir.attachment'].create({
                    'name': name and _("%s.pdf") % name or _("Factura_.pdf"),
                    'type': 'binary',
                    'datas': base64.b64encode(content),
                    'res_model': modelo,
                    'res_id': self.id,
                })
              


        template = self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)
        compose_form = self.env.ref('account.account_invoice_send_wizard_form', raise_if_not_found=False)
        ctx = dict(
            default_model='account.move',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            custom_layout="mail.mail_notification_paynow",
            force_email=True
        )
        return {
            'name': _('Send Invoice'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice.send',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def get_promocion(self,line_id):
        vasl=0
        query_movements = ("""
            select order_line_id from sale_order_line_invoice_rel 
            where
            invoice_line_id = """+str(line_id)+"""
            """)
        #_logger.debug(query_movements)
        self.env.cr.execute(query_movements)
        ids = [k for k in self.env.cr.fetchall()]
        name= ''
        if ids != []:
            line = self.env['sale.order.line'].search([('id','in',ids)],limit=1)
            ultima_promo = self.env['tf.history.promo'].search([('sale_id','=',line.order_id.id),('product_id','=',line.product_id.id),('last_applied_promo','=',True)],order="write_date desc", limit=1)
            if ultima_promo:
                name = str(ultima_promo.promo_id.id)+' : '+str(ultima_promo.promo_id.name)
            else:
                name =' '
        return name

    def get_tasa_xml(self,product_id):
        xml = self._l10n_mx_edi_decode_cfdi()
        impuestos = []
        bandera = False
        if xml is not None:
            if 'cfdi_node' in xml:
                conceptos = xml['cfdi_node'].Conceptos.Concepto
                for product in conceptos:
                    if product.get('NoIdentificacion')== product_id:
                        if 'Impuestos' in product:
                            for translado in product.Impuestos.Traslados.Traslado:
                                if bandera == False:
                                    if translado.attrib != {}:
                                        vals={
                                            'Tasa': translado.attrib['TasaOCuota'],
                                            'Base': round(float(translado.attrib['Base']),2),
                                            'Impuesto': translado.attrib['Impuesto'],
                                            'Importe': round(float(translado.attrib['Importe']),2),
                                        }
                                        bandera = True
                                        impuestos.append(vals)

        return impuestos

    def get_product_lot(self,product_id):
        names = ''
        sale_order = self.env['sale.order'].search([('name','=',self.invoice_origin)],limit=1)
        for pick in sale_order.picking_ids:
            for move in pick.move_line_ids_without_package:
                if product_id == move.product_id.id:
                    if move.lot_id.name:
                        names += str(move.lot_id.name)+', '
        return names
        
    def get_referencia_pedido(self):
        sale_order = self.env['sale.order'].search([('name','=',self.invoice_origin)],limit=1)
        if sale_order and 'x_studio_orden_de_compra' in sale_order:
            return sale_order.x_studio_orden_de_compra
        else:
            return 'N/A'

    def action_invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        if any(not move.is_invoice(include_receipts=True) for move in self):
            raise UserError(_("Only invoices could be printed."))

        self.filtered(lambda inv: not inv.is_move_sent).write({'is_move_sent': True})
        if self.user_has_groups('account.group_account_invoice'):
            return self.env.ref('as_sale_pricelist.as_account_invoices_new_mx').report_action(self)
        else:
            return self.env.ref('as_sale_pricelist.as_account_invoices_new_mx').report_action(self)

    def adjuntar_factura_model(self,invoice):
   
        return ''

    def l10n_mx_edi_amount_to_text(self):
        """Method to transform a float amount to text words
        E.g. 100 - ONE HUNDRED
        :returns: Amount transformed to words mexican format for invoices
        :rtype: str
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
        # currency_type = 'M.N' if currency == 'MXN' elif currency_type = 'DOLARES' if currency == 'USD' else 'M.E.'
        # Split integer and decimal part
        amount_i, amount_d = divmod(self.amount_total, 1)
        amount_d = round(amount_d, 2)
        amount_d = int(round(amount_d * 100, 2))
        words = self.currency_id.with_context(lang=self.partner_id.lang or 'es_ES').amount_to_text(amount_i).upper()
        invoice_words = '%(words)s %(amount_d)02d/100 %(curr_t)s' % dict(
            words=words, amount_d=amount_d, curr_t=currency_type)
        return invoice_words