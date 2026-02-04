# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError
    
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