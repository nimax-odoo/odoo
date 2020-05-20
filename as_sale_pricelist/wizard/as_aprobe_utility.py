# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import date, time
from odoo.tools.safe_eval import safe_eval
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError

#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class asSaleOrderPromoWizard(models.Model):
    _name = 'as.aprobe.sale'
    _description = 'Aprobe sale Wizard'

    as_password = fields.Char(string='Contraseña para aprobar Ventas')
    as_sale = fields.Many2one('sale.order', 'Sale Order')

    def as_aprobe_sale(self):
        password_config = self.env['ir.config_parameter'].sudo().get_param('as_sale_pricelist.as_password_ventas1')
        if self.as_sale.as_aprobe == False:
            if self.as_password == password_config:
                self.as_sale.update({'as_aprobe':True})
                self.as_sale.action_confirm()
            else:
                raise ValidationError('Contraseña incorrecta, no se puede aprobar la venta')

