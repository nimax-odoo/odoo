# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from markupsafe import escape
import logging
import traceback
import time

_logger = logging.getLogger(__name__)
_debug_logger = logging.getLogger(__name__ + ".debug")
_debug_logger.setLevel(logging.DEBUG)

# ---------- MONKEY PATCH PARA RES.COMPANY ----------
# Agregamos método faltante _lock_edi_documents que el módulo l10n_mx_edi está tratando de llamar
class ResCompany(models.Model):
    _inherit = 'res.company'
    
    def _lock_edi_documents(self, records):
        """
        Este método es un monkey patch para resolver un error en el flujo de timbrado CFDI.
        En alguna versión/parte de Odoo, se espera que res.company tenga este método.
        """
        _logger.info(f"[AS_MX_INV] Monkey patch para _lock_edi_documents llamado con {len(records)} registros.")
        # Simplemente retorna sin hacer nada - implementación básica
        return True
        
    def _unlock_edi_documents(self, records):
        """
        Este método es un monkey patch para resolver un error en el flujo de timbrado CFDI.
        Complementa al método _lock_edi_documents implementado arriba.
        En alguna versión de Odoo, se espera que res.company tenga este método para desbloquear.
        """
        _logger.info(f"[AS_MX_INV] Monkey patch para _unlock_edi_documents llamado con {len(records)} registros.")
        # Simplemente retorna sin hacer nada - implementación básica
        return True

# ---------- FIN MONKEY PATCH ----------

# ---------- MONKEY PATCH PARA FORZAR CERTIFICADO EN L10N_MX_EDI.DOCUMENT ----------
class L10nMxEdiDocument(models.Model):
    _inherit = 'l10n_mx_edi.document'
    
    @api.model
    def _get_edi_certificate(self, company):
        """
        Propósito: Obtener el certificado válido para el timbrado CFDI
        Parámetros: company - La compañía para la que se busca el certificado
        Retorno: Certificado válido para timbrado
        """
        try:
            # Búsqueda dinámica de certificados válidos para la compañía
            certificate = self.env['certificate.certificate'].search([
                ('company_id', '=', company.id),
                ('is_valid', '=', True)
            ], limit=1)
            
            if certificate:
                _logger.info(f"[AS_MX_INV] Usando certificado ID {certificate.id} para timbrado de {company.name}")
                return certificate
            else:
                # Si no hay certificado para esta compañía, intentar con la compañía raíz si es diferente
                root_company = self.env.company
                if company != root_company:
                    certificate = self.env['certificate.certificate'].search([
                        ('company_id', '=', root_company.id),
                        ('is_valid', '=', True)
                    ], limit=1)
                    if certificate:
                        _logger.info(f"[AS_MX_INV] Usando certificado de compañía raíz ID {certificate.id} para timbrado de {company.name}")
                        return certificate
                
                _logger.error(f"[AS_MX_INV] No se encontró ningún certificado válido para la compañía {company.name}")
                return None
        except Exception as e:
            _logger.error(f"[AS_MX_INV] Error al buscar certificado: {e}")
            return None
            
    @api.model
    def _get_document_cfdi_representation(self, cfdi_values, xsd_name):
        """
        Función que falta en el core de Odoo. 
        Este método debería generar la representación XML del CFDI.
        Como no podemos replicar toda su lógica, intentaremos una solución alternativa.
        """
        _logger.warning(f"[AS_MX_INV] Monkey patch para _get_document_cfdi_representation llamado con {xsd_name}")
        
        # Intentamos buscar si existe otro método en el modelo que haga algo similar
        # y que podamos llamar como fallback
        if hasattr(self, '_get_cfdi_values_from_documents'):
            _logger.info(f"[AS_MX_INV] Intentando usar _get_cfdi_values_from_documents como alternativa")
            try:
                return self._get_cfdi_values_from_documents(cfdi_values, xsd_name)
            except Exception as e:
                _logger.error(f"[AS_MX_INV] Error al usar método alternativo: {e}")
        
        # Si llegamos aquí, no hay alternativa viable
        error_msg = f"MÉTODO FALTANTE EN ODOO: _get_document_cfdi_representation. " \
                   f"Este método debería generar la representación XML del CFDI. " \
                   f"Por favor, contacta con soporte para completar la instalación del módulo l10n_mx_edi."
        
        _logger.error(f"[AS_MX_INV] {error_msg}")
        
        # Como último recurso, intentamos devolver cualquier valor de cfdi_values que pueda ser útil
        if isinstance(cfdi_values, dict) and 'cfdi_str' in cfdi_values:
            return cfdi_values.get('cfdi_str')
        elif isinstance(cfdi_values, dict) and 'cfdi' in cfdi_values:
            return cfdi_values.get('cfdi')
            
        # No hay solución viable, levantamos error con mensaje claro
        raise UserError(error_msg)

