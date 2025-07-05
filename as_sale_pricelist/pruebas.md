# Documentación de Pruebas - Módulo as_sale_pricelist

## Tabla de Pruebas Funcionales

| Funcionalidad | Sospecha de Mal Funcionamiento | Pasos para Testear | Resultado Esperado |
|---------------|--------------------------------|-------------------|-------------------|
| **Lista de Precios por Línea de Producto** | No | 1. Crear una orden de venta<br>2. Agregar productos a la orden<br>3. Clic en el botón "Actualizar Lista de Precios"<br>4. Verificar que aparezca el wizard con las líneas de productos y sus precios<br>5. Seleccionar una línea y hacer clic en "Aplicar"<br>6. Verificar que el precio se actualice en la línea de venta | Los precios se actualizan correctamente según la lista de precios seleccionada, respetando los márgenes y descuentos configurados |
| **Cálculo de Precio Base USD** | Sí | 1. Crear una orden de venta<br>2. Agregar un producto con categoría que tenga parámetros del proveedor<br>3. Abrir el wizard de lista de precios<br>4. Verificar el campo "PRICE BASE USD"<br>5. Comprobar que el cálculo use la fórmula: `(precio_lista - descuento_socio) * costo_importación * impuesto_importación` | El "PRICE BASE USD" debe calcularse correctamente basado en los parámetros del socio y producto |
| **Cálculo de Precio NIMAX** | Sí | 1. Abrir el wizard de lista de precios<br>2. Verificar el campo "Precio NIMAX"<br>3. Comprobar que el cálculo use la fórmula: `precio_base_usd / (1 - ganancia_esperada/100)` | El precio NIMAX debe reflejar correctamente el margen esperado sobre el precio base |
| **Cálculo de Costo NIMAX** | Sí | 1. Abrir el wizard de lista de precios<br>2. Verificar los campos "Costo NIMAX" y "COST NIMAX MXP"<br>3. Validar la conversión de moneda | Los costos deben calcularse correctamente en ambas monedas (USD y MXN) |
| **Conversión de Moneda** | Sí | 1. Crear una orden de venta con moneda diferente a la de la compañía<br>2. Abrir el wizard de lista de precios<br>3. Verificar que los campos muestren valores en la moneda correcta<br>4. Aplicar precio y verificar que la conversión sea correcta | Las conversiones de moneda deben usar las tasas correctas y mantener coherencia en todos los cálculos |
| **Programas de Cupones** | Sí | 1. Ir al menú principal "Cupones" > "Programas de Promoción"<br>2. Crear un nuevo programa de cupón y configurar reglas de aplicación y recompensas<br>3. Crear una orden de venta<br>4. Agregar productos que cumplan con las reglas<br>5. Aplicar el cupón<br>6. Verificar que el descuento se aplique correctamente | El programa de cupones debe aplicar correctamente los descuentos según las reglas configuradas |
| **Gestión de Cupones** | Sí | 1. Ir al menú principal "Cupones" > "Cupones"<br>2. Crear un nuevo cupón y asociarlo a un programa<br>3. Asignar el cupón a un cliente específico<br>4. En una orden de venta, aplicar el cupón<br>5. Verificar que el estado del cupón cambie correctamente (draft -> sent -> used) | El cupón debe pasar por los diferentes estados y aplicar correctamente el descuento asociado a su programa |
| **Tipos de Programas de Promoción** | Sí | 1. Ir al menú principal "Cupones" > "Programas de Promoción"<br>2. Crear un nuevo programa de tipo "DEAL"<br>3. Crear otro de tipo "DEMO"<br>4. Crear otro de tipo "ESPECIAL"<br>5. Crear otro de tipo "FABRICANTE"<br>6. Verificar que cada tipo muestre los campos específicos correspondientes | Cada tipo de programa debe mostrar campos específicos y funcionar según su lógica propia |
| **Promociones** | Sí | 1. Ir al menú principal "Cupones" > "Programas de Promoción"<br>2. Crear una nueva promoción con reglas específicas<br>3. Crear una orden de venta que cumpla las condiciones<br>4. Verificar que la promoción se aplique automáticamente | Las promociones deben aplicarse automáticamente cuando se cumplen las condiciones |
| **Descuento Máximo** | No | 1. Configurar un programa de cupones con un descuento máximo<br>2. Crear una orden con un valor alto<br>3. Aplicar el cupón<br>4. Verificar que el descuento no supere el máximo configurado | El descuento debe limitarse al valor máximo configurado |
| **Precios Específicos por Categoría** | No | 1. Configurar una lista de precios con ítems específicos para categorías<br>2. Crear una orden de venta<br>3. Agregar productos de esas categorías<br>4. Verificar que se apliquen los precios específicos | Los precios específicos por categoría deben aplicarse correctamente |
| **Historial de Promociones** | No | 1. Aplicar diferentes precios usando el wizard<br>2. Verificar la creación de registros en `tf.history.promo`<br>3. Comprobar que los datos históricos sean correctos | El historial debe guardar correctamente todas las aplicaciones de precios y promociones |
| **Campos Personalizados en Líneas de Venta** | No | 1. Crear una orden de venta<br>2. Aplicar precios desde el wizard<br>3. Revisar que los campos personalizados como MARGIN_MXP, TOTAL_USD, etc. se llenen correctamente | Todos los campos personalizados deben contener los valores calculados correctamente |
| **Utilidad por Lista de Precios** | Sí | 1. Configurar una lista de precios con utilidad (campo as_utilidad)<br>2. Crear una orden de venta<br>3. Usar el wizard para actualizar precios<br>4. Verificar que el margen calculado respete la utilidad configurada | El margen debe calcularse según el porcentaje de utilidad configurado |
| **Descuento Basado en Último Precio de Compra** | Sí | 1. Verificar que el producto tenga un valor en el campo as_last_purchase_price<br>2. Abrir el wizard de lista de precios<br>3. Comprobar que el descuento se calcule correctamente basado en ese precio | El descuento debe calcularse correctamente según la última compra |
| **Parámetros de Socio (tf_partner_id)** | Sí | 1. Configurar parámetros en el socio para diferentes categorías<br>2. Crear una orden de venta con productos de esas categorías<br>3. Verificar que los cálculos usen los parámetros correctos del socio | Los cálculos deben usar los parámetros específicos del socio para cada categoría de producto |
| **Aplicación Masiva de Precios** | No | 1. Crear una orden con múltiples líneas<br>2. Abrir el wizard de lista de precios<br>3. Aplicar precios en varias líneas<br>4. Verificar que todos se actualicen correctamente | Todas las líneas seleccionadas deben actualizarse correctamente |

