# -*- coding: utf-8 -*-

from odoo import models, fields, api


class tfResPartner(models.Model):
    _name = "tf.res.partner"
    inherit = ['mail.thread'] 

    name = fields.Char(track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', track_visibility='onchange')
    partner_type = fields.Many2one('as.partner.type', 'Partner Type', track_visibility='onchange')
    category_id = fields.Many2one('product.category', 'Product Category', track_visibility='onchange')
    purchase_discount = fields.Float('Purchase Discount', track_visibility='onchange')
    partner_discount = fields.Float('Partner Discount', track_visibility='onchange')
    cost_deal_import = fields.Float('% Cost Of Import', track_visibility='onchange')
    fulfillment_rebate = fields.Float('Fullfillment Rebate', track_visibility='onchange')
    

    @api.model
    def create(self, vals):
        record = super(tfResPartner, self).create(vals)
        if record.partner_id:
            record.partner_id.message_post(body=f'Se creó un nuevo registro de: {record.name}')
        return record

    def write(self, vals):
        for record in self:
            original_values = record.read(vals.keys())[0]
            changes = []
            for field, new_value in vals.items():
                old_value = original_values[field]
               
                if field == 'partner_id' and isinstance(old_value, tuple):
                    new_value = self.env['res.partner'].browse(new_value).name if old_value else False
                    old_value = old_value[1]
                    
                elif field == 'partner_type' and isinstance(old_value, tuple):
                    new_value = self.env['as.partner.type'].browse(new_value).name if new_value else False
                    old_value = old_value[1]

                elif field == 'category_id' and isinstance(old_value, tuple):
                    new_value = self.env['product.category'].browse(new_value).name if old_value else False
                    old_value = old_value[1]

                
                changes.append(f'{field}: {old_value}  ->  {new_value}')
            
            result = super(tfResPartner, self).write(vals)
            
            if record.partner_id:
                message_body = f'Actualizó el registro: {record.name}, \n' + '\n'.join(changes)
                record.partner_id.message_post(body=message_body)
        return result