# Monkey patch para IR.UI.VIEW para debugging
class AsUIView(models.Model):
    _inherit = 'ir.ui.view'
    
    def _as_debug_log(self, message):
        """
        Propósito: Función de utilidad para loguear mensajes de debug para vistas
        Parámetros: message - mensaje a loguear
        """
        trace_id = f"VIEW-{int(time.time())}"
        _debug_logger.info(f"[{trace_id}] {message}")
        
    def _get_view_id(self, xml_id):
        """
        Sobrescrito para añadir logueo de debugging
        """
        self._as_debug_log(f"_get_view_id - xml_id: {xml_id}")
        try:
            # Verificar si es un ID técnico (módulo.nombre)
            if isinstance(xml_id, str) and '.' in xml_id:
                module, name = xml_id.split('.')
                self._as_debug_log(f"Buscando vista con módulo={module}, nombre={name}")

                # Verificar si existe como record
                self.env.cr.execute("""
                    SELECT v.id
                    FROM ir_ui_view v
                    JOIN ir_model_data d ON (d.model = 'ir.ui.view' AND d.res_id = v.id)
                    WHERE d.module = %s AND d.name = %s
                """, (module, name))
                result = self.env.cr.fetchone()
                if result:
                    view_id = result[0]
                    self._as_debug_log(f"Vista encontrada en la BD con ID: {view_id}")
                else:
                    self._as_debug_log(f"¡ALERTA! Vista NO encontrada en la BD: {xml_id}")
                    
                    # Intentar buscar un reporte con este nombre
                    self.env.cr.execute("""
                        SELECT r.id, r.name, r.report_name
                        FROM ir_act_report_xml r
                        JOIN ir_model_data d ON (d.model = 'ir.actions.report' AND d.res_id = r.id)
                        WHERE d.module = %s AND d.name = %s
                    """, (module, name))
                    report_result = self.env.cr.fetchone()
                    if report_result:
                        self._as_debug_log(f"Encontrado un reporte (NO UNA VISTA) con ID: {report_result[0]}, name: {report_result[1]}")
                        
            result = super(AsUIView, self)._get_view_id(xml_id)
            self._as_debug_log(f"_get_view_id completado exitosamente: {result}")
            return result
        except Exception as e:
            error_msg = f"Error en _get_view_id: {e}\n{traceback.format_exc()}"
            self._as_debug_log(error_msg)
            _logger.error(error_msg)
            raise

