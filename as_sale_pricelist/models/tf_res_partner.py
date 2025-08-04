# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import base64
import openpyxl
from io import BytesIO

class TfResPartner(models.Model):
    _name = 'tf.res.partner'
    _description = 'Partner Program'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, tracking=True)
    partner_type = fields.Many2one('as.partner.type', string='Partner Type', required=True, tracking=True)
    category_id = fields.Many2one('product.category', string='Product Category', tracking=True)
    partner_discount = fields.Float(string='Partner Discount (%)', tracking=True)
    purchase_discount = fields.Float(string='Purchase Discount (%)', tracking=True)
    fulfillment_rebate = fields.Float(string='Fulfillment Rebate (%)', tracking=True)
    cost_deal_import = fields.Float(string='Cost Deal Import (%)', tracking=True)
    partner_ids = fields.Many2many('res.partner', string='Clientes')
    attachment = fields.Binary(string="Subir", attachment=True)
    attachment_name = fields.Char(string="Nombre del archivo",
                                  help="Attachment file name")
    orders_count = fields.Integer('Contactos', compute='_get_contact')
  
    
    def _get_contact(self):
        self.orders_count = len(self.partner_ids)    

    def action_download_sample(self):
        """ For downloading a sample excel file """
        return {
            'type': 'ir.actions.act_url',
            'url': '/download/excel2',
            'target': 'self',
            'file_name': 'Plantilla.xlsx'
        }

   
    def action_open_orders(self):
        self.ensure_one()
        consultas = self.partner_ids
        action = {
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'name': _("Contactos"),
        }
        action.update({
            'view_mode': 'list,form',
            'domain': [('id','in',consultas.ids)]
        })
        return action   
            
    @api.depends('partner_id', 'partner_type')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.partner_id.name or ''} - {record.partner_type.name or ''}" 

            

    def process_file_contact(self):

        if self.attachment:
            wb = openpyxl.load_workbook(
                filename=BytesIO(base64.b64decode(self.attachment)),
                read_only=True) if self.attachment else ""
            ws = wb.active
            vals_list = []
            for record in ws.iter_rows(min_row=2, values_only=True):
                contact= self.env['res.partner'].sudo().search([('id','=',record[0])])
                if not contact:
                    raise UserError(_('El Cliente "%s" no existe en el sistema.') % record[1])
                vals_list.append((4, contact.id))
            self.write({
                'partner_ids': vals_list
            }) 
