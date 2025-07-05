#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar el estado del módulo as_mx_invoice

Ejecutar desde shell de Odoo:
> exec(open('CHECK_MODULE_STATUS.py').read())
"""

def check_module_status():
    """
    Propósito: Verifica el estado del módulo as_mx_invoice
    """
    print("🔍 Verificando estado del módulo as_mx_invoice...")
    
    try:
        # Verificar si el módulo está instalado
        module = env['ir.module.module'].search([('name', '=', 'as_mx_invoice')])
        
        if module:
            print(f"✅ Módulo encontrado:")
            print(f"   - ID: {module.id}")
            print(f"   - Estado: {module.state}")
            print(f"   - Versión: {module.latest_version}")
            print(f"   - Instalable: {module.installable}")
            print(f"   - Auto-install: {module.auto_install}")
            
            if module.state == 'installed':
                print("✅ El módulo está INSTALADO")
                
                # Verificar si nuestras clases están disponibles
                print("\n🔧 Verificando herencias...")
                
                # Test account.payment
                payment_model = env['account.payment']
                if hasattr(payment_model, '_as_payment_force_log'):
                    print("✅ AsMxAccountPayment - Método _as_payment_force_log encontrado")
                else:
                    print("❌ AsMxAccountPayment - Método _as_payment_force_log NO encontrado")
                
                # Test l10n_mx_edi.document
                edi_model = env['l10n_mx_edi.document']
                if hasattr(edi_model, '_as_force_cfdi_log'):
                    print("✅ AsMxEdiDocument - Método _as_force_cfdi_log encontrado")
                else:
                    print("❌ AsMxEdiDocument - Método _as_force_cfdi_log NO encontrado")
                
                # Test account.move
                move_model = env['account.move']
                if hasattr(move_model, '_as_payment_force_log'):
                    print("✅ AsMxAccountMove - Método _as_payment_force_log encontrado")
                else:
                    print("❌ AsMxAccountMove - Método _as_payment_force_log NO encontrado")
                    
            elif module.state == 'uninstalled':
                print("⚠️ El módulo NO está instalado")
                print("💡 Para instalarlo:")
                print("   1. Ir a Apps")
                print("   2. Buscar 'as_mx_invoice'")
                print("   3. Hacer clic en 'Install'")
                
            elif module.state == 'to upgrade':
                print("🔄 El módulo necesita actualización")
                print("💡 Para actualizarlo:")
                print("   1. Ir a Apps")
                print("   2. Buscar 'as_mx_invoice'")
                print("   3. Hacer clic en 'Upgrade'")
                
        else:
            print("❌ Módulo as_mx_invoice NO encontrado")
            print("💡 Verificar:")
            print("   1. Que el módulo esté en el addons-path")
            print("   2. Que el __manifest__.py sea válido")
            print("   3. Reiniciar Odoo con --update=all")
        
        # Verificar dependencias
        print("\n📦 Verificando dependencias...")
        l10n_mx_edi = env['ir.module.module'].search([('name', '=', 'l10n_mx_edi')])
        if l10n_mx_edi and l10n_mx_edi.state == 'installed':
            print("✅ l10n_mx_edi está instalado")
        else:
            print("❌ l10n_mx_edi NO está instalado o disponible")
            
        account = env['ir.module.module'].search([('name', '=', 'account')])
        if account and account.state == 'installed':
            print("✅ account está instalado")
        else:
            print("❌ account NO está instalado")
        
        # Buscar pagos para probar
        print("\n💰 Buscando pagos para probar Force CFDI...")
        payments = env['account.payment'].search([
            ('state', '=', 'posted'),
            ('l10n_mx_edi_force_pue_payment_needed', '=', True)
        ], limit=3)
        
        if payments:
            print(f"✅ Encontrados {len(payments)} pagos con Force CFDI disponible:")
            for payment in payments:
                print(f"   - {payment.name} (ID: {payment.id}) - {payment.amount} {payment.currency_id.name}")
        else:
            print("⚠️ No se encontraron pagos con Force CFDI disponible")
            
            # Buscar cualquier pago
            any_payments = env['account.payment'].search([('state', '=', 'posted')], limit=3)
            if any_payments:
                print(f"ℹ️ Pagos disponibles para prueba:")
                for payment in any_payments:
                    print(f"   - {payment.name} (ID: {payment.id}) - Force needed: {payment.l10n_mx_edi_force_pue_payment_needed}")
        
        print("\n🎯 RESUMEN:")
        if module and module.state == 'installed':
            print("✅ Módulo instalado correctamente")
            print("🔧 Para probar Force CFDI:")
            print("   1. Ir a un pago con l10n_mx_edi_force_pue_payment_needed = True")
            print("   2. Hacer clic en 'Force CFDI'")
            print("   3. Revisar logs y chatter")
        else:
            print("❌ Módulo necesita instalación/actualización")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

# Ejecutar si estamos en shell de Odoo
if __name__ == "__main__":
    print("⚠️ Este script debe ejecutarse desde el shell de Odoo")
else:
    check_module_status() 