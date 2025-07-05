# Manual de Usuario - Ahorasoft Lista de Precios por Línea de Productos en Ventas

## Índice
1. [Introducción](#introducción)
2. [Configuración Inicial](#configuración-inicial)
   - [Listas de Precios](#listas-de-precios)
   - [Programas de Lealtad](#programas-de-lealtad)
   - [Configuración del Sistema](#configuración-del-sistema)
3. [Uso del Módulo](#uso-del-módulo)
   - [Creación de Pedidos de Venta](#creación-de-pedidos-de-venta)
   - [Aplicación de Listas de Precios por Línea](#aplicación-de-listas-de-precios-por-línea)
   - [Aplicación de Promociones por Línea](#aplicación-de-promociones-por-línea)
   - [Verificación de Márgenes](#verificación-de-márgenes)
4. [Tipos de Promociones](#tipos-de-promociones)
5. [Reportes y Análisis](#reportes-y-análisis)
6. [Solución de Problemas](#solución-de-problemas)

## Introducción

El módulo "Ahorasoft Lista de Precios por Línea de Productos en Ventas" extiende la funcionalidad estándar de Odoo para permitir la selección de listas de precios específicas a nivel de línea de pedido, en lugar de solo a nivel de pedido completo. También integra un sistema de promociones/programas de lealtad por línea de pedido.

Este manual le guiará a través de la configuración y uso del módulo para aprovechar al máximo sus funcionalidades.

## Configuración Inicial

### Listas de Precios

1. Vaya a **Ventas > Configuración > Listas de Precios**
2. Cree o edite las listas de precios según sus necesidades
3. Para cada lista de precios, puede configurar:
   - Nombre y moneda
   - Reglas de precios basadas en productos, categorías, cantidades, etc.
   - Utilidad esperada (campo adicional)

4. Para marcar una lista de precios como "Tarifa Base":
   - Edite la lista de precios
   - Active la casilla "Tarifa Base"
   - Guarde los cambios

> **Nota**: Debe existir al menos una tarifa base por cada moneda que utilice en el sistema.

### Programas de Lealtad

1. Vaya a **Ventas > Configuración > Programas de Lealtad**
2. Cree un nuevo programa de lealtad
3. Configure los campos básicos:
   - Nombre
   - Tipo de programa
   - Reglas de aplicación

4. En la pestaña "Configuración Adicional", configure:
   - Lista de Precios: seleccione la lista de precios asociada a esta promoción
   - Tipo de Promoción: seleccione entre Normal, Oportunidad, Demo, Precio Especial o Rebate
   - Campos de precios y costos en USD
   - Dominio de Productos: expresión de dominio para filtrar productos aplicables
   - Dominio de Clientes: expresión de dominio para filtrar clientes aplicables
   - Fechas de validez: desde y hasta cuándo es válida la promoción
   - Porcentaje o monto fijo de descuento
   - Cantidad máxima permitida: límite de unidades que pueden beneficiarse de esta promoción

### Configuración del Sistema

1. Vaya a **Configuración > Parámetros del Sistema**
2. Configure los siguientes parámetros:
   - `as_sale_pricelist.as_margin_minimo`: margen mínimo permitido por línea
   - `as_sale_pricelist.as_margin_global`: margen global mínimo permitido

## Uso del Módulo

### Creación de Pedidos de Venta

1. Vaya a **Ventas > Pedidos > Pedidos**
2. Cree un nuevo pedido de venta
3. Seleccione el cliente
4. Seleccione la moneda en el campo "Moneda"
5. El sistema asignará automáticamente la lista de precios base para esa moneda
6. Añada líneas de productos al pedido

### Aplicación de Listas de Precios por Línea

1. En la línea de pedido, haga clic en el botón "Precios"
2. Se abrirá un asistente mostrando las listas de precios disponibles en la moneda del pedido
3. Seleccione la lista de precios deseada para esa línea específica
4. Haga clic en "Aplicar"
5. El sistema recalculará el precio unitario y los márgenes para esa línea

### Aplicación de Promociones por Línea

1. En la línea de pedido, haga clic en el botón "Promo"
2. Se abrirá un asistente mostrando las promociones disponibles para ese producto
3. El sistema filtrará automáticamente las promociones según:
   - Producto seleccionado
   - Cliente del pedido
   - Fechas de validez
4. Seleccione la promoción deseada
5. Haga clic en "Aplicar"
6. El sistema recalculará el precio, costos y márgenes según el tipo de promoción

### Verificación de Márgenes

Al confirmar un pedido de venta, el sistema verificará:
1. Que cada línea tenga un margen superior al mínimo configurado
2. Que el margen global del pedido sea superior al mínimo configurado

Si alguna línea tiene un margen inferior al mínimo pero superior a cero:
1. Se mostrará un asistente de aprobación
2. Un usuario con permisos deberá aprobar la venta con márgenes bajos

Si alguna línea tiene un margen inferior al global:
1. Se mostrará un mensaje de error
2. Deberá modificar los precios antes de confirmar

## Tipos de Promociones

El módulo soporta varios tipos de promociones, cada una con un comportamiento específico:

### Normal
- Promoción estándar sin cálculos especiales

### Oportunidad (DEAL)
- Aplica un porcentaje de descuento sobre el precio base
- Recalcula el costo para mantener el margen deseado

### Demo (DEMO)
- Aplica un descuento fijo o porcentual sobre el precio de lista
- Ideal para productos de demostración

### Precio Especial (ESPECIAL)
- Establece un precio fijo en USD para el producto
- Útil para ofertas especiales o precios negociados

### Rebate (FABRICANTE)
- Aplica un descuento proporcionado por el fabricante
- Reduce tanto el precio como el costo, manteniendo el margen

## Reportes y Análisis

El módulo incluye varios reportes para analizar el uso de listas de precios y promociones:

1. **Historial de Promociones**
   - Acceda desde **Ventas > Reportes > Historial de Promociones**
   - Muestra todas las promociones aplicadas a pedidos
   - Permite filtrar por cliente, producto, vendedor, etc.

2. **Reporte de Comisiones**
   - Acceda desde **Ventas > Reportes > Comisiones**
   - Calcula las comisiones basadas en ventas y promociones aplicadas

## Solución de Problemas

### No se muestran listas de precios al hacer clic en "Precios"
- Verifique que existan listas de precios en la moneda del pedido
- Verifique que el usuario tenga permisos para ver listas de precios

### No se muestran promociones al hacer clic en "Promo"
- Verifique que existan programas de lealtad activos
- Verifique que el producto cumpla con el dominio de productos de alguna promoción
- Verifique que el cliente cumpla con el dominio de clientes de alguna promoción
- Verifique que las fechas de validez incluyan la fecha actual

### Error al confirmar: "No se puede confirmar la venta, modifique sus precios"
- El margen de alguna línea es inferior al margen global mínimo
- Modifique el precio o aplique una lista de precios/promoción diferente

### Error al confirmar: "No se permiten muchas promociones"
- Ha excedido la cantidad máxima permitida para esa promoción
- Reduzca la cantidad o utilice otra promoción

### Error al confirmar: "EXISTEN LINEAS PRODUCTO SIN PRECIO BASE"
- Alguna línea no tiene una lista de precios asignada
- Haga clic en "Precios" y seleccione una lista de precios para esa línea 