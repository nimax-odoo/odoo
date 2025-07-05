#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
import logging

_logger = logging.getLogger(__name__)

class AsMxInvoiceCheckPAC(models.AbstractModel):
    _name = 'as_mx_invoice.check_pac'
    _description = 'Herramienta de verificación de PAC y certificados'

    def action_check_pac_config(self):
        """
        Verifica la configuración de PAC y certificados para compañías mexicanas.
        Puede ser llamada desde una acción del servidor o desde código.
        Guarda los resultados en el chatter de la factura actual.
        """
        self.ensure_one()
        output = []
        
        # Detectar la factura desde el contexto o el registro actual
        invoice = False
        active_model = self._context.get('active_model')
        active_id = self._context.get('active_id')
        
        if active_model == 'account.move' and active_id:
            invoice = self.env['account.move'].browse(active_id)
            if not invoice.exists() or invoice.move_type not in ('out_invoice', 'out_refund'):
                invoice = False
        
        if not invoice:
            return "No se encontró una factura válida para aplicar el análisis de PAC."
        
        # Función auxiliar para agregar texto al output
        def add_output(text):
            _logger.info(text)
            output.append(text)
        
        add_output('\n====== VERIFICACIÓN DATOS PAC Y CERTIFICADOS (POR AS) ======')
        add_output(f'Factura analizada: {invoice.name} (ID: {invoice.id})')

        # --- Mostrar datos de las compañías mexicanas ---
        company = invoice.company_id
        add_output(f'\n-- DETALLES DE LA COMPAÑÍA DE LA FACTURA --')

        add_output(f'\nID: {company.id} | Nombre: {company.name}')
        add_output(f'RFC: {company.partner_id.vat}')
    
        # Datos PAC (pueden no existir todos los campos)
        pac_name = getattr(company, 'l10n_mx_edi_pac', 'campo_no_existe')
        pac_test = getattr(company, 'l10n_mx_edi_pac_test_env', 'campo_no_existe')
        pac_user = getattr(company, 'l10n_mx_edi_pac_username', 'campo_no_existe')
        pac_pass = getattr(company, 'l10n_mx_edi_pac_password', 'campo_no_existe')
        
        # Ver si hay password configurado
        has_password = False if pac_pass == 'campo_no_existe' else bool(pac_pass)
        
        add_output(f'PAC Nombre: {pac_name}')
        add_output(f'PAC Test Mode: {pac_test}')
        add_output(f'PAC User: {pac_user}')
        add_output(f'PAC Password Set: {"Sí" if has_password else "No"}')
        
        # Buscar certificados de la compañía
        add_output('\n---- Certificados modernos (certificate.certificate):')
        certs = self.env['certificate.certificate'].search([('company_id', '=', company.id)])
        if certs:
            for cert in certs:
                valid_txt = "VÁLIDO" if cert.is_valid else "INVÁLIDO"
                add_output(f'ID: {cert.id} | Nombre: {cert.name} | Estado: {valid_txt}')
                # Verificar fechas si existen
                if hasattr(cert, 'date_start') and hasattr(cert, 'date_end'):
                    add_output(f'Vigencia: {cert.date_start} - {cert.date_end}')
                add_output(f'Tiene PEM: {"Sí" if cert.pem_certificate else "NO"}')
                add_output(f'Tiene clave (.key): {"Sí" if cert.private_key_id.id else "NO"}')
        else:
            add_output('No se encontraron certificados modernos')
        
        # Certificados antiguos en l10n_mx_edi.certificate (versiones anteriores)
        add_output('\n---- Certificados antiguos (l10n_mx_edi.certificate):')
        old_certs = self.env['l10n_mx_edi.certificate'].search([('company_id', '=', company.id)])
        if old_certs:
            for cert in old_certs:
                valid_txt = "VÁLIDO" if cert.state == 'valid' else f"INVÁLIDO ({cert.state})"
                add_output(f'ID: {cert.id} | Nombre: {cert.name} | Estado: {valid_txt}')
                # Verificar fechas si existen
                if hasattr(cert, 'date_start') and hasattr(cert, 'date_end'):
                    add_output(f'Vigencia: {cert.date_start} - {cert.date_end}')
        else:
            add_output('No se encontraron certificados antiguos')
        
        # --- Detalles de esta factura ---
        add_output('\n-- DETALLES DE LA FACTURA ACTUAL:')
        add_output(f'Nombre: {invoice.name} (ID: {invoice.id}) | Fecha: {invoice.invoice_date}')
        add_output(f'Cliente: {invoice.partner_id.name} | RFC: {invoice.partner_id.vat}')
        add_output(f'Necesita CFDI: {invoice.l10n_mx_edi_is_cfdi_needed}')
        add_output(f'Estado CFDI: {invoice.l10n_mx_edi_cfdi_state or "Sin timbrar"}')
        add_output(f'UUID CFDI: {invoice.l10n_mx_edi_cfdi_uuid or "N/A"}')
        add_output(f'Método Pago: {invoice.l10n_mx_edi_payment_method_id.name or "No configurado"} ({invoice.l10n_mx_edi_payment_method_id.code or "N/A"})')
        add_output(f'Uso CFDI: {invoice.l10n_mx_edi_usage or "No configurado"}')
        add_output(f'Régimen Fiscal: {invoice.l10n_mx_edi_fiscal_regime or "No configurado"}')
        
        # Verificar si hay documento EDI generado
        edi_docs = self.env['l10n_mx_edi.document'].search([('move_id', '=', invoice.id)], limit=1)
        if edi_docs:
            doc = edi_docs[0]
            add_output(f'Documento EDI ID: {doc.id} | Estado: {doc.state}')
            add_output(f'Content XML: {"Tiene content" if doc.content else "Sin content"}')
            add_output(f'Content PDF: {"Tiene attachment" if doc.attachment_id else "Sin attachment"}')
            if doc.message:
                add_output(f'Mensaje EDI: {doc.message}')
        else:
            add_output('No tiene documento EDI generado')
        
        # --- Revisar requisitos críticos para timbrado ---
        add_output('\n-- REQUISITOS CRÍTICOS PARA TIMBRADO:')
        # 1. RFC Emisor (Compañía)
        if not company.partner_id.vat or not company.partner_id.vat.startswith('MX'):
            add_output('❌ FALTA RFC correcto en la compañía')
        else:
            add_output('✅ RFC de compañía OK')
            
        # 2. RFC Receptor (Cliente)
        if not invoice.partner_id.vat:
            add_output('❌ FALTA RFC en el cliente')
        else:
            add_output('✅ RFC de cliente OK')
            
        # 3. Régimen Fiscal Emisor
        if not getattr(company, 'l10n_mx_edi_fiscal_regime', False):
            add_output('❌ FALTA Régimen Fiscal en la compañía')
        else:
            add_output('✅ Régimen Fiscal de compañía OK')
            
        # 4. Régimen Fiscal Receptor
        if not invoice.l10n_mx_edi_fiscal_regime:
            add_output('❌ FALTA Régimen Fiscal en el cliente')
        else:
            add_output('✅ Régimen Fiscal de cliente OK')
            
        # 5. Certificado
        valid_cert = self.env['certificate.certificate'].search_count([
            ('company_id', '=', company.id),
            ('is_valid', '=', True)
        ])
        if not valid_cert:
            add_output('❌ NO hay certificado válido')
        else:
            add_output('✅ Certificado válido encontrado')
            
        # 6. Configuración PAC
        if pac_name == 'campo_no_existe' or pac_user == 'campo_no_existe' or not has_password:
            add_output('❌ FALTA configuración completa del PAC')
        else:
            add_output('✅ Configuración de PAC parece completa')
            
        # 7. Método de Pago
        if not invoice.l10n_mx_edi_payment_method_id:
            add_output('❌ FALTA Método de Pago SAT')
        else:
            add_output('✅ Método de Pago SAT configurado')
            
        # 8. Uso CFDI
        if not invoice.l10n_mx_edi_usage:
            add_output('❌ FALTA Uso CFDI')
        else:
            add_output('✅ Uso CFDI configurado')
            
        # 9. Código Postal del lugar de expedición
        if not company.partner_id.zip:
            add_output('❌ FALTA Código Postal en dirección de compañía')
        else:
            add_output('✅ Código Postal de compañía OK')
            
        # 10. Líneas de factura
        lines_check = []
        for line in invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product'):
            if not line.product_id:
                lines_check.append(f'❌ Línea {line.name[:20]}... sin producto')
            elif not getattr(line.product_id, 'unspsc_code_id', True):
                lines_check.append(f'❌ Producto {line.product_id.name[:20]}... sin clave SAT producto')
            elif not getattr(line.product_uom_id, 'unspsc_code_id', True):
                lines_check.append(f'❌ Unidad de medida {line.product_uom_id.name} sin clave SAT')
        
        if lines_check:
            for check in lines_check:
                add_output(check)
        else:
            add_output('✅ Líneas de factura parecen válidas')
        
        add_output('\n========= FIN VERIFICACIÓN PAC Y CERTIFICADOS =========')
        
        # Guardar en el chatter de la factura
        result_text = '\n'.join(output)
        invoice.message_post(
            body=f"<pre>{result_text}</pre>",
            subject="Verificación de PAC y Certificados (AS)",
            message_type='comment',
            subtype_xmlid='mail.mt_note',
            body_is_html=True
        )
        
        # Return para poder verlo en la respuesta
        return result_text
        
    def check_pac_certificate(self, certificate_id=None):
        """
        Verifica un certificado específico o busca certificados válidos.
        @param certificate_id: ID del certificado a verificar (opcional)
        @return: Texto con resultados de la verificación
        """
        output = []
        
        # Detectar la factura desde el contexto o el registro actual
        invoice = False
        active_model = self._context.get('active_model')
        active_id = self._context.get('active_id')
        
        if active_model == 'account.move' and active_id:
            invoice = self.env['account.move'].browse(active_id)
            if not invoice.exists() or invoice.move_type not in ('out_invoice', 'out_refund'):
                invoice = False
        
        # Función auxiliar para agregar texto al output
        def add_output(text):
            _logger.info(text)
            output.append(text)
            
        add_output('\n====== VERIFICACIÓN CERTIFICADO ESPECÍFICO (POR AS) ======')
        
        # Si nos pasan un ID específico, buscamos ese certificado
        if certificate_id:
            add_output(f'\n-- VERIFICANDO CERTIFICADO ID: {certificate_id} --')
            
            # Primero buscar en el modelo moderno
            cert = self.env['certificate.certificate'].browse(certificate_id)
            if cert.exists():
                add_output(f'Certificado encontrado en modelo "certificate.certificate"')
                add_output(f'ID: {cert.id} | Nombre: {cert.name}')
                add_output(f'Para compañía: {cert.company_id.name} (ID: {cert.company_id.id})')
                add_output(f'Es válido: {"Sí" if cert.is_valid else "NO"}')
                if hasattr(cert, 'date_start') and hasattr(cert, 'date_end'):
                    add_output(f'Vigencia: {cert.date_start} - {cert.date_end}')
                add_output(f'Tiene PEM: {"Sí" if cert.pem_certificate else "NO"}')
                add_output(f'Tiene clave (.key): {"Sí" if cert.private_key_id.id else "NO"}')
                
                # Intentar leer el contenido del certificado
                if cert.pem_certificate:
                    add_output(f'\nContent check: El certificado tiene {len(cert.pem_certificate)} bytes')
            
            # Buscar también en el modelo antiguo
            old_cert = self.env['l10n_mx_edi.certificate'].browse(certificate_id)
            if old_cert.exists():
                add_output(f'\nCertificado encontrado en modelo antiguo "l10n_mx_edi.certificate"')
                add_output(f'ID: {old_cert.id} | Nombre: {old_cert.name}')
                add_output(f'Para compañía: {old_cert.company_id.name} (ID: {old_cert.company_id.id})')
                add_output(f'Estado: {old_cert.state}')
                if hasattr(old_cert, 'date_start') and hasattr(old_cert, 'date_end'):
                    add_output(f'Vigencia: {old_cert.date_start} - {old_cert.date_end}')
            
            if not cert.exists() and not old_cert.exists():
                add_output(f'ERROR: No se encontró ningún certificado con ID {certificate_id}')
        else:
            # Buscar certificados válidos para todas las compañías
            add_output('\n-- BUSCANDO CERTIFICADOS VÁLIDOS --')
            
            companies = self.env['res.company'].search([])
            for company in companies:
                add_output(f'\nCompañía: {company.name} (ID: {company.id})')
                
                # Certificados modernos
                certs = self.env['certificate.certificate'].search([
                    ('company_id', '=', company.id),
                    ('is_valid', '=', True)
                ], limit=3)
                
                if certs:
                    add_output(f'Certificados válidos en modelo moderno: {len(certs)}')
                    for cert in certs:
                        add_output(f'- ID: {cert.id} | Nombre: {cert.name}')
                else:
                    add_output('No se encontraron certificados válidos en modelo moderno')
                
                # Certificados antiguos
                old_certs = self.env['l10n_mx_edi.certificate'].search([
                    ('company_id', '=', company.id),
                    ('state', '=', 'valid')
                ], limit=3)
                
                if old_certs:
                    add_output(f'Certificados válidos en modelo antiguo: {len(old_certs)}')
                    for cert in old_certs:
                        add_output(f'- ID: {cert.id} | Nombre: {cert.name}')
                else:
                    add_output('No se encontraron certificados válidos en modelo antiguo')
        
        add_output('\n========= FIN VERIFICACIÓN CERTIFICADO =========')
        
        # Si hay factura, guardar en su chatter
        result_text = '\n'.join(output)
        if invoice:
            invoice.message_post(
                body=f"<pre>{result_text}</pre>",
                subject="Verificación de Certificado (AS)",
                message_type='comment',
                subtype_xmlid='mail.mt_note',
                body_is_html=True
            )
            
        return result_text

    def action_fix_edi_documents(self):
        """
        Corrige documentos EDI que tienen problemas con el campo document_type inexistente.
        Este método verifica documentos EDI existentes y los repara para que puedan ser procesados
        correctamente.
        @return: Texto con resultados de la operación
        """
        # Detectar la factura desde el contexto o el registro actual
        invoice = False
        active_model = self._context.get('active_model')
        active_id = self._context.get('active_id')
        
        if active_model == 'account.move' and active_id:
            invoice = self.env['account.move'].browse(active_id)
            if not invoice.exists() or invoice.move_type not in ('out_invoice', 'out_refund'):
                invoice = False
        
        output = []
        def add_output(text):
            _logger.info(text)
            output.append(text)
            
        add_output('\n====== REPARACIÓN DE DOCUMENTOS EDI (POR AS) ======')
        
        # Si tenemos una factura específica, trabajamos con sus documentos EDI
        if invoice:
            add_output(f'Verificando documentos EDI para la factura: {invoice.name} (ID: {invoice.id})')
            edi_docs = self.env['l10n_mx_edi.document'].search([('move_id', '=', invoice.id)])
            if not edi_docs:
                # Crear un nuevo documento EDI
                add_output(f'No se encontraron documentos EDI para esta factura. Creando uno nuevo...')
                try:
                    edi_doc = self.env['l10n_mx_edi.document'].create({
                        'move_id': invoice.id,
                        'state': 'invoice_sent_failed',  # Estado inicial para intentar el envío
                        'datetime': fields.Datetime.now(),
                    })
                    add_output(f'✅ Documento EDI creado correctamente con ID: {edi_doc.id}')
                except Exception as e:
                    add_output(f'❌ Error al crear documento EDI: {str(e)}')
            else:
                add_output(f'Se encontraron {len(edi_docs)} documentos EDI para esta factura')
                for doc in edi_docs:
                    add_output(f'- ID: {doc.id} | Estado: {doc.state}')
                    # No necesitamos corregir nada si ya existen documentos EDI válidos
        else:
            # Si no tenemos factura específica, buscamos documentos EDI con problemas
            add_output('Buscando documentos EDI con posibles problemas...')
            # Documentos sin datetime (campo requerido)
            invalid_docs = self.env['l10n_mx_edi.document'].search([
                ('datetime', '=', False),
            ], limit=20)
            
            if invalid_docs:
                add_output(f'Se encontraron {len(invalid_docs)} documentos sin datetime')
                for doc in invalid_docs:
                    try:
                        doc.write({
                            'datetime': fields.Datetime.now(),
                        })
                        add_output(f'✅ Corregido documento ID: {doc.id} (Agregado datetime)')
                    except Exception as e:
                        add_output(f'❌ Error al corregir documento ID {doc.id}: {str(e)}')
            else:
                add_output('No se encontraron documentos sin datetime')
            
            # Documentos sin estado válido
            invalid_state_docs = self.env['l10n_mx_edi.document'].search([
                ('state', 'not in', ['invoice_sent', 'invoice_sent_failed', 'invoice_cancel_requested', 
                                    'invoice_cancel_requested_failed', 'invoice_cancel', 'invoice_cancel_failed', 
                                    'invoice_received', 'ginvoice_sent', 'ginvoice_sent_failed', 
                                    'ginvoice_cancel', 'ginvoice_cancel_failed', 'payment_sent_pue', 
                                    'payment_sent', 'payment_sent_failed', 'payment_cancel', 'payment_cancel_failed']),
            ], limit=20)
            
            if invalid_state_docs:
                add_output(f'Se encontraron {len(invalid_state_docs)} documentos con estado inválido')
                for doc in invalid_state_docs:
                    try:
                        doc.write({
                            'state': 'invoice_sent_failed',  # Estado genérico para retry
                        })
                        add_output(f'✅ Corregido documento ID: {doc.id} (Corregido state)')
                    except Exception as e:
                        add_output(f'❌ Error al corregir documento ID {doc.id}: {str(e)}')
            else:
                add_output('No se encontraron documentos con estado inválido')
        
        add_output('\n========= FIN REPARACIÓN DOCUMENTOS EDI =========')
        
        # Si hay factura, guardar en su chatter
        result_text = '\n'.join(output)
        if invoice:
            invoice.message_post(
                body=f"<pre>{result_text}</pre>",
                subject="Reparación Documentos EDI (AS)",
                message_type='comment',
                subtype_xmlid='mail.mt_note',
                body_is_html=True
            )
        
        return result_text 