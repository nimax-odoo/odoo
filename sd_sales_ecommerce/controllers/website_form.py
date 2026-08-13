# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json

from odoo import _
from odoo.http import request
from odoo.addons.website.controllers.form import WebsiteForm


class WebsiteNewsletterForm(WebsiteForm):

    def _handle_website_form(self, model_name, **kwargs):
        if model_name == 'res.access.portal':
            vat = kwargs.get('vat')
            email = kwargs.get('email')
            description = kwargs.get('description')
            # return json.dumps({'error': _('Prueba : %s',vat)})
            # 1. Validación: VAT obligatorio
            if not vat:
                return json.dumps({'error': _('Debe ingresar un número de documento válido.')})
            # 2. Buscar partner
            partner = request.env['res.partner'].sudo().search([('vat', '=', vat)], limit=1)
            if not partner:
                return json.dumps({'error': _('No se encontró un cliente con ese documento, contacte al administrador')})
            # 3. Validar email
            if not partner.email:
                return json.dumps({'error': _('El cliente no tiene un correo registrado.')})
            # 4. Validar si ya existe usuario
            existing_user = request.env['res.users'].sudo().search([
                ('login', '=', partner.email)
            ], limit=1)
            if existing_user:
                return json.dumps({'error': _('El usuario del cliente ya se encuentra registrado.')})
            # 5. Obtener compañías
            company_ids = request.env['res.company'].sudo().search([])
            # 6. Crear usuario portal
            portal_user = request.env['res.users'].sudo().create({
                'company_id': request.env.company.id,
                'company_ids': [(6, 0, company_ids.ids)],
                'email': email,
                'login': email,
                'name': partner.name,
                'partner_id': partner.id,
                'group_ids': [(4, request.env.ref('base.group_portal').sudo().id)],
            })
            portal_user_id = request.env['res.access.portal'].sudo().create({
                'name': 'Registro del usuario '+portal_user.login,
                'vat': vat,
                'email': email,
                'notas': description,
                'partner_id': partner.id,                
            })
            # postear en el cchatter que el contacto se ha registrado en el portal
            partner.message_post(body="El contacto se ha registrado en el portal.")
            partner.message_post(body=str(description))
            #notificar por correo a los usuarios del grupo group_auto_access_portal que un nuevo que usuario se ha registrado en el portal
            template = request.env.ref('sd_sales_ecommerce.email_template_access_portal')
            emails = ''
            if request.env.ref("sd_sales_ecommerce.group_auto_access_portal").sudo().user_ids:
                for user in request.env.ref("sd_sales_ecommerce.group_auto_access_portal").sudo().user_ids:
                    if user.partner_id.email:
                        emails += user.partner_id.email + ','
                template.sudo().with_context(force_send=True,).send_mail(
                    partner.id,
                    email_layout_xmlid='mail.mail_notification_light',
                    email_values={
                        'email_to': emails,
                        'message_type': 'user_notification',
                    },
                    force_send=True,
                )

            return json.dumps({'id': vat})
            
        return super()._handle_website_form(model_name, **kwargs)