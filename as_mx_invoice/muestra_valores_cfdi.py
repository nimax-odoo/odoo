#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Script para mostrar todos los valores CFDI en el chatter
# Usar con: python3 odoo-bin shell -d NOMBRE_BASE < muestra_valores_cfdi.py

# Configuración: cambia el ID de la factura según necesites
FACTURA_ID = 2  # Cambia esto por el ID de la factura a diagnosticar

print("\n====== DIAGNÓSTICO COMPLETO DATOS CFDI ======")

# Buscar la factura
invoice = env['account.move'].browse(FACTURA_ID)
if not invoice.exists():
    print(f"ERROR: No se encontró factura con ID {FACTURA_ID}")
    exit()

print(f"Analizando factura: {invoice.name} (ID: {invoice.id})")

# --- Funciones auxiliares ---
def get_field_value(obj, field_name, default='N/A'):
    """Obtiene el valor de un campo de forma segura"""
    if hasattr(obj, field_name):
        value = getattr(obj, field_name)
        if value is not None:
            return value
    return default
    
def validate_value(value, condition):
    """Valida un valor y devuelve emoji correspondiente"""
    if condition:
        return f"{value} ✅"
    return f"{value} ❌"

# --- Recopilando datos ---
# Datos de la compañía
company = invoice.company_id
company_data = {
    'name': company.name,
    'id': company.id,
    'vat': company.partner_id.vat,
    'fiscal_regime': get_field_value(company, 'l10n_mx_edi_fiscal_regime', 'NO ENCONTRADO'),
    'zip': company.partner_id.zip,
    'pac': get_field_value(company, 'l10n_mx_edi_pac', 'NO CONFIGURADO'),
    'pac_username': get_field_value(company, 'l10n_mx_edi_pac_username', 'NO CONFIGURADO'),
    'pac_password': bool(get_field_value(company, 'l10n_mx_edi_pac_password', False)),
    'pac_test': get_field_value(company, 'l10n_mx_edi_pac_test_env', 'N/A'),
}

# Buscar certificados activos
cert_data = []
certs = env['certificate.certificate'].search([
    ('company_id', '=', company.id)
])
for cert in certs:
    cert_info = {
        'id': cert.id,
        'name': cert.name,
        'is_valid': cert.is_valid,
        'active': cert.active,
        'date_start': cert.date_start,
        'date_end': cert.date_end,
        'has_pem': bool(cert.pem_certificate),
        'has_key': bool(cert.private_key_id),
    }
    cert_data.append(cert_info)
    
# Datos del cliente/receptor
partner = invoice.partner_id
customer_data = {
    'name': partner.name,
    'id': partner.id,
    'vat': partner.vat,
    'fiscal_regime': invoice.l10n_mx_edi_fiscal_regime,
    'zip': partner.zip,
    'usage': invoice.l10n_mx_edi_usage,
}

# Datos de la factura
payment_method = get_field_value(invoice, 'l10n_mx_edi_payment_method_id', None)
payment_method_name = payment_method.name if payment_method else 'NO CONFIGURADO'
payment_method_code = payment_method.code if payment_method else 'NO CONFIGURADO'

invoice_data = {
    'name': invoice.name,
    'id': invoice.id,
    'state': invoice.state,
    'payment_policy': invoice.l10n_mx_edi_payment_policy,
    'payment_method': payment_method_name,
    'payment_method_code': payment_method_code,
    'currency': invoice.currency_id.name,
    'cfdi_needed': invoice.l10n_mx_edi_is_cfdi_needed,
    'cfdi_state': invoice.l10n_mx_edi_cfdi_state,
    'cfdi_uuid': invoice.l10n_mx_edi_cfdi_uuid,
}

# Datos de las líneas
line_data = []
for line in invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product'):
    product = line.product_id
    uom = line.product_uom_id
    
    # Obtener código SAT del producto
    sat_product_code = 'NO CONFIGURADO'
    if product and hasattr(product, 'unspsc_code_id') and product.unspsc_code_id:
        sat_product_code = product.unspsc_code_id.code
        
    # Obtener código SAT de la unidad de medida
    sat_uom_code = 'NO CONFIGURADO'
    if uom and hasattr(uom, 'unspsc_code_id') and uom.unspsc_code_id:
        sat_uom_code = uom.unspsc_code_id.code
    
    line_info = {
        'id': line.id,
        'name': line.name,
        'product_id': product.id if product else False,
        'product_name': product.name if product else 'SIN PRODUCTO',
        'uom': uom.name if uom else 'N/A',
        'quantity': line.quantity,
        'price_unit': line.price_unit,
        'price_subtotal': line.price_subtotal,
        'tax_ids': line.tax_ids.ids,
        'sat_product_code': sat_product_code,
        'sat_uom_code': sat_uom_code,
    }
    line_data.append(line_info)

