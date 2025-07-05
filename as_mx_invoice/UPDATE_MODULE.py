#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar el módulo as_mx_invoice

Ejecutar desde shell de Odoo:
> exec(open('UPDATE_MODULE.py').read())
"""

def update_module():
    """
    Propósito: Actualiza el módulo as_mx_invoice
    """
    print("🔄 Actualizando módulo as_mx_invoice...")
    
    try:
        # Buscar el módulo
        module = env['ir.module.module'].search([('name', '=', 'as_mx_invoice')])
        
        if not module:
            print("❌ Módulo as_mx_invoice no encontrado")
            print("💡 Primero debe instalarse el módulo")
            return
        
        print(f"📦 Módulo encontrado - Estado actual: {module.state}")
        
        if module.state == 'uninstalled':
            print("🔧 Instalando módulo...")
            module.button_immediate_install()
            print("✅ Módulo instalado")
            
        elif module.state in ('installed', 'to upgrade'):
            print("🔄 Actualizando módulo...")
            module.button_immediate_upgrade()
            print("✅ Módulo actualizado")
            
        else:
            print(f"⚠️ Estado del módulo: {module.state}")
            print("💡 Intentando forzar actualización...")
            module.button_immediate_upgrade()
        
        # Verificar el resultado
        module.refresh()
        print(f"🎯 Estado final del módulo: {module.state}")
        
        if module.state == 'installed':
            print("✅ ¡Módulo actualizado exitosamente!")
            print("\n🔧 Verificando herencias...")
            
            # Test rápido de las herencias
            try:
                payment_model = env['account.payment']
                if hasattr(payment_model, '_as_payment_force_log'):
                    print("✅ AsMxAccountPayment cargado correctamente")
                else:
                    print("❌ AsMxAccountPayment NO cargado")
                
                edi_model = env['l10n_mx_edi.document']
                if hasattr(edi_model, '_as_force_cfdi_log'):
                    print("✅ AsMxEdiDocument cargado correctamente")
                else:
                    print("❌ AsMxEdiDocument NO cargado")
                    
                move_model = env['account.move']
                if hasattr(move_model, '_as_payment_force_log'):
                    print("✅ AsMxAccountMove cargado correctamente")
                else:
                    print("❌ AsMxAccountMove NO cargado")
                    
            except Exception as test_error:
                print(f"⚠️ Error verificando herencias: {test_error}")
        else:
            print(f"❌ Error en la actualización. Estado: {module.state}")
            
    except Exception as e:
        print(f"\n❌ ERROR durante la actualización: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

# Ejecutar si estamos en shell de Odoo
if __name__ == "__main__":
    print("⚠️ Este script debe ejecutarse desde el shell de Odoo")
else:
    update_module() 