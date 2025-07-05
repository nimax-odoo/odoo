# Especificaciones para la Migración del Módulo as_sale_pricelist a Odoo 18 Enterprise

<specs>
1. El módulo debe ser compatible con Odoo 18 Enterprise.
2. Mantener todos los nombres de campos existentes para asegurar la compatibilidad con la base de datos actual.
3. Preservar la funcionalidad de listas de precios por línea de pedido (orderline).
4. Mantener el sistema de promociones/cupones por línea de pedido.
5. El flujo de usuario debe permitir seleccionar la lista de precios y luego la promoción para cada línea de pedido.
6. Crear un modelo personalizado "as.coupon.program" para reemplazar la funcionalidad del módulo "Loyalty" de Odoo 18.
7. Nombre del modulo "as_sale_pricelist"
</specs>

<rules>
1. NO cambiar los nombres de los campos existentes para mantener la compatibilidad con la base de datos.
2. Adaptar el código a la API y estructura de Odoo 18 Enterprise.
3. Asegurar que todas las dependencias sean compatibles con Odoo 18.
4. Mantener la misma experiencia de usuario en cuanto a la selección de listas de precios y promociones.
5. Crear un modelo personalizado "as.coupon.program" en lugar de integrar con el módulo de lealtad (Loyalty).
6. Preservar toda la lógica de negocio existente adaptándola a la nueva versión.
7. Usar el elemento <list> en lugar de <tree> en todas las vistas XML.
8. Usar "list" en lugar de "tree" en el atributo view_mode de las acciones.
</rules>

<challenges_and_solutions>
## Desafíos Encontrados y Soluciones Implementadas

### 1. Cambios en la Estructura de Vistas XML
**Desafío**: En Odoo 18, el elemento `<tree>` ha sido reemplazado por `<list>` en todas las vistas.
**Solución**: Se actualizaron todas las vistas del módulo para usar `<list>` en lugar de `<tree>`, incluyendo vistas embebidas.

### 2. Cambios en el Atributo view_mode
**Desafío**: El atributo `view_mode` en las acciones ahora usa "list" en lugar de "tree".
**Solución**: Se actualizaron todas las acciones para usar "list" en lugar de "tree" en el atributo `view_mode`.

### 3. Problemas con Dependencias
**Desafío**: El módulo "loyalty" en Odoo 18 tiene una estructura diferente al módulo "coupon" en versiones anteriores.
**Solución**: Se creó un modelo personalizado "as.coupon.program" para reemplazar la funcionalidad del módulo "loyalty".

### 4. Errores de Clave Foránea
**Desafío**: Al migrar, surgieron errores de clave foránea debido a referencias a registros que ya no existen.
**Solución**: Se crearon scripts de migración para manejar la transición, incluyendo:
- Cambio de `ondelete='set null'` para el campo `last_promo_id` en `sale.order`
- Cambio de `ondelete='restrict'` para el campo `coupon_ids` en `sale.order.line`
- Scripts de pre-migración para limpiar referencias problemáticas

### 5. Tabla Inexistente
**Desafío**: Error "relation 'as_coupon_program' does not exist" al duplicar registros.
**Solución**: Se crearon scripts de migración para verificar y crear la tabla si no existe, y para corregir las relaciones entre tablas.

### 6. Cambios en la Estructura de Formularios
**Desafío**: La estructura de los formularios de venta ha cambiado en Odoo 18.
**Solución**: Se reemplazó completamente el campo `order_line` en la vista de formulario de venta para adaptarlo a la nueva estructura.
</challenges_and_solutions>

<your_task>
1. Analizar el código actual del módulo as_sale_pricelist para Odoo 15.
2. Identificar todos los cambios necesarios para hacerlo compatible con Odoo 18 Enterprise.
3. Actualizar las dependencias en el archivo __manifest__.py.
4. Adaptar los modelos Python para usar la API actual de Odoo 18.
5. Actualizar las vistas XML para asegurar compatibilidad con Odoo 18.
6. Crear un modelo personalizado "as.coupon.program" para reemplazar la funcionalidad del módulo "loyalty".
7. Probar exhaustivamente todas las funcionalidades para asegurar que funcionan correctamente.
8. Documentar todos los cambios realizados y cualquier consideración importante para la migración.
</your_task>