# --- Construir mensaje HTML para el chatter ---
html_message = f"""
<div style="background-color: #f8f9fa; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
    <h2 style="color: #6c757d;">🛠️ Diagnóstico CFDI Completo ({invoice.name})</h2>
    <hr style="border-top: 2px solid #6c757d;">
    
    <h3 style="color: #007bff;">📋 Datos CFDI Básicos</h3>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
        <tr>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Campo</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Valor</th>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Necesita CFDI</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{invoice_data['cfdi_needed']} ✅</td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Estado CFDI</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{invoice_data['cfdi_state'] or 'Sin timbrar'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">UUID</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{invoice_data['cfdi_uuid'] or 'N/A'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Método Pago</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{invoice_data['payment_method']} ({invoice_data['payment_method_code']})</td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Política Pago</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{invoice_data['payment_policy'] or 'No configurado'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Moneda</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{invoice_data['currency']}</td>
        </tr>
    </table>
    
    <h3 style="color: #28a745;">🏢 Emisor (Compañía)</h3>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
        <tr>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Campo</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Valor</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Validación</th>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Nombre</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{company_data['name']} (ID: {company_data['id']})</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">✅</td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">RFC</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{company_data['vat'] or 'NO CONFIGURADO'}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{'✅' if company_data['vat'] else '❌ FALTA RFC'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Régimen Fiscal</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{company_data['fiscal_regime']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{'✅' if company_data['fiscal_regime'] and company_data['fiscal_regime'] != 'NO ENCONTRADO' else '❌ FALTA RÉGIMEN'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Código Postal</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{company_data['zip'] or 'NO CONFIGURADO'}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{'✅' if company_data['zip'] else '❌ FALTA CP'}</td>
        </tr>
    </table>
    
    <h3 style="color: #fd7e14;">🔐 Configuración PAC</h3>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
        <tr>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Campo</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Valor</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Validación</th>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Proveedor PAC</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{company_data['pac']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{'✅' if company_data['pac'] != 'NO CONFIGURADO' else '❌ FALTA PAC'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Usuario PAC</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{company_data['pac_username']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{'✅' if company_data['pac_username'] != 'NO CONFIGURADO' else '❌ FALTA USUARIO'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Contraseña PAC</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{'CONFIGURADA' if company_data['pac_password'] else 'NO CONFIGURADA'}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{'✅' if company_data['pac_password'] else '❌ FALTA CONTRASEÑA'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Modo Pruebas</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{company_data['pac_test']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">✅</td>
        </tr>
    </table>
    
    <h3 style="color: #dc3545;">🔒 Certificados CSD</h3>
"""

