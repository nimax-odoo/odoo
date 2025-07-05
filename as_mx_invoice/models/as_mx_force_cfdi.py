# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
import traceback
import time
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class AsMxEdiDocument(models.Model):
    """
    Propósito: Hereda l10n_mx_edi.document para añadir debugging completo al Force CFDI
    """
    _inherit = 'l10n_mx_edi.document'

    def _as_force_cfdi_log(self, message, level='info'):
        """
        Propósito: Registra logs específicos para Force CFDI con ID único
        Parámetros: message (mensaje), level (nivel de log)
        Retorno: None
        """
        trace_id = f"FORCE-CFDI-{self.id}-{int(time.time())}"
        formatted_message = f"[{trace_id}] {message}"
        
        if level == 'error':
            _logger.error(f"[AS_FORCE_CFDI] {formatted_message}")
        elif level == 'warning':
            _logger.warning(f"[AS_FORCE_CFDI] {formatted_message}")
        else:
            _logger.info(f"[AS_FORCE_CFDI] {formatted_message}")

    def _as_post_chatter_force_cfdi(self, message, message_type='info'):
        """
        Propósito: Publica mensaje en el chatter del documento relacionado
        Parámetros: message (mensaje), message_type (tipo de mensaje)
        Retorno: None
        """
        try:
            if self.move_id:
                icon = '🔥' if message_type == 'success' else '⚠️' if message_type == 'warning' else '❌' if message_type == 'error' else 'ℹ️'
                body = f"<p><strong>{icon} FORCE CFDI:</strong> {message}</p>"
                
                self.move_id.message_post(
                    body=body,
                    subject="Force CFDI - Debug Info",
                    message_type='comment',
                    subtype_xmlid='mail.mt_note',
                    body_is_html=True
                )
        except Exception as e:
            _logger.error(f"[AS_FORCE_CFDI] Error posting to chatter: {e}")

    def action_force_payment_cfdi(self):
        """
        Propósito: Hereda y extiende la función Force CFDI con logging completo
        Retorno: Resultado de la función original
        """
        self.ensure_one()
        
        # Información inicial
        start_time = time.time()
        self._as_force_cfdi_log(f"=== INICIANDO FORCE CFDI ===")
        self._as_force_cfdi_log(f"Document ID: {self.id}")
        self._as_force_cfdi_log(f"Document State: {self.state}")
        self._as_force_cfdi_log(f"Move ID: {self.move_id.id if self.move_id else 'None'}")
        self._as_force_cfdi_log(f"Move Name: {self.move_id.name if self.move_id else 'None'}")
        self._as_force_cfdi_log(f"SAT State: {self.sat_state}")
        
        self._as_post_chatter_force_cfdi(f"Iniciando proceso Force CFDI para documento {self.id}", 'info')
        
        # Validaciones previas
        if self.state != 'payment_sent_pue':
            error_msg = f"Estado incorrecto para Force CFDI. Estado actual: {self.state}, requerido: payment_sent_pue"
            self._as_force_cfdi_log(error_msg, 'error')
            self._as_post_chatter_force_cfdi(error_msg, 'error')
            raise ValueError(error_msg)
        
        if not self.move_id:
            error_msg = "No hay move_id asociado al documento"
            self._as_force_cfdi_log(error_msg, 'error')
            self._as_post_chatter_force_cfdi(error_msg, 'error')
            raise ValueError(error_msg)
        
        # Información del payment antes del proceso
        self._as_force_cfdi_log(f"Payment Currency: {self.move_id.currency_id.name if self.move_id.currency_id else 'None'}")
        self._as_force_cfdi_log(f"Payment Amount: {self.move_id.amount if hasattr(self.move_id, 'amount') else 'N/A'}")
        self._as_force_cfdi_log(f"Payment State: {self.move_id.state}")
        self._as_force_cfdi_log(f"Company: {self.move_id.company_id.name}")
        self._as_force_cfdi_log(f"Journal: {self.move_id.journal_id.name}")
        
        try:
            # Verificar configuración PAC antes del envío
            pac_info = self.move_id.company_id.l10n_mx_edi_pac
            pac_test = self.move_id.company_id.l10n_mx_edi_pac_test_env
            self._as_force_cfdi_log(f"PAC Configurado: {pac_info}")
            self._as_force_cfdi_log(f"PAC Test Environment: {pac_test}")
            
            if not pac_info:
                warning_msg = "ADVERTENCIA: No hay PAC configurado"
                self._as_force_cfdi_log(warning_msg, 'warning')
                self._as_post_chatter_force_cfdi(warning_msg, 'warning')
            
            # Verificar certificados
            certificate = self.move_id.company_id.l10n_mx_edi_certificate_ids.filtered('is_valid')
            if certificate:
                self._as_force_cfdi_log(f"Certificado válido encontrado: {certificate[0].serial_number}")
            else:
                warning_msg = "ADVERTENCIA: No se encontró certificado válido"
                self._as_force_cfdi_log(warning_msg, 'warning')
                self._as_post_chatter_force_cfdi(warning_msg, 'warning')
            
            # Llamar al método original
            self._as_force_cfdi_log("Llamando al método original action_force_payment_cfdi...")
            self._as_post_chatter_force_cfdi("Ejecutando Force CFDI...", 'info')
            
            result = super().action_force_payment_cfdi()
            
            # Log después de la ejecución
            execution_time = time.time() - start_time
            self._as_force_cfdi_log(f"Método original ejecutado en {execution_time:.2f} segundos")
            
            # Verificar el estado después
            self._as_force_cfdi_log(f"Estado después del Force CFDI: {self.state}")
            self._as_force_cfdi_log(f"SAT State después: {self.sat_state}")
            self._as_force_cfdi_log(f"Message después: {self.message or 'Sin mensaje'}")
            
            if self.attachment_id:
                self._as_force_cfdi_log(f"Attachment creado: {self.attachment_id.name}")
                self._as_force_cfdi_log(f"Attachment UUID: {self.attachment_uuid or 'None'}")
                self._as_post_chatter_force_cfdi(
                    f"✅ CFDI generado exitosamente. UUID: {self.attachment_uuid or 'Pendiente'}", 
                    'success'
                )
            else:
                warning_msg = "No se generó attachment después del Force CFDI"
                self._as_force_cfdi_log(warning_msg, 'warning')
                self._as_post_chatter_force_cfdi(warning_msg, 'warning')
            
            self._as_force_cfdi_log(f"=== FORCE CFDI COMPLETADO ===")
            return result
            
        except Exception as e:
            # Log detallado del error
            execution_time = time.time() - start_time
            error_msg = f"ERROR en Force CFDI después de {execution_time:.2f}s: {str(e)}"
            traceback_str = traceback.format_exc()
            
            self._as_force_cfdi_log(error_msg, 'error')
            self._as_force_cfdi_log(f"Traceback completo: {traceback_str}", 'error')
            
            self._as_post_chatter_force_cfdi(f"❌ Error en Force CFDI: {str(e)}", 'error')
            
            # Re-lanzar la excepción para que el flujo normal la maneje
            raise


