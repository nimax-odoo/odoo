# AS: Botón Timbrar Factura MX Manual

## Descripción
Este módulo extiende la funcionalidad de la localización mexicana (l10n_mx_edi) de Odoo 18 Enterprise, proporcionando:

1. **Botón de timbrado manual**: Permite a los usuarios forzar el proceso de timbrado de una factura CFDI manualmente.
2. **Formato personalizado de impresión**: Implementa un formato de reporte para facturas adaptado a las necesidades específicas de NIMAX.

## Características

### Timbrado Manual
- Botón adicional en la vista de factura que ejecuta el proceso de timbrado
- Útil para depuración y casos donde el timbrado automático falla
- Muestra mensajes detallados sobre errores para facilitar la solución de problemas

### Formato de Impresión
- Diseño profesional adaptado a los requisitos de NIMAX
- Formato de letra personalizado (Helvetica Neue)
- Incluye todos los datos fiscales requeridos por el SAT
- Código QR para validación en el portal del SAT
- Secciones para notas importantes y términos de pago

## Instalación
1. Coloque el módulo en la carpeta de addons de Odoo
2. Actualice la lista de aplicaciones
3. Instale el módulo "AS: Botón Timbrar Factura MX Manual"

## Requisitos
- Odoo 18 Enterprise
- Módulo l10n_mx_edi (incluido en la versión Enterprise)

## Uso
1. Vaya a Facturación > Clientes > Facturas
2. Cree una nueva factura o seleccione una existente
3. Para timbrar manualmente, haga clic en el botón "Timbrar" que aparece en la parte superior
4. Para imprimir con el formato personalizado, seleccione la opción "Factura MX" en el menú de impresión

## Solución de Problemas

### Error de ID duplicado (as_mx_invoice_report_template)
Si al actualizar el módulo aparece un error como:
```
odoo.tools.convert.ParseError: while parsing .../as_report_format.xml:37
For external id as_mx_invoice.as_mx_invoice_report_template when trying to create/update a record of model ir.actions.report found record of different model ir.ui.view...
```

Siga estos pasos para resolverlo:

1. Detenga el servidor Odoo
2. Ejecute el siguiente comando SQL para eliminar el registro conflictivo:
   ```sql
   psql -d SU_BASE_DE_DATOS -c "DELETE FROM ir_model_data WHERE name='as_mx_invoice_report_template';"
   ```
3. Reinicie el servidor Odoo con la opción de actualización:
   ```
   ./odoo-bin -u as_mx_invoice -d SU_BASE_DE_DATOS
   ```

Si el problema persiste, es posible que necesite desinstalar y reinstalar completamente el módulo:
```sql
psql -d SU_BASE_DE_DATOS -c "DELETE FROM ir_module_module WHERE name='as_mx_invoice'; DELETE FROM ir_model_data WHERE module='as_mx_invoice';"
```

### Error "l10n_mx_edi_get_xml_etree" al generar reportes
Si al generar reportes de factura aparece un error como:
```
AttributeError: 'account.move' object has no attribute 'l10n_mx_edi_get_xml_etree'
```

Esto ocurre porque:
1. La factura no ha sido timbrada (no tiene CFDI) o
2. El módulo necesita la versión 1.0.15 o superior que incluye estos métodos

**Solución**: Actualice el módulo a la versión 1.0.15 o superior donde se ha implementado el manejo defensivo de estos métodos.

Si necesita visualizar facturas sin timbrar, la versión 1.0.15+ ahora maneja este caso correctamente y mostrará el formato sin la información del CFDI.

### Error "TypeError: 'NoneType' object is not callable" en reporte
Si aparece este error al generar el reporte de factura:
```
TypeError: 'NoneType' object is not callable
Template: as_mx_invoice.as_report_invoice_mx
```

Esto ocurre por un problema en la evaluación de las expresiones condicionales en la plantilla QWeb. 

**Solución**: Actualice el módulo a la versión 1.0.18 o superior donde se ha eliminado por completo el uso de funciones Python en la plantilla QWeb.

#### Nota sobre cambios en la versión 1.0.18:
En la versión 1.0.18 hemos realizado una simplificación radical de la plantilla que:
1. Elimina todas las llamadas dinámicas a métodos Python desde QWeb
2. Reemplaza todos los `t-esc` con `t-field` para mayor seguridad
3. Elimina tablas de impuestos detalladas que presentaban problemas 
4. Simplifica el código QR para mostrar solo el UUID
5. Elimina las fuentes personalizadas en favor de Arial/Helvetica estándar
6. Elimina todas las condiciones complejas y llamadas a funciones helper

Este enfoque prioriza la estabilidad y compatibilidad con Odoo 18 sobre la funcionalidad dinámica completa. El reporte ahora es más sencillo pero funciona de manera confiable.

### Error en button_process_edi_web_services
Si recibe errores de sintaxis relacionados con el método `button_process_edi_web_services`, verifique la versión del módulo. A partir de la versión 1.0.13, se ha corregido la estructura try-except de este método que causaba problemas.

## Soporte
Para obtener ayuda sobre este módulo:
- Envíe un correo a soporte@ahorasoft.com
- Visite http://www.ahorasoft.com

## Licencia
LGPL-3 