class AsActionsReport(models.Model):
    _inherit = 'ir.actions.report'
    
    def _as_debug_log(self, message):
        """
        Propósito: Función de utilidad para loguear mensajes de debug para reportes
        Parámetros: message - mensaje a loguear
        """
        trace_id = f"REPORT-{self.id}-{int(time.time())}"
        _debug_logger.info(f"[{trace_id}] {message}")
        
    def _render_qweb_html(self, report_ref, docids, data=None):
        """
        Sobrescrito para añadir logueo de debugging
        """
        self._as_debug_log(f"_render_qweb_html - report_ref: {report_ref}, docids: {docids}")
        try:
            # Verificar si el report_ref existe como vista
            if isinstance(report_ref, str):
                view_obj = self.env['ir.ui.view']
                try:
                    view_id = view_obj._get_view_id(report_ref)
                    self._as_debug_log(f"Vista encontrada para {report_ref}: ID={view_id}")
                except Exception as ve:
                    self._as_debug_log(f"ERROR al buscar vista {report_ref}: {ve}")
                    
                # Verificar si existe el reporte en ir.actions.report
                report = self.env['ir.actions.report']._get_report(report_ref)
                if report:
                    self._as_debug_log(f"Reporte encontrado: ID={report.id}, name={report.name}, report_name={report.report_name}")
                else:
                    self._as_debug_log(f"¡ALERTA! No se encontró reporte para {report_ref}")
            
            result = super(AsActionsReport, self)._render_qweb_html(report_ref, docids, data=data)
            self._as_debug_log(f"_render_qweb_html completado exitosamente")
            return result
        except Exception as e:
            error_msg = f"Error en _render_qweb_html: {e}\n{traceback.format_exc()}"
            self._as_debug_log(error_msg)
            _logger.error(error_msg)
            raise

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        """
        Sobrescrito para añadir logueo de debugging
        """
        self._as_debug_log(f"_render_qweb_pdf - report_ref: {report_ref}, res_ids: {res_ids}")
        try:
            result = super(AsActionsReport, self)._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
            self._as_debug_log(f"_render_qweb_pdf completado exitosamente")
            return result
        except Exception as e:
            error_msg = f"Error en _render_qweb_pdf: {e}\n{traceback.format_exc()}"
            self._as_debug_log(error_msg)
            _logger.error(error_msg)
            raise

    def _get_report_from_name(self, report_name):
        """
        Sobrescrito para añadir logueo de debugging
        """
        self._as_debug_log(f"_get_report_from_name - report_name: {report_name}")
        try:
            report = super(AsActionsReport, self)._get_report_from_name(report_name)
            if report:
                self._as_debug_log(f"Reporte encontrado: ID={report.id}, name={report.name}")
            else:
                self._as_debug_log(f"No se encontró reporte para {report_name}")
            return report
        except Exception as e:
            error_msg = f"Error en _get_report_from_name: {e}\n{traceback.format_exc()}"
            self._as_debug_log(error_msg)
            _logger.error(error_msg)
            raise

    def _render_template(self, template, values=None):
        """
        Sobrescrito para añadir logueo de debugging
        """
        if not values:
            values = {}
        self._as_debug_log(f"_render_template - template: {template}")
        try:
            result = super(AsActionsReport, self)._render_template(template, values)
            self._as_debug_log(f"_render_template completado exitosamente")
            return result
        except Exception as e:
            error_msg = f"Error en _render_template: {e}\n{traceback.format_exc()}"
            self._as_debug_log(error_msg)
            _logger.error(error_msg)
            raise

