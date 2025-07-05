#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la herencia de Force CFDI

Ejecutar desde terminal de Odoo:
> python3 TEST_FORCE_CFDI.py

O desde shell de Odoo:
> exec(open('TEST_FORCE_CFDI.py').read())
"""

def test_force_cfdi_inheritance():
    """
    Propósito: Verifica que las funciones Force CFDI estén correctamente heredadas
    """
    print("🔥 Testing Force CFDI Inheritance...")
    
    try:
        # Test 1: Verificar que el modelo AsMxEdiDocument existe
        print("\n1️⃣ Verificando modelo AsMxEdiDocument...")
        edi_model = env['l10n_mx_edi.document']
        print(f"   ✅ Modelo encontrado: {edi_model}")
        
        # Verificar que tiene nuestro método de logging
        if hasattr(edi_model, '_as_force_cfdi_log'):
            print("   ✅ Método _as_force_cfdi_log encontrado")
        else:
            print("   ❌ Método _as_force_cfdi_log NO encontrado")
            
        # Test 2: Verificar que el modelo AsMxAccountMove existe  
        print("\n2️⃣ Verificando modelo AsMxAccountMove...")
        move_model = env['account.move']
        print(f"   ✅ Modelo encontrado: {move_model}")
        
        # Verificar que tiene nuestro método de logging
        if hasattr(move_model, '_as_payment_force_log'):
            print("   ✅ Método _as_payment_force_log encontrado")
        else:
            print("   ❌ Método _as_payment_force_log NO encontrado")
            
        # Test 3: Verificar que action_force_payment_cfdi existe
        print("\n3️⃣ Verificando método action_force_payment_cfdi...")
        if hasattr(edi_model, 'action_force_payment_cfdi'):
            print("   ✅ Método action_force_payment_cfdi encontrado")
        else:
            print("   ❌ Método action_force_payment_cfdi NO encontrado")
            
        # Test 4: Verificar que l10n_mx_edi_cfdi_payment_force_try_send existe
        print("\n4️⃣ Verificando método l10n_mx_edi_cfdi_payment_force_try_send...")
        if hasattr(move_model, 'l10n_mx_edi_cfdi_payment_force_try_send'):
            print("   ✅ Método l10n_mx_edi_cfdi_payment_force_try_send encontrado")
        else:
            print("   ❌ Método l10n_mx_edi_cfdi_payment_force_try_send NO encontrado")
            
        # Test 5: Buscar documentos PUE existentes
        print("\n5️⃣ Buscando documentos PUE para prueba...")
        pue_docs = env['l10n_mx_edi.document'].search([
            ('state', '=', 'payment_sent_pue')
        ], limit=5)
        
        if pue_docs:
            print(f"   ✅ Encontrados {len(pue_docs)} documentos PUE")
            for doc in pue_docs:
                print(f"     - Doc {doc.id}: {doc.move_id.name if doc.move_id else 'Sin move'}")
        else:
            print("   ⚠️ No se encontraron documentos PUE para prueba")
            
        # Test 6: Verificar dependencias del módulo
        print("\n6️⃣ Verificando dependencias del módulo...")
        try:
            module = env['ir.module.module'].search([('name', '=', 'as_mx_invoice')])
            if module:
                print(f"   ✅ Módulo as_mx_invoice encontrado - Estado: {module.state}")
                
                # Verificar l10n_mx_edi
                l10n_module = env['ir.module.module'].search([('name', '=', 'l10n_mx_edi')])
                if l10n_module:
                    print(f"   ✅ Módulo l10n_mx_edi encontrado - Estado: {l10n_module.state}")
                else:
                    print("   ❌ Módulo l10n_mx_edi NO encontrado")
            else:
                print("   ❌ Módulo as_mx_invoice NO encontrado")
        except Exception as e:
            print(f"   ⚠️ Error verificando módulos: {e}")
        
        print("\n🎯 RESUMEN DEL TEST:")
        print("✅ Si todos los puntos anteriores muestran ✅, la herencia está funcionando correctamente")
        print("❌ Si algún punto muestra ❌, revisar la instalación del módulo")
        print("⚠️ Si hay advertencias, verificar configuración")
        
        print("\n🔧 Para probar Force CFDI en producción:")
        print("1. Buscar un pago con estado 'payment_sent_pue'")
        print("2. Ir a la pestaña CFDI del pago")
        print("3. Hacer clic en el botón 'Force CFDI'")
        print("4. Revisar logs en /var/log/odoo/ con grep 'AS_FORCE_CFDI'")
        print("5. Verificar mensajes en el chatter del pago")
        
    except Exception as e:
        print(f"\n❌ ERROR durante el test: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
    print("\n🔥 Test completado!")

# Ejecutar el test si estamos en shell de Odoo
if __name__ == "__main__":
    print("⚠️ Este script debe ejecutarse desde el shell de Odoo")
    print("Ejemplo: odoo shell -d tu_base_datos --addons-path=... -c tu_config.conf")
    print("Luego ejecutar: exec(open('TEST_FORCE_CFDI.py').read())")
else:
    # Estamos en shell de Odoo, ejecutar el test
    test_force_cfdi_inheritance() 