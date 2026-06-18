# -*- coding: utf-8 -*-
import logging
import uuid
from odoo import api, fields, models, _
import requests
import json
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    def send_invoice_cyberpuerta(self):
        users = self.env['res.users'].sudo().search([('sd_cy_webhook_active','=',True)])

        if not users:
            msg = "No hay usuarios con integración Cyberpuerta activa."

        results = []

        for user in users:
            if not user.sd_cy_token:
                msg = f"El usuario '{user.name}' no tiene token configurado."

            if not user.sd_cy_url:
                msg = f"El usuario '{user.name}' no tiene URL configurada."

            url = f"{user.sd_cy_url}/api/provider/order/cfdi"

            headers = {
                "Authorization": f"Bearer {user.sd_cy_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            payload = [{
                "order_number": self.invoice_origin or "",
                "invoice_uuid": self.l10n_mx_edi_cfdi_uuid or ""
            }]

            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,  # mejor que data=json.dumps
                    timeout=120
                )
                if response.status_code == 200:
                    msg = f"Enviado satisfactoriamente: {response.text}"

                # 🔍 Validación HTTP
                if response.status_code != 200:
                    msg = (
                        f"Error HTTP {response.status_code} al enviar factura a Cyberpuerta.\n"
                        f"Usuario: {user.name}\n"
                        f"URL: {url}\n"
                    )
                    _logger.error(f"[Cyberpuerta] {response.status_code}")

            except requests.exceptions.Timeout:
                msg = f"Timeout al conectar con Cyberpuerta (usuario: {user.name})"
                _logger.error(f"[Cyberpuerta] {msg}")

            except requests.exceptions.ConnectionError:
                msg = f"No se pudo conectar a Cyberpuerta (usuario: {user.name})"
                _logger.error(f"[Cyberpuerta] {msg}")

            except Exception as e:
                msg = f"Error inesperado enviando factura (usuario: {user.name}): {str(e)}"
                _logger.error(f"[Cyberpuerta] {msg}")
        self.message_post(body=str(msg))