## Pruebas de Integración

| Integración | Sospecha de Mal Funcionamiento | Pasos para Testear | Resultado Esperado |
|-------------|--------------------------------|-------------------|-------------------|
| **Integración con Módulo de Ventas** | No | 1. Crear una orden de venta<br>2. Aplicar precios y promociones<br>3. Confirmar la orden<br>4. Verificar que los precios y descuentos se mantengan | Los precios y descuentos deben mantenerse en todo el flujo de ventas |
| **Integración con Facturación** | Sí | 1. Crear una orden de venta<br>2. Aplicar precios y promociones<br>3. Confirmar la orden<br>4. Crear factura<br>5. Verificar que los precios y descuentos se transfieran correctamente | Los precios y descuentos deben transferirse correctamente a la factura |
| **Integración con Módulo de Inventario** | No | 1. Crear una orden de venta<br>2. Aplicar precios<br>3. Confirmar la orden<br>4. Verificar que el albarán tenga la información correcta | Los datos de precio no deberían afectar al inventario |
| **Integración entre Programas y Cupones** | Sí | 1. Crear un programa en el menú "Cupones" > "Programas de Promoción"<br>2. Usar el botón "Ver Cupones" en el programa<br>3. Crear un cupón desde allí<br>4. Verificar que el cupón esté correctamente vinculado al programa | El botón debe abrir la vista filtrada de cupones y los nuevos cupones deben heredar las reglas del programa |

## Menús y Navegación

| Menú | Ubicación | Descripción | Funcionalidades Clave |
|------|-----------|-------------|----------------------|
| **Cupones** | Menú principal | Menú raíz para acceder a la funcionalidad de cupones y promociones | Acceso a programas de promoción y cupones individuales |
| **Programas de Promoción** | Cupones > Programas de Promoción | Gestión de todos los programas de promoción y descuentos | Creación y configuración de programas con diferentes tipos (DEAL, DEMO, ESPECIAL, FABRICANTE) |
| **Cupones** | Cupones > Cupones | Gestión de cupones individuales vinculados a programas | Seguimiento del ciclo de vida de cupones (borrador, enviado, usado, expirado, cancelado) |
| **Botón "Actualizar Lista de Precios"** | Órdenes de venta > Pestaña Líneas de pedido | Acceso al wizard de actualización de precios | Selección de precios específicos por línea de producto |

## Pruebas de Seguridad

| Aspecto | Sospecha de Mal Funcionamiento | Pasos para Testear | Resultado Esperado |
|---------|--------------------------------|-------------------|-------------------|
| **Permisos de Usuario** | Sí | 1. Crear un usuario con permisos limitados<br>2. Intentar acceder a las promociones y lista de precios<br>3. Verificar que sólo pueda ver/editar según sus permisos | Los usuarios sólo deben poder acceder a las funcionalidades según sus permisos |
| **Reglas de Registro** | Sí | 1. Crear diferentes usuarios para diferentes equipos de ventas<br>2. Verificar que sólo vean los registros que les corresponden | Las reglas de registro deben aplicarse correctamente |

## Problemas Conocidos

1. **Problema con el Chatter en Programas de Cupón**: Se ha eliminado la herencia de mail.thread para evitar problemas con los seguidores. Los programas de cupón ya no tienen funcionalidad de chatter.
2. **Cálculo de Precios en Monedas**: Posibles errores en las conversiones de moneda cuando se cambia la moneda de la orden.
3. **Compatibilidad con Odoo 18**: Se han realizado adaptaciones para la nueva API de _compute_price_rule, pero pueden existir problemas no identificados.
4. **Estructura de Menús**: La navegación a través de los menús de cupones está funcionando correctamente. Los menús están ubicados en el nivel principal como "Cupones" con submenús para "Programas de Promoción" y "Cupones". 