class AsMxAccountPayment(models.Model):
    """
    Propósito: Hereda account.payment para añadir debugging a Force CFDI payment
    """
    _inherit = 'account.payment'

    def _as_payment_force_log(self, message, level='info'):
        """
        Propósito: Registra logs específicos para pagos Force CFDI
        Parámetros: message (mensaje), level (nivel de log)
        Retorno: None
        """
        trace_id = f"PAYMENT-FORCE-{self.id}-{int(time.time())}"
        formatted_message = f"[{trace_id}] {message}"
        
        if level == 'error':
            _logger.error(f"[AS_PAYMENT_FORCE] {formatted_message}")
        elif level == 'warning':
            _logger.warning(f"[AS_PAYMENT_FORCE] {formatted_message}")
        else:
            _logger.info(f"[AS_PAYMENT_FORCE] {formatted_message}")

    def _as_post_chatter_payment_force(self, message, message_type='info'):
        """
        Propósito: Publica mensaje en el chatter del payment
        Parámetros: message (mensaje), message_type (tipo de mensaje)
        Retorno: None
        """
        try:
            icon = '🔥' if message_type == 'success' else '⚠️' if message_type == 'warning' else '❌' if message_type == 'error' else 'ℹ️'
            body = f"<p><strong>{icon} PAYMENT FORCE CFDI:</strong> {message}</p>"
            
            self.message_post(
                body=body,
                subject="Payment Force CFDI - Debug Info",
                message_type='comment',
                subtype_xmlid='mail.mt_note',
                body_is_html=True
            )
        except Exception as e:
            _logger.error(f"[AS_PAYMENT_FORCE] Error posting to chatter: {e}")

    def l10n_mx_edi_cfdi_payment_force_try_send(self):
        """
        Propósito: Hereda y extiende la función para forzar envío de CFDI de pago
        Retorno: Resultado de la función original
        """
        self.ensure_one()
        
        # Log inicial
        start_time = time.time()
        # self._as_payment_force_log(f"=== INICIANDO PAYMENT FORCE TRY SEND ===")
        # self._as_payment_force_log(f"Payment ID: {self.id}")
        # self._as_payment_force_log(f"Payment Name: {self.name}")
        # self._as_payment_force_log(f"Payment State: {self.state}")
        # self._as_payment_force_log(f"Amount: {self.amount}")
        # self._as_payment_force_log(f"Currency: {self.currency_id.name}")
        # self._as_payment_force_log(f"Partner: {self.partner_id.name if self.partner_id else 'None'}")
        # self._as_payment_force_log(f"Move ID: {self.move_id.id if self.move_id else 'None'}")
        # self._as_payment_force_log(f"Move Name: {self.move_id.name if self.move_id else 'None'}")
        
        # Información de documentos CFDI existentes
        if self.move_id:
            payment_docs = self.move_id.l10n_mx_edi_payment_document_ids
            self._as_payment_force_log(f"Documentos de pago existentes: {len(payment_docs)}")
            for doc in payment_docs:
                self._as_payment_force_log(f"  - Doc {doc.id}: State={doc.state}, SAT={doc.sat_state}")
        
        # Chatter message
        self._as_post_chatter_payment_force(f"Iniciando forzado de CFDI de pago para {self.name}", 'info')
        
        try:
            # Llamar al método original que delega a move_id
            self._as_payment_force_log("Llamando al método original l10n_mx_edi_cfdi_payment_force_try_send")
            
            result = super().l10n_mx_edi_cfdi_payment_force_try_send()
            
            # Log después de la ejecución
            execution_time = time.time() - start_time
            self._as_payment_force_log(f"Método ejecutado en {execution_time:.2f} segundos")
            
            # Verificar documentos después del proceso
            if self.move_id:
                updated_payment_docs = self.move_id.l10n_mx_edi_payment_document_ids
                self._as_payment_force_log(f"Documentos después del proceso: {len(updated_payment_docs)}")
                
                # Buscar nuevos documentos
                new_docs = updated_payment_docs.filtered(lambda d: d.create_date >= fields.Datetime.now() - timedelta(minutes=1))
                if new_docs:
                    for doc in new_docs:
                        self._as_payment_force_log(f"NUEVO documento creado - ID: {doc.id}, State: {doc.state}")
                        self._as_post_chatter_payment_force(
                            f"✅ Nuevo documento CFDI creado (ID: {doc.id})", 
                            'success'
                        )
                else:
                    warning_msg = "No se crearon nuevos documentos CFDI"
                    self._as_payment_force_log(warning_msg, 'warning')
                    self._as_post_chatter_payment_force(warning_msg, 'warning')
            
            self._as_payment_force_log(f"=== PAYMENT FORCE TRY SEND COMPLETADO ===")
            return result
            
        except Exception as e:
            # Log detallado del error
            execution_time = time.time() - start_time
            error_msg = f"ERROR en Payment Force después de {execution_time:.2f}s: {str(e)}"
            traceback_str = traceback.format_exc()
            
            self._as_payment_force_log(error_msg, 'error')
            self._as_payment_force_log(f"Traceback: {traceback_str}", 'error')
            
            self._as_post_chatter_payment_force(f"❌ Error en Force CFDI: {str(e)}", 'error')
            
            # Re-lanzar la excepción
            raise


