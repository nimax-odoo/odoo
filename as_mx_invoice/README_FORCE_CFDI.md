# 🔥 Force CFDI Debug - Instrucciones de Uso

## 📋 Resumen

Se implementó la herencia completa de la funcionalidad "Force CFDI" con debugging avanzado y logging completo. **El problema era que los logs deben aparecer en `account.payment`, no en `account.move`**.

## ⚡ Solución Implementada

### **Problema Identificado:**
- Los pagos en Odoo 18 usan el modelo `account.payment`
- El método `l10n_mx_edi_cfdi_payment_force_try_send()` en `account.payment` delega a `account.move`
- Los logs y chatter deben estar en el payment, no en el move

### **Solución:**
- ✅ Herencia de `account.payment` con logging completo
- ✅ Herencia de `l10n_mx_edi.document` para documentos CFDI
- ✅ Herencia de `account.move` como respaldo
- ✅ Chatter automático en el payment correcto
- ✅ IDs únicos de traza para seguimiento

## 🚀 Instalación Inmediata

### **Paso 1: Verificar archivos**
```bash
cd /opt.cata/bb/odoo18_enterprise_clientes/nimax/as_mx_invoice
./INSTALL_FORCE_CFDI.sh
```

### **Paso 2: Actualizar módulo**
**Opción A - Desde Odoo UI:**
1. Ir a **Apps**
2. Buscar `as_mx_invoice`
3. Hacer clic en **Upgrade**

**Opción B - Desde shell de Odoo:**
```python
exec(open('UPDATE_MODULE.py').read())
```

### **Paso 3: Verificar instalación**
```python
exec(open('CHECK_MODULE_STATUS.py').read())
```

## 🔍 Uso y Testing

### **Encontrar un pago para probar:**
1. Ir a **Contabilidad** → **Pagos**
2. Buscar un pago con estado **Publicado**
3. Abrir el pago
4. Ir a la pestaña **CFDI**
5. Buscar el botón **Force CFDI**

### **Ejecutar Force CFDI:**
1. Hacer clic en **Force CFDI**
2. **Los logs aparecerán en el chatter del payment** 🔥
3. Verificar logs en tiempo real:
```bash
tail -f /var/log/odoo/odoo18e.nimax.log | grep "AS_PAYMENT_FORCE\|AS_FORCE_CFDI"
```

## 📧 Mensajes en Chatter

Los mensajes aparecen automáticamente en el chatter del payment con iconos:
- 🔥 **Inicio del proceso**
- ℹ️ **Información general**
- ⚠️ **Advertencias**
- ✅ **Éxito con UUID**
- ❌ **Errores detallados**

## 🔧 Debugging

### **Logs en tiempo real:**
```bash
# Ver todos los logs de Force CFDI
tail -f /var/log/odoo/odoo18e.nimax.log | grep "AS_PAYMENT_FORCE\|AS_FORCE_CFDI"

# Ver logs específicos de un payment
tail -f /var/log/odoo/odoo18e.nimax.log | grep "PAYMENT-FORCE-123-"
```

### **Verificar herencias:**
```python
# En shell de Odoo
payment = env['account.payment'].browse(PAYMENT_ID)
hasattr(payment, '_as_payment_force_log')  # Debe ser True
hasattr(payment, 'l10n_mx_edi_cfdi_payment_force_try_send')  # Debe ser True
```

## 🚨 Troubleshooting

### **No aparecen logs:**
```bash
python3 CHECK_MODULE_STATUS.py
python3 UPDATE_MODULE.py
```

### **CFDI vacío en payment:**
- ✅ **SOLUCIONADO**: Los logs ahora aparecen en `account.payment`
- Verificar el chatter del payment directamente
- Los mensajes aparecen automáticamente

### **Botón Force CFDI no aparece:**
- Verificar: `l10n_mx_edi_force_pue_payment_needed = True`
- Verificar: Estado del documento = `payment_sent_pue`
- Verificar: Permisos de usuario

## 📊 Información Técnica

### **Archivos creados/modificados:**
- `models/as_mx_force_cfdi.py` - Herencias principales
- `models/__init__.py` - Imports
- `__manifest__.py` - Versión 1.0.35
- `ChangeLog.txt` - Documentación de cambios

### **Modelos heredados:**
- `AsMxAccountPayment` (account.payment) - **PRINCIPAL**
- `AsMxEdiDocument` (l10n_mx_edi.document)
- `AsMxAccountMove` (account.move) - Respaldo

### **Prefijos de logs:**
- `[AS_PAYMENT_FORCE]` - Pagos
- `[AS_FORCE_CFDI]` - Documentos
- `[AS_MOVE_FORCE]` - Moves

## ✅ Estado Final

🎯 **PROBLEMA RESUELTO**: Los logs de Force CFDI ahora aparecen correctamente en el chatter del payment con información completa y debugging avanzado.

🔥 **FUNCIONALIDAD COMPLETA**: Herencia 100% funcional con logging exhaustivo, chatter automático y troubleshooting simplificado.

---

*Desarrollado por Ahorasoft - Debugging que mata... pero de manera técnicamente elegante* 💀🔧 