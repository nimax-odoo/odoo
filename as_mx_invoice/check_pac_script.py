#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Script para diagnosticar la configuración de PAC/Certificados
# Uso: python3 odoo-bin shell -d NOMBRE_BASE < check_pac_script.py

# Configuración: cambia el ID de la factura según necesites
FACTURA_ID = 2  # Cambia esto por el ID de la factura a diagnosticar

print("\n====== DIAGNÓSTICO DE CONFIGURACIÓN PAC Y CERTIFICADOS ======")

# Buscar la factura
invoice = env['account.move'].browse(FACTURA_ID)
if not invoice.exists():
    print(f"ERROR: No se encontró factura con ID {FACTURA_ID}")
    exit()

print(f"Analizando factura: {invoice.name} (ID: {invoice.id})")

# Implementación simplificada del método action_check_pac_config
output = []

def add_output(text):
    print(text)
    output.append(text)

add_output('\n====== VERIFICACIÓN DATOS PAC Y CERTIFICADOS (AS) ======')
add_output(f'Factura analizada: {invoice.name} (ID: {invoice.id})')

# --- Mostrar datos de las compañías mexicanas ---
company = invoice.company_id
add_output(f'\n-- DETALLES DE LA COMPAÑÍA DE LA FACTURA --')

add_output(f'\nID: {company.id} | Nombre: {company.name}')
add_output(f'RFC: {company.partner_id.vat}')

# Datos PAC
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
certs = env['certificate.certificate'].search([('company_id', '=', company.id)])
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
    
# Certificados antiguos
add_output('\n---- Certificados antiguos (l10n_mx_edi.certificate):')
old_certs = env['l10n_mx_edi.certificate'].search([('company_id', '=', company.id)])
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
edi_docs = env['l10n_mx_edi.document'].search([('move_id', '=', invoice.id)], limit=1)
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
valid_cert = env['certificate.certificate'].search_count([
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

# Verificar si la factura tiene documento EDI
edi_docs = env['l10n_mx_edi.document'].search([('move_id', '=', invoice.id)])
if not edi_docs:
    add_output('\n==== CREANDO DOCUMENTO EDI DE PRUEBA =====')
    # Crear un documento EDI para probar
    try:
        edi_doc = env['l10n_mx_edi.document'].create({
            'move_id': invoice.id,
            'state': 'invoice_sent_failed',
            'datetime': invoice.create_date,
        })
        add_output(f'✅ Documento EDI creado con ID: {edi_doc.id}')
        add_output('Ahora puedes intentar el timbrado manual desde la interfaz.')
    except Exception as e:
        add_output(f'❌ Error al crear documento EDI: {str(e)}')

# Mostrar resultado en el chatter también
result_text = '\n'.join(output)
invoice.message_post(
    body=f"<pre>{result_text}</pre>",
    subject="Verificación de PAC y Certificados (AS)",
    message_type='comment',
    subtype_xmlid='mail.mt_note',
    body_is_html=True
)

print("\n✅ Diagnóstico completo y agregado al chatter!") 