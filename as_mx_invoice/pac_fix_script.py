#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Script para corregir PAC faltante y timbrar factura
# Usar con: python3 odoo-bin shell -d BASE_DE_DATOS < pac_fix_script.py

# Variables de configuración - CAMBIAR SEGÚN SEA NECESARIO
FACTURA_NUMERO = "ESCUE/2025/00002"  # Número de factura de la captura
COMPANY_NAME = "ESCUELA KEMPER URGATE"  # Nombre de la compañía

# Configuración del PAC
PAC_VALUES = {
    'l10n_mx_edi_pac': 'finkok',  # Opciones: 'finkok', 'solfact', 'sw'
    'l10n_mx_edi_pac_test_env': True,  # True para pruebas, False para producción
    'l10n_mx_edi_pac_username': 'usuario@test.com',  # Reemplazar por real
    'l10n_mx_edi_pac_password': 'password_test',  # Reemplazar por real
}

print("\n====== SCRIPT DE CORRECCIÓN PAC Y TIMBRADO ======")

# Buscar la factura por número
invoice = env['account.move'].search([('name', '=', FACTURA_NUMERO)], limit=1)

if not invoice:
    print(f"ERROR: No se encontró la factura con número {FACTURA_NUMERO}")
    # Intentamos buscar la compañía directamente
    company = env['res.company'].search([('name', 'ilike', COMPANY_NAME)], limit=1)
    if not company:
        print(f"ERROR: No se encontró la compañía con nombre similar a '{COMPANY_NAME}'")
        print("Buscando todas las compañías...")
        companies = env['res.company'].search([])
        print(f"Compañías disponibles: {len(companies)}")
        for comp in companies:
            print(f"- ID: {comp.id} | Nombre: {comp.name}")
        exit()
else:
    print(f"Factura encontrada: {invoice.name} (ID: {invoice.id})")
    print(f"Fecha: {invoice.invoice_date} | Estado: {invoice.state}")
    company = invoice.company_id
    print(f"Compañía de la factura: {company.name} (ID: {company.id})")

# Guardar configuración anterior para comparar
old_values = {
    'pac': getattr(company, 'l10n_mx_edi_pac', 'No configurado'),
    'test_env': getattr(company, 'l10n_mx_edi_pac_test_env', 'No configurado'),
    'username': getattr(company, 'l10n_mx_edi_pac_username', 'No configurado'),
    'password': 'Configurado' if getattr(company, 'l10n_mx_edi_pac_password', False) else 'No configurado'
}

print("\n--- VALORES PAC ACTUALES ---")
print(f"- PAC: {old_values['pac']}")
print(f"- Modo Pruebas: {old_values['test_env']}")
print(f"- Usuario: {old_values['username']}")
print(f"- Contraseña: {old_values['password']}")

