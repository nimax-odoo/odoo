# -*- coding: utf-8 -*-
import logging
import uuid
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    sd_waybills = fields.Char('Seguimiento Guia Remisión')
    sd_carrier_id = fields.Many2one('delivery.carrier',string='Seguimiento Guia Remisión')

    def get_extra_print_items(self):
        """ Helper to dynamically add items in the 'Print' menu of list and form of sale.order.
        """
        if moves_to_export := self.filtered(lambda m: m._get_move_zip_export_docs()):
            return [
                {
                    'key': 'download_all',
                    'description': _("Export ZIP"),
                    **moves_to_export.action_move_download_all(),
                },
            ]
        return []

    def _get_move_zip_export_docs(self):
        self.ensure_one()
        attachment = self.message_main_attachment_id
        return [{
            'filename': attachment.name,
            'filetype': attachment.mimetype,
            'content': attachment.raw,
        }] if attachment else []

    def action_move_download_all(self):
        return {
            'type': 'ir.actions.act_url',
            'url': f'/account/download_move_attachments/{",".join(str(move_id) for move_id in self.ids)}',
            'target': 'download',
        }