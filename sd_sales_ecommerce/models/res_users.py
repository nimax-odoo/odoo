# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, time
from odoo.tools.safe_eval import safe_eval
from datetime import date, datetime, time
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, is_html_empty
from odoo.tools.translate import html_translate
from odoo.http import request
from odoo.tools import format_amount
#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class AsResUsers(models.Model):
    _inherit = 'res.users'

    sd_desc_percentaje = fields.Float(
        string='Porcentaje de Stock a Mostrar',
        default=1.0, related='partner_id.sd_desc_percentaje',  readonly=False,
        help='Porcentaje del stock real que se mostrará en la E-commerce. Si es 0.8, se mostrará el 80% del stock real. Si está vacío o es 1, se mostrará el 100%.'
    )
    
    sd_pricelist = fields.Many2one(
        'product.pricelist',
        string='Lista de Precios E-commerce', related='partner_id.sd_pricelist',readonly=False,
        help='Lista de precios que se utilizará por defecto en la E-commerce de Stock con precios. Si se deja vacío, se usará la lista de precios del cliente.'
    )
    sd_pricelist_ids = fields.Many2many(
        'product.pricelist','partner_id',
        string='Listas de Precios E-commerce',related='partner_id.sd_pricelist_ids',readonly=False,
        help='Lista de precios que se utilizará por defecto en la E-commerce de Stock con precios. Si se deja vacío, se usará la lista de precios del cliente.'
    )
    sd_reserva_stock = fields.Boolean(
        string='Reservar automaticamente stock E-commerce', related='partner_id.sd_reserva_stock',readonly=False,
        help='Permite reservar el stock de forma automatica en el e-commerce.'
    )

class AsResPartner(models.Model):
    _inherit = 'res.partner'

    sd_desc_percentaje = fields.Float(
        string='Porcentaje de Stock a Mostrar',
        default=1.0,
        help='Porcentaje del stock real que se mostrará en la E-commerce. Si es 0.8, se mostrará el 80% del stock real. Si está vacío o es 1, se mostrará el 100%.'
    )
    
    sd_pricelist = fields.Many2one(
        'product.pricelist',
        string='Lista de Precios E-commerce Predeterminada',
        help='Lista de precios que se utilizará por defecto en la E-commerce de Stock con precios. Si se deja vacío, se usará la lista de precios del cliente.'
    )

    sd_pricelist_ids = fields.Many2many(
        'product.pricelist',
        string='Listas de Precios E-commerce',
        help='Lista de precios que se utilizará por defecto en la E-commerce de Stock con precios. Si se deja vacío, se usará la lista de precios del cliente.'
    )
    sd_reserva_stock = fields.Boolean(
        string='No permitir reservar automaticamente stock E-commerce',
        help='No permite reservar stock de forma automatica en el e-commerce.',default=False
    )

class PortalWizardUser(models.TransientModel):
    _inherit = 'portal.wizard.user'
    
    def action_grant_access(self):
        self.ensure_one()
        self._assert_user_email_uniqueness()

        if self.is_portal or self.is_internal:
            raise UserError(_('The partner "%s" already has the portal access.', self.partner_id.name))

        group_portal = self.env.ref('base.group_portal')
        group_public = self.env.ref('base.group_public')

        self._update_partner_email()
        user_sudo = self.user_id.sudo()

        if not user_sudo:
            # create a user if necessary and make sure it is in the portal group
            company = self.partner_id.company_id or self.env.company
            user_sudo = self.sudo().with_company(company.id)._create_user()

        if not user_sudo.active or not self.is_portal:
            companies = self.env['res.company'].sudo().search([])
            user_sudo.write({'company_ids':companies.ids,'active': True, 'groups_id': [(4, group_portal.id), (3, group_public.id)]})
            # prepare for the signup process
            user_sudo.partner_id.signup_prepare()

        self.with_context(active_test=True)._send_email()
        if user_sudo:
            companies = self.env['res.company'].sudo().search([])
            user_sudo.company_ids = companies.ids
        return self.action_refresh_modal()