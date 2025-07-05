# Especificaciones del Módulo as_sale_pricelist

## Propósito
Este módulo extiende la funcionalidad estándar de listas de precios de Odoo para permitir la selección de listas de precios específicas a nivel de línea de pedido (orderline), en lugar de solo a nivel de pedido completo. También integra un sistema de promociones/cupones por línea de pedido.

## Modelos

### SaleOrderLine (sale.order.line)
Extiende el modelo sale.order.line para incluir campos relacionados con listas de precios y promociones.

DESCRIPCIÓN: Permite seleccionar una lista de precios específica para cada línea de pedido, así como aplicar promociones/cupones individualmente.

### SaleOrder (sale.order)
Extiende el modelo sale.order para soportar la funcionalidad de listas de precios por línea.

DESCRIPCIÓN: Permite mantener la lista de precios a nivel de cabecera mientras habilita la posibilidad de seleccionar listas de precios específicas para cada línea.

### as_LoyaltyProgram (loyalty.program)
Extiende el modelo loyalty.program para adaptarlo a la funcionalidad de promociones por línea.

DESCRIPCIÓN: Proporciona campos y métodos adicionales para soportar la aplicación de promociones a nivel de línea de pedido.

### as_SaleOrderPromoWizard (as.sale.order.promo.wizard)
Wizard para aplicar promociones a líneas de pedido específicas.

DESCRIPCIÓN: Permite seleccionar y aplicar promociones específicas a cada línea de pedido.

## Vistas

### view_order_form_inherit_view
Modifica las vistas de pedidos de venta para incluir la selección de listas de precios por línea.

DESCRIPCIÓN: Añade campos en la interfaz de usuario para seleccionar listas de precios y promociones a nivel de línea de pedido.

### as_loyalty_program_form_view
Extiende la vista de programas de lealtad para incluir campos adicionales.

DESCRIPCIÓN: Añade campos específicos para la configuración de promociones por línea de pedido.

## Cambios para Migración a Odoo 18

### Dependencias
- Reemplazado "sale_coupon" por "loyalty" en las dependencias del módulo.
- Actualizada la versión del módulo a "18.0.1.0.0".

### Modelos
- Migrado el modelo "coupon.program" a "loyalty.program".
- Añadidos campos adicionales en "loyalty.program" para mantener la funcionalidad de "coupon.program".
- Actualizado el campo "coupon_ids" en "sale.order.line" para usar "loyalty.program".
- Actualizado el campo "last_promo_id" en "sale.order" para usar "loyalty.program".

### Wizards
- Actualizado el wizard "as.sale.order.promo.wizard" para trabajar con "loyalty.program" en lugar de "coupon.program".
- Adaptada la lógica de aplicación de promociones para usar el nuevo modelo.

### Vistas
- Creada una nueva vista para extender "loyalty.program" con los campos necesarios.
- Mantenida la misma experiencia de usuario en la selección de listas de precios y promociones.

### API
- Actualizado el uso de "self.env.user.company_id" a "self.env.company" según la API de Odoo 18.
- Adaptados los métodos para trabajar con el nuevo módulo de lealtad.

## Flujo de Usuario

1. El usuario crea un pedido de venta.
2. Se selecciona una lista de precios a nivel de pedido (comportamiento estándar).
3. Para cada línea de pedido, el usuario puede:
   - Seleccionar una lista de precios específica diferente a la del pedido.
   - Aplicar una promoción/programa de lealtad específico a esa línea.
4. El sistema calcula los precios y descuentos según las selecciones realizadas.

## Consideraciones para Migración de Datos

1. Los registros existentes en "coupon.program" deben migrarse a "loyalty.program" manteniendo los mismos IDs.
2. Los campos adicionales específicos del módulo deben copiarse al nuevo modelo.
3. Las referencias en "sale.order.line.coupon_ids" y "sale.order.last_promo_id" deben actualizarse para apuntar al nuevo modelo.

## Notas Técnicas

1. El módulo "loyalty" en Odoo 18 reemplaza completamente la funcionalidad de "sale_coupon" de versiones anteriores.
2. Se han mantenido todos los nombres de campos existentes para asegurar la compatibilidad con la base de datos.
3. La lógica de negocio se ha preservado adaptándola a la nueva API y estructura de Odoo 18. 