class AsMxAccountMove(models.Model):
    """
    Propósito: Hereda account.move para añadir debugging a Force CFDI payment
    """
    _inherit = 'account.move'

    def _as_payment_force_log(self, message, level='info'):
        """
        Propósito: Registra logs específicos para pagos Force CFDI
        Parámetros: message (mensaje), level (nivel de log)
        Retorno: None
        """
        trace_id = f"MOVE-FORCE-{self.id}-{int(time.time())}"
        formatted_message = f"[{trace_id}] {message}"
        
        if level == 'error':
            _logger.error(f"[AS_MOVE_FORCE] {formatted_message}")
        elif level == 'warning':
            _logger.warning(f"[AS_MOVE_FORCE] {formatted_message}")
        else:
            _logger.info(f"[AS_MOVE_FORCE] {formatted_message}")

    def l10n_mx_edi_cfdi_payment_force_try_send(self):
        """
        Propósito: Hereda y extiende la función para forzar envío de CFDI de pago
        Retorno: Resultado de la función original
        """
        self.ensure_one()
        
        # Log inicial
        start_time = time.time()
        self._as_payment_force_log(f"=== INICIANDO PAYMENT FORCE TRY SEND ===")
        self._as_payment_force_log(f"Move ID: {self.id}")
        self._as_payment_force_log(f"Move Name: {self.name}")
        self._as_payment_force_log(f"Move Type: {self.move_type}")
        self._as_payment_force_log(f"State: {self.state}")
        self._as_payment_force_log(f"Amount: {self.amount if hasattr(self, 'amount') else 'N/A'}")
        self._as_payment_force_log(f"Currency: {self.currency_id.name}")
        self._as_payment_force_log(f"Partner: {self.partner_id.name if self.partner_id else 'None'}")
        
        # Información de documentos CFDI existentes
        payment_docs = self.l10n_mx_edi_payment_document_ids
        self._as_payment_force_log(f"Documentos de pago existentes: {len(payment_docs)}")
        for doc in payment_docs:
            self._as_payment_force_log(f"  - Doc {doc.id}: State={doc.state}, SAT={doc.sat_state}")
        
        # Chatter message
        try:
            self.message_post(
                body=f"<p><strong>🔥 PAYMENT FORCE CFDI:</strong> Iniciando forzado de CFDI de pago</p>",
                subject="Payment Force CFDI - Inicio",
                message_type='comment',
                subtype_xmlid='mail.mt_note',
                body_is_html=True
            )
        except Exception as chatter_error:
            self._as_payment_force_log(f"Error en chatter: {chatter_error}", 'warning')
        
        try:
            # Llamar al método original con force_cfdi=True
            self._as_payment_force_log("Llamando a _l10n_mx_edi_cfdi_payment_try_send con force_cfdi=True")
            
            result = super().l10n_mx_edi_cfdi_payment_force_try_send()
            
            # Log después de la ejecución
            execution_time = time.time() - start_time
            self._as_payment_force_log(f"Método ejecutado en {execution_time:.2f} segundos")
            
            # Verificar documentos después del proceso
            updated_payment_docs = self.l10n_mx_edi_payment_document_ids
            self._as_payment_force_log(f"Documentos después del proceso: {len(updated_payment_docs)}")
            
            new_docs = updated_payment_docs - payment_docs
            if new_docs:
                for doc in new_docs:
                    self._as_payment_force_log(f"NUEVO documento creado - ID: {doc.id}, State: {doc.state}")
                    try:
                        self.message_post(
                            body=f"<p><strong>✅ PAYMENT FORCE CFDI:</strong> Nuevo documento CFDI creado (ID: {doc.id})</p>",
                            subject="Payment Force CFDI - Documento Creado",
                            message_type='comment',
                            subtype_xmlid='mail.mt_note',
                            body_is_html=True
                        )
                    except:
                        pass
            else:
                warning_msg = "No se crearon nuevos documentos CFDI"
                self._as_payment_force_log(warning_msg, 'warning')
                try:
                    self.message_post(
                        body=f"<p><strong>⚠️ PAYMENT FORCE CFDI:</strong> {warning_msg}</p>",
                        subject="Payment Force CFDI - Advertencia",
                        message_type='comment',
                        subtype_xmlid='mail.mt_note',
                        body_is_html=True
                    )
                except:
                    pass
            
            self._as_payment_force_log(f"=== PAYMENT FORCE TRY SEND COMPLETADO ===")
            return result
            
        except Exception as e:
            # Log detallado del error
            execution_time = time.time() - start_time
            error_msg = f"ERROR en Payment Force después de {execution_time:.2f}s: {str(e)}"
            traceback_str = traceback.format_exc()
            
            self._as_payment_force_log(error_msg, 'error')
            self._as_payment_force_log(f"Traceback: {traceback_str}", 'error')
            
            try:
                self.message_post(
                    body=f"<p><strong>❌ PAYMENT FORCE CFDI ERROR:</strong> {str(e)}</p>",
                    subject="Payment Force CFDI - Error",
                    message_type='comment',
                    subtype_xmlid='mail.mt_note',
                    body_is_html=True
                )
            except:
                pass
            
            # Re-lanzar la excepción
            raise 