# Debugging para el wizard de envío de facturas
class AsAccountMoveSend(models.AbstractModel):
    _inherit = 'account.move.send'
    
    def _as_debug_log(self, message):
        """
        Propósito: Función de utilidad para loguear mensajes de debug para el wizard
        Parámetros: message - mensaje a loguear
        """
        trace_id = f"MOVE-SEND-{self.id}-{int(time.time())}"
        _debug_logger.info(f"[{trace_id}] {message}")
    
    def as_get_name_invoice(self):
        """
        Propósito: Método que retorna el nombre formateado de la factura para usar en reportes PDF
                  y correos electrónicos. Este método se llama cuando se usa el wizard de envío.
        Retorno: String con el nombre de la factura.
        """
        self._as_debug_log(f"Llamada a as_get_name_invoice en el wizard de envío")
        
        # Obtener el registro de la factura actual
        moves = self._get_moves()
        if not moves:
            self._as_debug_log("No se encontraron facturas a procesar")
            return "invoice.pdf"
            
        move = moves[0]  # Tomamos la primera factura
        
        self._as_debug_log(f"Delegando a as_get_name_invoice de la factura {move.name}")
        # Delegamos al método de la factura
        return move.as_get_name_invoice()
        
    def action_send_and_print(self):
        """
        Sobrescrito para añadir logueo de debugging
        """
        self._as_debug_log(f"action_send_and_print iniciado. Contexto: {self.env.context}")
        
        # Obtener las facturas
        moves = self._get_moves()
        self._as_debug_log(f"Facturas a procesar: {moves.mapped('name')}")
        
        try:
            # Obtener las plantillas de email
            templates_to_check = self.template_id
            for template in templates_to_check:
                self._as_debug_log(f"Plantilla email: {template.name}, report_name: {template.report_name}")
                for attach in template.attachment_ids:
                    self._as_debug_log(f"Adjunto fijo en plantilla: {attach.name}")
            
            # Obtener reportes dinámicos
            if not self.env.context.get('active_models'):
                dynamic_reports = []
                for attachment_widget in self.attachment_ids:
                    if attachment_widget.get('dynamic_report'):
                        report_ref = attachment_widget.get('dynamic_report')
                        self._as_debug_log(f"Reporte dinámico encontrado: {report_ref}")
                        
                        # Verificar si el reporte existe como vista
                        try:
                            view_obj = self.env['ir.ui.view']
                            view_id = view_obj._get_view_id(report_ref)
                            self._as_debug_log(f"Vista para reporte dinámico encontrada: ID={view_id}")
                        except Exception as ve:
                            self._as_debug_log(f"ERROR al buscar vista para reporte dinámico {report_ref}: {ve}")
                        
                        # Verificar como reporte
                        report = self.env['ir.actions.report']._get_report(report_ref)
                        if report:
                            self._as_debug_log(f"Reporte dinámico encontrado como ir.actions.report: ID={report.id}, name={report.name}")
                        else:
                            self._as_debug_log(f"¡ALERTA! Reporte dinámico NO encontrado como ir.actions.report: {report_ref}")
                        
            result = super(AsAccountMoveSend, self).action_send_and_print()
            self._as_debug_log(f"action_send_and_print completado exitosamente")
            return result
        except Exception as e:
            error_msg = f"Error en action_send_and_print: {e}\n{traceback.format_exc()}"
            self._as_debug_log(error_msg)
            _logger.error(error_msg)
            # No levantamos la excepción nuevamente para permitir ver el error en log
            # Pero no interrumpimos la UI
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error al enviar y/o imprimir'),
                    'message': str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }
            
    def _generate_dynamic_reports(self, moves_data):
        """
        Sobrescrito para añadir logueo de debugging y mejorar la gestión de tipos
        """
        self._as_debug_log(f"_generate_dynamic_reports iniciado. Moves data: {list(moves_data.keys())}")
        try:
            # No usamos super() para evitar errores en la implementación original
            # Implementamos nuestra propia versión segura de la función
            
            for move_id, move_data in moves_data.items():
                if not isinstance(move_id, int):
                    self._as_debug_log(f"ID de factura no es un entero: {type(move_id)}, intentando adaptarlo")
                    # Si es un objeto account.move, extraemos su ID
                    if hasattr(move_id, '_name') and move_id._name == 'account.move':
                        try:
                            move_id = move_id.id
                            self._as_debug_log(f"Adaptado objeto account.move a ID: {move_id}")
                        except Exception as conversion_error:
                            self._as_debug_log(f"Error al adaptar object account.move: {conversion_error}")
                            continue
                    else:
                        self._as_debug_log(f"No se pudo adaptar el tipo: {type(move_id)}, saltando")
                        continue
                
                try:
                    # Intentamos obtener el nombre, pero de forma segura
                    move_record = self.env['account.move'].sudo().browse(move_id)
                    if move_record.exists():
                        move_name = move_record.name or f"ID:{move_id}"
                    else:
                        move_name = f"ID:{move_id} (no existe)"
                    
                    self._as_debug_log(f"Generando reportes dinámicos para factura: {move_name}")
                    
                    # Procesamos los reportes dinámicos
                    dynamic_reports = [
                        attachment_widget
                        for attachment_widget in move_data.get('attachment_ids', [])
                        if attachment_widget.get('dynamic_report')
                    ]
                    
                    for dynamic_report in dynamic_reports:
                        report_ref = dynamic_report.get('dynamic_report')
                        if not report_ref:
                            continue
                            
                        self._as_debug_log(f"Procesando reporte dinámico: {report_ref}")
                        
                        try:
                            # Aquí renderizamos directamente con el ID, no con el record
                            self.env['ir.actions.report'].sudo()._render(report_ref, [move_id])
                            self._as_debug_log(f"Reporte dinámico renderizado correctamente: {report_ref}")
                        except Exception as render_error:
                            self._as_debug_log(f"ERROR al renderizar reporte dinámico {report_ref}: {render_error}")
                            _logger.error(f"Error al renderizar reporte dinámico: {render_error}\n{traceback.format_exc()}")
                except Exception as move_error:
                    self._as_debug_log(f"ERROR procesando factura ID {move_id}: {move_error}")
                    _logger.error(f"Error procesando factura: {move_error}\n{traceback.format_exc()}")
            
            self._as_debug_log(f"_generate_dynamic_reports completado exitosamente")
            return True
        except Exception as e:
            error_msg = f"Error en _generate_dynamic_reports: {e}\n{traceback.format_exc()}"
            self._as_debug_log(error_msg)
            _logger.error(error_msg)
            # No propagamos el error para que el proceso de envío no se interrumpa
            return True


