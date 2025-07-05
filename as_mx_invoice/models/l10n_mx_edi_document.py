# -*- coding: utf-8 -*-
from odoo import models, api, _, fields
import base64
import logging
import json
import traceback
from odoo.tools import html_escape # Importar html_escape
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Ya no necesitamos cryptography aquí si quitamos la validación previa
# try:
#     from cryptography import x509
#     from cryptography.hazmat.backends import default_backend
# except ImportError:
#     _logger.warning("Librería cryptography no encontrada.")
#     x509 = None

class L10nMxEdiDocumentInherit(models.Model):
    _inherit = 'l10n_mx_edi.document'

    def _add_certificate_cfdi_values(self, cfdi_values):
        """
        OVERRIDE: Muestra info del CSD en chatter antes de llamar a super().
        """
        _logger.info("[AS_MX_INVOCE] Entrando a _add_certificate_cfdi_values heredado")
        
        if 'move_id' in self.env.context:
            move_id = self.env.context.get('move_id')
            if isinstance(move_id, int):
                move = self.env['account.move'].browse(move_id)
                if move.exists():
                    msg = """<p>Verificando certificado para CFDI...</p>
                        <pre>
Compañía: %s (ID: %s)
RFC emisor: %s
Buscando certificado activo...
                        </pre>
                    """ % (move.company_id.name, move.company_id.id, 
                          move.company_id.partner_id.vat or "RFC NO CONFIGURADO")
                    move.message_post(body=msg, message_type='comment', subtype_xmlid='mail.mt_note', body_is_html=True)
        
        # Llamada al método original
        return super(L10nMxEdiDocumentInherit, self)._add_certificate_cfdi_values(cfdi_values)

    @api.model
    def _send_api(self, *args, **kwargs):
        """
        OVERRIDE: Agrega más logs detallados y debug para detectar problemas
        y para llamar correctamente al método original.
        """
        # ¡IMPORTANTE! Este método es llamado tanto en instancias como a nivel de modelo
        # Verificamos si somos un recordset vacío o no
        is_empty = not self or not self.ids
        
        # Mostramos información completa de los argumentos para debug
        _logger.info("[_send_api] Llamada a _send_api con los siguientes parámetros:")
        _logger.info(f"[_send_api] Args: {args}")
        _logger.info(f"[_send_api] Kwargs: {kwargs}")
        
        # --- PARSEO DE ARGUMENTOS POSICIONALES (VERSIÓN 2) ---
        # Este es un problema en el flujo de timbrado: Odoo llama a _send_api con args, no kwargs
        # Analizar patrón de llamada a _send_api desde account_move.py
        record = None
        on_populate_function = None
        
        # Intentar extraer record del kwarg primero
        if 'record' in kwargs:
            record = kwargs.get('record')
        # Si no hay kwarg 'record', intentar extraer de los args según el patrón típico
        elif args and len(args) >= 1:
            # Primera posición puede ser record
            first_arg = args[0]
            # Caso 1: Primer argumento es res.company (como vemos en los logs)
            if hasattr(first_arg, '_name') and first_arg._name == 'res.company':
                _logger.info("[_send_api] Primer argumento es una compañía, buscando factura...")
                # Buscar factura con context o buscar por nombre del XML
                if len(args) >= 3 and isinstance(args[2], str) and args[2].endswith('.xml'):
                    xml_filename = args[2]
                    _logger.info(f"[_send_api] Intentando extraer número de factura del nombre de XML: {xml_filename}")
                    # El nombre del XML es algo como 'ESCUE-ESCUE202500002-MX-Invoice-4.0.xml'
                    # Intentar extraer número de factura
                    parts = xml_filename.split('-')
                    if len(parts) >= 2:
                        invoice_ref = parts[1]
                        _logger.info(f"[_send_api] Buscando factura con referencia: {invoice_ref}")
                        invoice = self.env['account.move'].search([('name', 'like', invoice_ref)], limit=1)
                        if invoice:
                            _logger.info(f"[_send_api] ¡Factura encontrada! {invoice.name}")
                            record = invoice
                            kwargs['record'] = invoice
                if not record and self.env.context.get('active_model') == 'account.move':
                    active_id = self.env.context.get('active_id')
                    if active_id:
                        invoice = self.env['account.move'].browse(active_id)
                        if invoice.exists():
                            _logger.info(f"[_send_api] Factura encontrada en context: {invoice.name}")
                            record = invoice
                            kwargs['record'] = invoice
            # Caso 2: Primer argumento es account.move
            elif hasattr(first_arg, '_name') and first_arg._name == 'account.move':
                record = first_arg
                kwargs['record'] = record
                _logger.info(f"[_send_api] Record extraído directamente de args[0]: {record.name}")
                
        # Si siguen existiendo funciones al final, a veces on_populate es 4° o 5° argumento
        if args and len(args) >= 4:
            for i in range(len(args)-3, len(args)):
                if i >= 0 and callable(args[i]):
                    on_populate_function = args[i]
                    break
        
        if on_populate_function:
            _logger.info("[_send_api] Se encontró una función on_populate, preservándola")
        
        # --- FIN PARSEO DE ARGUMENTOS ---
        
        if is_empty:
            _logger.warning("[_send_api] _send_api llamado en un recordset vacío de l10n_mx_edi.document")
            # Intentamos crear un documento EDI primero si tenemos la factura
            if record and hasattr(record, 'company_id') and getattr(record, '_name', '') == 'account.move':
                _logger.info(f"[_send_api] Intentando crear documento EDI para factura {record.name}")
                # Esto es un hack: necesitamos un documento para continuar
                edi_doc = self.create({
                    'move_id': record.id,
                    'state': 'invoice_sent_failed',  # Usamos un estado válido en lugar de document_type
                    'datetime': fields.Datetime.now(),  # Aseguramos que el campo requerido tenga valor
                })
                _logger.info(f"[_send_api] Documento EDI creado ID: {edi_doc.id}")
                # Ahora usamos el nuevo documento
                kwargs['record'] = record  # Asegurarse que record está en kwargs
                return edi_doc._send_api(*args, **kwargs)
        else:
            # Si no somos un recordset vacío, pero tampoco singleton
            if len(self) > 1:
                _logger.warning(f"[_send_api] _send_api llamado en múltiples documentos a la vez: {self.ids}. Usando solo el primero.")
                return self[0]._send_api(*args, **kwargs)
            
            # Si llegamos aquí es porque somos singleton
            self.ensure_one()
        
        # Revisamos si hay argumentos inválidos
        if len(args) > 0 and isinstance(args[0], str):
            _logger.warning(f"[_send_api] _send_api recibió un primer argumento inválido (tipo: {type(args[0])}, valor: {args[0]}). Intentando corregir.")
            # Creamos una nueva lista de args sin el primer argumento
            args = args[1:] if len(args) > 1 else ()
        
        for key, value in list(kwargs.items()):
            if key == 'extra_context' and isinstance(value, str):
                _logger.warning(f"[_send_api] _send_api recibió un extra_context inválido (tipo: {type(value)}, valor: {value}). Ignorándolo.")
                del kwargs['extra_context']
            elif key == 'record' and (not value or not hasattr(value, 'company_id')):
                _logger.error(f"[_send_api] El objeto 'record' pasado a _send_api no es una factura válida o no tiene company_id.")
                if not value:
                    # Si value es None o False, intentamos usar self.move_id
                    if not is_empty and self.move_id:
                        kwargs['record'] = self.move_id
                        _logger.info(f"[_send_api] Intentando usar self.move_id: {self.move_id.name}")
                elif not hasattr(value, 'id'):
                    # Si value no tiene ID, es posible que sea un string o entero
                    try:
                        move_id = int(value) if isinstance(value, str) else value
                        move = self.env['account.move'].browse(move_id)
                        if move.exists():
                            kwargs['record'] = move
                            _logger.info(f"[_send_api] Se corrigió record usando ID {move_id}: {move.name}")
                        else:
                            _logger.error(f"[_send_api] No se encontró factura con ID {move_id}")
                    except (ValueError, TypeError):
                        _logger.error(f"[_send_api] No se pudo convertir {value} a ID de factura")
        
        # Verificamos si tenemos los datos necesarios
        record = kwargs.get('record')
        if not record or not hasattr(record, 'company_id'):
            _logger.error(f"[_send_api] No se pudo obtener una factura válida, abortando _send_api")
            
            # Intento de último recurso: buscar en el contexto
            if self.env.context.get('active_model') == 'account.move':
                active_id = self.env.context.get('active_id')
                if active_id:
                    invoice = self.env['account.move'].browse(active_id)
                    if invoice.exists():
                        _logger.info(f"[_send_api] Factura encontrada en contexto: {invoice.name}")
                        record = invoice
                        kwargs['record'] = invoice
            
            if not record:
                result = {'error': _('Datos de factura inválidos o faltantes para envío a PAC. Revise el log.')}
                return result

        # Verificamos que la compañía tenga configuración de PAC
        company = record.company_id
        if not company:
            _logger.error(f"[_send_api] La factura no tiene compañía asociada")
            result = {'error': _('La factura no tiene compañía asociada. Imposible enviar a PAC.')}
            return result
            
        pac_name = getattr(company, 'l10n_mx_edi_pac', False)
        if not pac_name:
            _logger.error(f"[_send_api] La compañía {company.name} no tiene PAC configurado")
            result = {'error': _('La compañía no tiene proveedor PAC configurado.')}
            return result
            
        # Verificar credenciales
        pac_username = getattr(company, 'l10n_mx_edi_pac_username', False)
        pac_password = getattr(company, 'l10n_mx_edi_pac_password', False)
        if not pac_username or not pac_password:
            _logger.error(f"[_send_api] Credenciales PAC faltantes para {company.name}")
            result = {'error': _('La compañía no tiene credenciales PAC configuradas.')}
            return result
        
        # Antes de llamar a super, registramos que vamos a hacerlo
        _logger.info(f"[_send_api] Llamando a super()._send_api con args={args} y kwargs={kwargs.keys()}")
        
        # PUNTO CLAVE: Guardar el registro antes de limpiarlo de kwargs
        invoice_record = kwargs.pop('record', None)
        _logger.info(f"[_send_api] Removido parámetro 'record' de kwargs antes de llamar a super()")
        
        # Ahora sí, llamamos al método original con los argumentos corregidos
        try:
            # Si estamos en un recordset vacío, usamos la versión como método de modelo
            if is_empty:
                result = super(L10nMxEdiDocumentInherit, self)._send_api(*args, **kwargs)
            else:
                # Si no, usamos la versión como método de instancia
                result = super()._send_api(*args, **kwargs)
                
            _logger.info(f"[_send_api] Resultado de _send_api: {result}")
            return result
        except Exception as e:
            error_msg = f"Excepción no controlada en _send_api: {e}\n{traceback.format_exc()}"
            _logger.error(f"[_send_api] {error_msg}")
            return {'error': error_msg}

    @api.model
    def _add_date_cfdi_values(self, cfdi_values, document_date, journal=None, document_post_time=None):
        """
        OVERRIDE: Asegura que document_date sea un objeto datetime válido.
        Este método es invocado para formatear la fecha del documento CFDI.
        Ahora acepta el parámetro document_post_time para compatibilidad con Odoo 18.
        """
        _logger.info("[AS_MX_DOC] _add_date_cfdi_values llamado con document_date: " + str(document_date))
        _logger.info("[AS_MX_DOC] _add_date_cfdi_values recibió document_post_time: " + str(document_post_time))
        
        # Verificar si document_date es válido
        if not document_date or not hasattr(document_date, 'strftime'):
            _logger.warning("[AS_MX_DOC] document_date es inválido (False/None o no tiene strftime), usando now()")
            document_date = fields.Datetime.now()
            
        # Continuar con la función original, pasando el nuevo parámetro
        return super(L10nMxEdiDocumentInherit, self)._add_date_cfdi_values(cfdi_values, document_date, journal, document_post_time)
 