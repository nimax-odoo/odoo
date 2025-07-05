#!/bin/bash
# Script de instalación rápida para Force CFDI Debug
# Autor: Ahorasoft

echo "🔥 Instalando Force CFDI Debug..."

# Verificar que estamos en el directorio correcto
if [ ! -f "__manifest__.py" ]; then
    echo "❌ Error: Ejecutar desde el directorio del módulo as_mx_invoice"
    exit 1
fi

echo "📁 Directorio correcto detectado"

# Verificar archivos necesarios
FILES=("models/as_mx_force_cfdi.py" "models/__init__.py" "__manifest__.py")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file encontrado"
    else
        echo "❌ $file NO encontrado"
        exit 1
    fi
done

echo "📦 Todos los archivos necesarios están presentes"

# Verificar proceso de Odoo
ODOO_PROCESS=$(ps aux | grep odoo | grep nimax | grep -v grep)
if [ -n "$ODOO_PROCESS" ]; then
    echo "✅ Proceso de Odoo detectado"
    echo "   $ODOO_PROCESS"
else
    echo "⚠️ No se detectó proceso de Odoo para nimax"
fi

# Verificar logs
LOG_FILE="/var/log/odoo/odoo18e.nimax.log"
if [ -f "$LOG_FILE" ]; then
    echo "✅ Archivo de log encontrado: $LOG_FILE"
else
    echo "⚠️ Archivo de log no encontrado: $LOG_FILE"
    echo "   Verificar configuración de logging"
fi

echo ""
echo "🎯 PASOS PARA COMPLETAR LA INSTALACIÓN:"
echo ""
echo "1️⃣ Actualizar el módulo:"
echo "   - Ir a Apps en Odoo"
echo "   - Buscar 'as_mx_invoice'"
echo "   - Hacer clic en 'Upgrade'"
echo ""
echo "2️⃣ O usar shell de Odoo:"
echo "   cd $(pwd)"
echo "   # En shell de Odoo:"
echo "   exec(open('UPDATE_MODULE.py').read())"
echo ""
echo "3️⃣ Verificar instalación:"
echo "   exec(open('CHECK_MODULE_STATUS.py').read())"
echo ""
echo "4️⃣ Probar Force CFDI:"
echo "   - Ir a un pago con estado 'posted'"
echo "   - Buscar botón 'Force CFDI' en pestaña CFDI"
echo "   - Revisar logs: tail -f $LOG_FILE | grep AS_PAYMENT_FORCE"
echo ""
echo "🔍 Para debugging en tiempo real:"
echo "   tail -f $LOG_FILE | grep 'AS_PAYMENT_FORCE\\|AS_FORCE_CFDI'"
echo ""
echo "📧 Chatter: Los mensajes aparecen automáticamente en el payment"
echo ""
echo "✅ Instalación preparada. Ejecutar pasos 1-4 para completar." 