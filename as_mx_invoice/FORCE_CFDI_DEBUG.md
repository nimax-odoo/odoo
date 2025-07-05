# 🔥 Force CFDI - Debugging Completo

## 📋 Descripción

Este módulo hereda y extiende la funcionalidad estándar "Force CFDI" de Odoo añadiendo logging completo y mensajes en el chatter para facilitar el debugging y monitoreo de procesos CFDI.

## 🎯 Funcionalidades Agregadas

### 1. **Logging Completo**
- ✅ Logs detallados en todos los pasos del proceso
- ✅ IDs únicos de traza para seguimiento
- ✅ Información de configuración PAC y certificados
- ✅ Tiempos de ejecución
- ✅ Estados antes y después del proceso

### 2. **Mensajes en Chatter**
- 🔥 Notificaciones en tiempo real del proceso
- ✅ Confirmaciones de éxito con UUID
- ⚠️ Advertencias de configuración
- ❌ Errores detallados con información técnica

### 3. **Validaciones Mejoradas**
- ✅ Verificación de estado del documento
- ✅ Validación de configuración PAC
- ✅ Verificación de certificados válidos
- ✅ Control de errores robusto

## 🔧 Modelos Heredados

### **AsMxEdiDocument** (`l10n_mx_edi.document`)
- Hereda: `action_force_payment_cfdi()`
- Añade: Logging completo y chatter para documentos

### **AsMxAccountPayment** (`account.payment`)
- Hereda: `l10n_mx_edi_cfdi_payment_force_try_send()`
- Añade: Logging detallado y chatter para pagos
- **IMPORTANTE**: Los logs aparecen en el chatter del payment, no del move

### **AsMxAccountMove** (`account.move`)
- Hereda: `l10n_mx_edi_cfdi_payment_force_try_send()`
- Añade: Logging detallado para moves (respaldo)

## 📝 Logs Generados

### **Prefix de Logs:**
- `[AS_FORCE_CFDI]` - Para documentos CFDI
- `[AS_PAYMENT_FORCE]` - Para pagos (account.payment)
- `[AS_MOVE_FORCE]` - Para moves (account.move)

### **Información Registrada:**
```
=== INICIANDO FORCE CFDI ===
Document ID: 123
Document State: payment_sent_pue
Move ID: 456
Move Name: PAY/2024/001
SAT State: valid
Payment Currency: MXN
Payment Amount: 1000.00
Company: Mi Empresa SA de CV
PAC Configurado: finkok
Certificado válido encontrado: 30001000000400002434
Llamando al método original action_force_payment_cfdi...
Método original ejecutado en 2.45 segundos
Estado después del Force CFDI: payment_sent
Attachment creado: PAY-2024-001-MX-Payment-2.0.xml
Attachment UUID: 12345678-1234-1234-1234-123456789012
=== FORCE CFDI COMPLETADO ===
```

## 📧 Mensajes en Chatter

### **Tipos de Mensajes:**
- 🔥 **Inicio del proceso**
- ℹ️ **Información general**
- ⚠️ **Advertencias de configuración**
- ✅ **Éxito con UUID**
- ❌ **Errores con detalles técnicos**

## 🚀 Uso

### **Activación Automática:**
La funcionalidad se activa automáticamente al heredar las funciones existentes. No requiere configuración adicional.

### **Donde Aparece:**
1. **Vista de Factura/Pago** → Pestaña CFDI → Botón "Force CFDI"
2. **Logs del servidor** → Búsqueda por `[AS_FORCE_CFDI]` o `[AS_PAYMENT_FORCE]`
3. **Chatter** → Mensajes automáticos durante el proceso

## 🔍 Debugging

### **Para encontrar logs específicos:**
```bash
# Buscar logs de Force CFDI
grep "AS_FORCE_CFDI" /var/log/odoo/odoo18e.nimax.log*

# Buscar logs de Payment Force
grep "AS_PAYMENT_FORCE" /var/log/odoo/odoo18e.nimax.log*

# Buscar logs de Move Force
grep "AS_MOVE_FORCE" /var/log/odoo/odoo18e.nimax.log*

# Buscar por ID específico
grep "PAYMENT-FORCE-123-" /var/log/odoo/odoo18e.nimax.log*
```

### **Verificar en el chatter:**
1. Ir a la factura o pago
2. Revisar mensajes con asunto "Force CFDI - Debug Info"
3. Verificar iconos: 🔥 ✅ ⚠️ ❌

## ⚠️ Consideraciones

### **Performance:**
- Los logs están optimizados para no impactar el rendimiento
- Los mensajes de chatter son asíncronos cuando es posible

### **Seguridad:**
- No se expone información sensible en logs
- Los errores se sanitizan antes de mostrar en chatter

### **Compatibilidad:**
- 100% compatible con la funcionalidad estándar de Odoo
- No modifica el comportamiento original, solo añade información

## 📊 Beneficios

1. **🔧 Debugging Simplificado**: Identificación rápida de problemas
2. **📈 Monitoreo Mejorado**: Seguimiento completo del proceso
3. **👥 Comunicación Clara**: Mensajes comprensibles para usuarios finales
4. **🎯 Troubleshooting Eficiente**: Información técnica detallada
5. **📋 Auditoria Completa**: Registro de todos los pasos realizados

## 🚨 Troubleshooting

### **Problema: No aparecen logs**
```bash
# 1. Verificar que el módulo esté instalado
python3 CHECK_MODULE_STATUS.py

# 2. Actualizar el módulo
python3 UPDATE_MODULE.py

# 3. Verificar logs en tiempo real
tail -f /var/log/odoo/odoo18e.nimax.log* | grep "AS_PAYMENT_FORCE\|AS_FORCE_CFDI"
```

### **Problema: CFDI vacío en payment**
- **Causa**: Los logs están en `account.payment`, no en `account.move`
- **Solución**: Revisar el chatter del payment directamente
- **Verificar**: Que el módulo esté actualizado con la herencia de `account.payment`

### **Problema: Botón Force CFDI no aparece**
- **Verificar**: `l10n_mx_edi_force_pue_payment_needed = True`
- **Verificar**: Estado del documento = `payment_sent_pue`
- **Verificar**: Permisos de usuario (`account.group_account_invoice`)

### **Problema: Error en herencia**
```python
# Verificar en shell de Odoo
payment = env['account.payment'].browse(PAYMENT_ID)
hasattr(payment, '_as_payment_force_log')  # Debe ser True
```

## 🔗 Archivos Relacionados

- `models/as_mx_force_cfdi.py` - Implementación principal
- `models/__init__.py` - Imports del módulo
- `__manifest__.py` - Dependencias (`l10n_mx_edi`)
- `CHECK_MODULE_STATUS.py` - Script de verificación
- `UPDATE_MODULE.py` - Script de actualización

---

*Desarrollado por Ahorasoft - Debugging que mata... técnicamente hablando* 💀🔧 