<deliverables>
1. Código fuente actualizado del módulo as_sale_pricelist compatible con Odoo 18 Enterprise.
2. Documentación de los cambios realizados en el archivo ChangeLog.txt.
3. Scripts de migración para manejar la transición de datos.
4. Modelo personalizado "as.coupon.program" para reemplazar la funcionalidad del módulo "loyalty".
</deliverables>

<migration_steps>
## Pasos de Migración Realizados

1. **Actualización de Dependencias**:
   - Eliminada la dependencia del módulo "loyalty"
   - Eliminada la dependencia del módulo "l10n_mx_edi_40" que no está disponible

2. **Creación de Modelo Personalizado**:
   - Creado el modelo "as.coupon.program" para reemplazar "loyalty.program"
   - Implementados todos los campos necesarios para mantener la funcionalidad

3. **Actualización de Modelos Relacionados**:
   - Actualizado "sale.order.line" para usar "as.coupon.program"
   - Actualizado "sale.order" para usar "as.coupon.program"
   - Actualizado "as.sale.order.promo.wizard" para usar "as.coupon.program"
   - Actualizado "tf.history.promo" para usar "as.coupon.program"

4. **Actualización de Vistas XML**:
   - Cambiado `<tree>` por `<list>` en todas las vistas
   - Cambiado `view_mode="tree,form"` por `view_mode="list,form"` en todas las acciones
   - Reemplazado completamente el campo `order_line` en la vista de formulario de venta

5. **Scripts de Migración**:
   - Creados scripts de pre-migración para limpiar referencias problemáticas
   - Creados scripts de post-migración para verificar y corregir relaciones

6. **Pruebas y Correcciones**:
   - Corregidos errores de XPath en vistas XML
   - Corregidos errores de clave foránea
   - Corregidos errores de tabla inexistente
</migration_steps>

<context>
Este módulo es crítico para el negocio ya que gestiona las listas de precios y promociones a nivel de línea de pedido. La migración ha sido cuidadosa para mantener toda la funcionalidad existente mientras se adapta a la nueva versión de Odoo.

La decisión de crear un modelo personalizado "as.coupon.program" en lugar de integrar con el módulo "loyalty" se tomó para evitar problemas de normalización y mantener un mayor control sobre la funcionalidad.
</context>

<version_history>
## Historial de Versiones

### 18.0.1.0.12 (2023-03-13)
- Cambiado el elemento <tree> por <list> en las vistas embebidas.
- Corregido el error al abrir el formulario de contactos.

### 18.0.1.0.11 (2023-03-13)
- Actualizado el atributo view_mode en todas las acciones.
- Corregido el problema al hacer clic en contactos desde el formulario de orden de venta.

### 18.0.1.0.10 (2023-03-13)
- Cambiado el elemento <tree> por <list> en todas las vistas del módulo.
- Corregido el error "Cannot find key 'tree' in the 'views' registry".

### 18.0.1.0.9 (2023-03-13)
- Agregado script de migración para crear la tabla as_coupon_program.
- Solucionado el error "relation 'as_coupon_program' does not exist".

### 18.0.1.0.8 (2023-03-13)
- Actualizado el atributo mode del campo order_line.
- Cambiado el elemento <tree> por <list> en la vista de líneas de pedido.

### 18.0.1.0.7 (2023-03-13)
- Corrección radical de la vista XML para órdenes de venta.
- Reemplazo completo del campo order_line para evitar problemas con XPath.

### 18.0.1.0.6 (2023-03-12)
- Corrección de la vista XML para órdenes de venta.
- Corrección de expresiones XPath que causaban errores de instalación.

### 18.0.1.0.5 (2023-03-12)
- Eliminada la dependencia del módulo "loyalty".
- Creado un modelo personalizado "as.coupon.program".

### 18.0.1.0.4 (2023-03-12)
- Cambiado el campo `last_promo_id` en el modelo `sale.order`.
- Creado un script de pre-migración más agresivo.

### 18.0.1.0.3 (2023-03-12)
- Añadido `ondelete='cascade'` al campo `sh_promo_id`.
- Ampliado el script de pre-migración.

### 18.0.1.0.2 (2023-03-12)
- Añadido `ondelete='set null'` al campo `last_promo_id`.
- Añadido `ondelete='restrict'` al campo `coupon_ids`.

### 18.0.1.0.1 (2023-03-12)
- Eliminada la dependencia del módulo "l10n_mx_edi_40".

### 18.0.1.0.0 (2023-03-12)
- Migración inicial del módulo a Odoo 18 Enterprise.
</version_history>