# Actualizar configuración
try:
    company.write({
        'l10n_mx_edi_pac': PAC_VALUES.get('l10n_mx_edi_pac', 'finkok'),
        'l10n_mx_edi_pac_test_env': PAC_VALUES.get('l10n_mx_edi_pac_test_env', True),
        'l10n_mx_edi_pac_username': PAC_VALUES.get('l10n_mx_edi_pac_username', ''),
        'l10n_mx_edi_pac_password': PAC_VALUES.get('l10n_mx_edi_pac_password', '')
    })
    print("\n¡CONFIGURACIÓN PAC ACTUALIZADA CORRECTAMENTE!")
    
    # Verificar la nueva configuración
    new_values = {
        'pac': getattr(company, 'l10n_mx_edi_pac', 'No configurado'),
        'test_env': getattr(company, 'l10n_mx_edi_pac_test_env', 'No configurado'),
        'username': getattr(company, 'l10n_mx_edi_pac_username', 'No configurado'),
        'password': 'Configurado' if getattr(company, 'l10n_mx_edi_pac_password', False) else 'No configurado'
    }
    
    print("\n--- NUEVOS VALORES PAC ---")
    print(f"- PAC: {new_values['pac']}")
    print(f"- Modo Pruebas: {new_values['test_env']}")
    print(f"- Usuario: {new_values['username']}")
    print(f"- Contraseña: {new_values['password']}")
    
    # También agregar mensaje en el chatter si hay factura
    if invoice:
        message = f"""
<b>CONFIGURACIÓN PAC ACTUALIZADA (Script AS)</b>
<pre>
VALORES ANTERIORES:
- PAC: {old_values['pac']}
- Modo Pruebas: {old_values['test_env']}
- Usuario: {old_values['username']}
- Contraseña: {old_values['password']}

NUEVOS VALORES:
- PAC: {new_values['pac']}
- Modo Pruebas: {new_values['test_env']}
- Usuario: {new_values['username']}
- Contraseña: {new_values['password']}
</pre>
"""
        invoice.message_post(body=message, subject="PAC Configurado", message_type='comment', subtype_xmlid='mail.mt_note', body_is_html=True)
        print("Mensaje agregado al chatter de la factura")
    
except Exception as e:
    print(f"ERROR al actualizar la configuración PAC: {e}")
    exit()

# Si hay factura, intentar timbrado manual
if invoice:
    print("\n=== INTENTANDO TIMBRADO MANUAL ===")
    try:
        print("Llamando a la función _l10n_mx_edi_cfdi_invoice_try_send...")
        result = invoice._l10n_mx_edi_cfdi_invoice_try_send()
        
        if result:
            if 'document' in result:
                print(f"¡ÉXITO! Se generó documento EDI ID: {result['document'].id}")
                print(f"Estado: {result['document'].state}")
                if result['document'].message:
                    print(f"Mensaje: {result['document'].message}")
                    
                # Añadir el resultado al chatter
                message = f"""
<b>RESULTADO TIMBRADO MANUAL (Script AS)</b>
<pre>
Documento EDI ID: {result['document'].id}
Estado: {result['document'].state}
Mensaje: {result['document'].message if result['document'].message else 'Sin mensaje'}
</pre>
"""
                invoice.message_post(body=message, subject="Resultado Timbrado Manual", message_type='comment', subtype_xmlid='mail.mt_note', body_is_html=True)
                
            elif 'error' in result:
                print(f"ERROR: {result['error']}")
                # Añadir el error al chatter
                message = f"""
<b>ERROR EN TIMBRADO MANUAL (Script AS)</b>
<pre>
{result['error']}
</pre>
"""
                invoice.message_post(body=message, subject="Error en Timbrado Manual", message_type='comment', subtype_xmlid='mail.mt_note', body_is_html=True)
            else:
                print(f"RESULTADO DESCONOCIDO: {result}")
                # Añadir el resultado al chatter
                invoice.message_post(body=f"<pre>Resultado desconocido: {result}</pre>", subject="Resultado Timbrado Manual", message_type='comment', subtype_xmlid='mail.mt_note', body_is_html=True)
        else:
            print("La función no retornó ningún resultado.")
            invoice.message_post(body="<pre>La función de timbrado no retornó ningún resultado.</pre>", subject="Sin Resultado en Timbrado", message_type='comment', subtype_xmlid='mail.mt_note', body_is_html=True)
            
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"EXCEPCIÓN durante timbrado manual: {e}")
        print(f"Traceback completo:\n{error_traceback}")
        
        # Añadir el error al chatter
        message = f"""
<b>EXCEPCIÓN EN TIMBRADO MANUAL (Script AS)</b>
<pre>
{e}

Traceback:
{error_traceback}
</pre>
"""
        invoice.message_post(body=message, subject="Excepción en Timbrado Manual", message_type='comment', subtype_xmlid='mail.mt_note', body_is_html=True)

print("\n¡SCRIPT COMPLETADO!") 