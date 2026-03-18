# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.addons.l10n_mx_edi_extended.models.account_move import CUSTOM_NUMBERS_PATTERN  
class StockQuant(models.Model):
    _inherit="stock.quant"

    sd_description = fields.Text(string="Motivo de ajuste")

    def action_apply_inventory(self):
        res = super(StockQuant, self).action_apply_inventory()
        for quant in self:
            template = self.env.ref('as_sale_pricelist.email_template_ajustment_stock')
            emails = ''
            for user in self.env.ref("as_sale_pricelist.group_send_mail_ajust").user_ids:
                if user.partner_id.email:
                    emails += user.partner_id.email + ','
            if not emails:
                continue
            template.with_context(force_send=True,).send_mail(
                quant.id,
                email_layout_xmlid='mail.mail_notification_light',
                email_values={
                    'email_to': emails,
                    'message_type': 'user_notification',
                },
                force_send=True,
            )
        return res

class StockLot(models.Model):
    _inherit = "stock.lot"

    def _inverse_l10n_mx_edi_landed_cost_id(self):
        #sustituida por necesidad de renombrar los numeros de lote porque odoo concatena con pedimentos causando conflicto.
        for lot in self:
            if not lot.product_id.l10n_mx_edi_can_use_customs_invoicing:
                continue
            split_name = lot.name.rsplit("/", 1)
            # If we already have a customs on the name we take only what is not, else we just take the whole name
            prefix_name = split_name[0].strip() if len(split_name) > 1 and CUSTOM_NUMBERS_PATTERN.match(split_name[1].strip()) else lot.name

            if prefix_name and lot.l10n_mx_edi_customs_number:
                lot.name = f"{prefix_name}"
                lot.ref = f"{lot.l10n_mx_edi_customs_number}"
            else:
                lot.name = prefix_name or lot.l10n_mx_edi_customs_number
                lot.ref = f"{lot.l10n_mx_edi_customs_number}"

    def _get_recompute_name(self):
        for lot in self:
            nombre = lot.name.split(' / ')
            if len(nombre) > 1:
                lot.name = nombre[0]
                lot.ref = f"{lot.l10n_mx_edi_customs_number}"