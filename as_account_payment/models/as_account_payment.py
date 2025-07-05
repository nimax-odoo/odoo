from odoo import api, models, fields, _
import base64
import xml.etree.ElementTree as ET
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    """
    Extends account.payment to handle EDI XML documents and exchange rates
    for Mexican CFDI 4.0 payments
    """
    _inherit = 'account.payment'

    xml_exchange_rate = fields.Float(
        string='XML Exchange Rate',
        compute='_compute_xml_exchange_rate',
        help='Exchange rate from EDI XML (TipoCambioP)',
        digits=(16, 6)
    )
    
    inverse_company_rate = fields.Float(
        string='Inverse Company Rate',
        compute='_compute_inverse_company_rate',
        store=True,
        digits=(16, 6),
        help='The inverse rate of the currency relative to the company currency'
    )

    xml_file = fields.Binary(
        string='XML File',
        help='Upload new XML file to replace existing EDI document'
    )
    xml_filename = fields.Char(
        string='XML Filename',
        help='Name of the uploaded XML file'
    )

    as_edi_doc = fields.Char(
        string='Documento EDI',
        compute='_compute_as_edi_doc',
        store=True,
        help='Name of attached EDI document'
    )

    def action_update_edi_documents(self):
        self.ensure_one()
        self.move_id._update_payments_edi_documents()
        
    @api.depends('currency_id', 'date')
    def _compute_inverse_company_rate(self):
        """
        Computes inverse exchange rate relative to company currency
        Updated for Odoo 18's new currency API
        """
        for payment in self:
            payment.inverse_company_rate = payment.currency_id._get_conversion_rate(
                from_currency=payment.company_id.currency_id,
                to_currency=payment.currency_id,
                company=payment.company_id,
                date=payment.date or fields.Date.today()
            )
            
    @api.depends('edi_document_ids.attachment_id')
    def _compute_xml_exchange_rate(self):
        """
        Extracts exchange rate from EDI XML document
        Updated for CFDI 4.0 namespace handling
        """
        for payment in self:
            rate = 1.0
            if payment.edi_document_ids and payment.edi_document_ids[0].attachment_id:
                try:
                    xml_content = base64.b64decode(payment.edi_document_ids[0].attachment_id.datas).decode()
                    root = ET.fromstring(xml_content)
                    namespaces = {
                        'cfdi': 'http://www.sat.gob.mx/cfd/4',
                        'pago20': 'http://www.sat.gob.mx/Pagos20'
                    }
                    docto = root.find('.//pago20:DoctoRelacionado', namespaces)
                    if docto is not None:
                        rate = float(docto.get('TipoCambioP', '1.0'))
                except Exception as e:
                    _logger.error(f"[_compute_xml_exchange_rate] Error: {str(e)}")
                    rate = 1.0
            payment.xml_exchange_rate = rate
                
    def action_fix_edi_xml_equivalencia(self):
        """
        Fixes EquivalenciaDR value in EDI XML documents
        Updated for Odoo 18's new attachment handling
        """
        self.ensure_one()
        _logger.info(f"[action_fix_edi_xml_equivalencia] Starting fix for payment {self.id}")
        
        for edi_doc in self.edi_document_ids:
            if not edi_doc.attachment_id or not edi_doc.attachment_id.datas:
                continue
                
            try:
                # XML processing logic remains the same
                xml_content = base64.b64decode(edi_doc.attachment_id.datas).decode()
                root = ET.fromstring(xml_content)
                
                namespaces = {
                    'cfdi': 'http://www.sat.gob.mx/cfd/4',
                    'pago20': 'http://www.sat.gob.mx/Pagos20'
                }
                
                for docto in root.findall('.//pago20:DoctoRelacionado', namespaces):
                    equivalencia = 1.0 / (self.manual_currency_rate if self.manual_currency_rate_active 
                                        else self.xml_exchange_rate or 1.0)
                    docto.set('EquivalenciaDR', '{:.6f}'.format(equivalencia))
                
                # Updated attachment creation for Odoo 18
                new_xml = ET.tostring(root, encoding='UTF-8', xml_declaration=True)
                new_datas = base64.b64encode(new_xml)
                
                # Create attachment using new API
                attachment = self.env['ir.attachment'].create({
                    'name': f'Corregido_EDI_XML_{edi_doc.name}',
                    'raw': new_xml,  # New in Odoo 18
                    'res_model': self._name,
                    'res_id': self.id,
                })
                
                # Update EDI document
                edi_doc.attachment_id.write({'raw': new_xml})
                
                # Post message with updated messaging API
                self.message_post(
                    body=_("EDI XML document corrected: %s (Exchange Rate: %s)") % (
                        edi_doc.name, self.xml_exchange_rate
                    ),
                    attachment_ids=[attachment.id],
                    subtype_xmlid='mail.mt_note',
                    message_type='notification'
                )
                
            except Exception as e:
                _logger.error(f"[action_fix_edi_xml_equivalencia] Error: {str(e)}")
                raise UserError(_(f"Error fixing XML: {str(e)}"))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _("EDI XML documents have been corrected."),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_upload_replace_xml(self):
        """Subir y reemplazar el documento XML EDI."""
        self.ensure_one()
        
        if not self.xml_file:
            raise UserError(_("Por favor, cargue un archivo XML primero."))

        if not self.edi_document_ids:
            raise UserError(_("No se encontró ningún documento EDI para reemplazar."))

        try:
            # Decodificar el archivo XML cargado
            xml_content = base64.b64decode(self.xml_file)
            
            # Validar que sea un XML válido
            try:
                ET.fromstring(xml_content)
            except ET.ParseError:
                raise UserError(_("El archivo proporcionado no es un documento XML válido."))

            # Crear nuevo adjunto usando la API de Odoo 18
            new_attachment = self.env['ir.attachment'].create({
                'name': self.xml_filename or 'reemplazo.xml',
                'raw': xml_content,  # Usando 'raw' en lugar de 'datas'
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/xml'
            })

            # Actualizar el documento EDI con el nuevo adjunto
            for edi_doc in self.edi_document_ids:
                if edi_doc.edi_format_id.code == 'cfdi_3_3':
                    edi_doc.write({
                        'attachment_id': new_attachment.id,
                        'state': 'sent',
                    })

            # Publicar mensaje en el historial
            self.message_post(
                body=_("El documento XML EDI ha sido reemplazado con: %s") % (self.xml_filename or 'reemplazo.xml'),
                attachment_ids=[new_attachment.id]
            )

            # Limpiar el campo de carga
            self.write({
                'xml_file': False,
                'xml_filename': False,
            })

            # Retornar acción para recargar la página y mostrar notificación
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',  # Esto recargará la página completa
                'params': {
                    'message': _("El documento XML ha sido reemplazado exitosamente."),
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            raise UserError(_("Error al reemplazar XML: %s") % str(e))

    @api.depends('edi_document_ids', 'edi_document_ids.attachment_id.name')
    def _compute_as_edi_doc(self):
        """
        Calcula si el pago tiene documentos EDI asociados.
        """
        for payment in self:
            # El atributo correcto en Odoo 18 es 'edi_document_ids'
            # Verificamos si existe el atributo antes de usarlo
            if hasattr(payment, 'edi_document_ids'):
                attachment_names = payment.edi_document_ids.mapped('attachment_id.name')
            else:
                # Alternativa: buscar en los documentos EDI relacionados con el pago
                attachment_names = self.env['account.edi.document'].search([
                    ('move_id', '=', payment.move_id.id)
                ]).mapped('attachment_id.name')
            
            payment.as_edi_doc = any('xml' in name for name in attachment_names) if attachment_names else False