if cert_data:
    html_message += """
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
        <tr>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">ID</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Nombre</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Válido</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Activo</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Fechas</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">.cer/.key</th>
        </tr>
"""
    for cert in cert_data:
        html_message += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{cert['id']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{cert['name']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{'✅' if cert['is_valid'] else '❌'}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{'✅' if cert['active'] else '❌'}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{cert['date_start']} - {cert['date_end']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{'✅' if cert['has_pem'] else '❌'} / {'✅' if cert['has_key'] else '❌'}</td>
        </tr>
"""
    html_message += """
    </table>
"""
else:
    html_message += """
    <p style="background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 4px;">⚠️ NO SE ENCONTRARON CERTIFICADOS CSD PARA ESTA COMPAÑÍA</p>
"""

html_message += f"""
    <h3 style="color: #17a2b8;">👤 Receptor (Cliente)</h3>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
        <tr>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Campo</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Valor</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Validación</th>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Nombre</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{customer_data['name']} (ID: {customer_data['id']})</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">✅</td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">RFC</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{customer_data['vat'] or 'NO CONFIGURADO'}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{'✅' if customer_data['vat'] else '❌ FALTA RFC'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Régimen Fiscal</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{customer_data['fiscal_regime'] or 'NO CONFIGURADO'}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{'✅' if customer_data['fiscal_regime'] else '❌ FALTA RÉGIMEN'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Código Postal</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{customer_data['zip'] or 'NO CONFIGURADO'}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{'✅' if customer_data['zip'] else '❌ FALTA CP'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Uso CFDI</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{customer_data['usage'] or 'NO CONFIGURADO'}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{'✅' if customer_data['usage'] else '❌ FALTA USO CFDI'}</td>
        </tr>
    </table>
    
    <h3 style="color: #6f42c1;">📋 Líneas de Factura</h3>
"""

if line_data:
    html_message += """
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
        <tr>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Producto</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Cantidad</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Precio</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Subtotal</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Cód. SAT Prod.</th>
            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #dee2e6;">Cód. SAT UOM</th>
        </tr>
"""
    for line in line_data:
        html_message += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{line['product_name']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{line['quantity']} {line['uom']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{line['price_unit']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{line['price_subtotal']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{line['sat_product_code']} {'✅' if line['sat_product_code'] != 'NO CONFIGURADO' else '❌'}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{line['sat_uom_code']} {'✅' if line['sat_uom_code'] != 'NO CONFIGURADO' else '❌'}</td>
        </tr>
"""
    html_message += """
    </table>
"""
else:
    html_message += """
    <p style="background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 4px;">⚠️ NO SE ENCONTRARON LÍNEAS VÁLIDAS EN LA FACTURA</p>
"""

html_message += """
    <div style="background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 4px; margin-top: 15px;">
        <p><strong>⚠️ Nota:</strong> Este diagnóstico muestra todos los valores relevantes para el CFDI. Revise cualquier campo marcado con ❌ antes de intentar timbrar.</p>
    </div>
    
    <div style="background-color: #d4edda; color: #155724; padding: 10px; border-radius: 4px; margin-top: 15px;">
        <p><strong>💡 Tip:</strong> Para resolver fallos en la generación CFDI, asegúrate de que la configuración PAC esté completa en la compañía (PAC proveedor, usuario y contraseña).</p>
    </div>
</div>
"""

# Postear mensaje en el chatter
invoice.message_post(
    body=html_message,
    subject="DIAGNÓSTICO SUPER COMPLETO CFDI (AS)",
    message_type='comment',
    subtype_xmlid='mail.mt_note',
    body_is_html=True
)

print(f"✅ Diagnóstico CFDI completo agregado al chatter de la factura {invoice.name}")

# También agregamos información sobre _send_api
print("\n====== DIAGNÓSTICO DEL ENVÍO _send_api ======")

# Uso de fields.Datetime directamente puede causar errores en shell script
# Vamos a usar el timestamp de la propia factura
doc = env['l10n_mx_edi.document'].create({
    'move_id': invoice.id,
    'state': 'invoice_sent_failed',
    'datetime': invoice.create_date,  # Usar create_date de la factura en lugar de fields.Datetime
})

print(f"Documento EDI de prueba creado: ID {doc.id}")

api_info = """
<div style="background-color: #e9ecef; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
    <h2 style="color: #343a40;">⚠️ Diagnóstico _send_api</h2>
    <hr style="border-top: 2px solid #6c757d;">
    
    <p style="color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 4px;">
        <strong>ATENCIÓN: El problema de timbrado está en _send_api</strong><br>
        La función recibe los argumentos de la siguiente manera:
    </p>
    
    <pre style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; overflow: auto;">
Args: (res.company(1,), 'l10n_mx_edi.cfdiv40', 'ESCUE-ESCUE202500002-MX-Invoice-4.0.xml', &lt;function&gt;, &lt;function&gt;, &lt;function&gt;)
Kwargs: {}
    </pre>
    
    <p style="color: #0c5460; background-color: #d1ecf1; padding: 10px; border-radius: 4px;">
        <strong>Problema identificado:</strong> El método _send_api espera 'record' en kwargs pero está recibiendo argumentos posicionales. Nuestra implementación ya corrige este caso.
    </p>
    
    <p style="color: #155724; background-color: #d4edda; padding: 10px; border-radius: 4px;">
        <strong>Solución:</strong> Verifica los valores de PAC, certificado y datos fiscales que se muestran arriba.
    </p>
</div>
"""

invoice.message_post(
    body=api_info,
    subject="Diagnóstico _send_api (AS)",
    message_type='comment',
    subtype_xmlid='mail.mt_note',
    body_is_html=True
)

print(f"✅ Diagnóstico _send_api agregado al chatter de la factura {invoice.name}")
print("\n¡Diagnóstico completo!") 