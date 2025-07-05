# Ahorasoft Lista de Precios por Línea de Productos en Ventas

## Descripción
Este módulo extiende la funcionalidad estándar de listas de precios de Odoo para permitir la selección de listas de precios específicas a nivel de línea de pedido (orderline), en lugar de solo a nivel de pedido completo. También integra un sistema de promociones/programas de lealtad por línea de pedido.

## Características Principales
- Selección de listas de precios específicas para cada línea de pedido
- Aplicación de promociones/programas de lealtad individualmente a cada línea
- Cálculo de márgenes y utilidades por línea
- Conversión automática de precios entre monedas (MXN/USD)
- Historial de promociones aplicadas
- Control de cantidades máximas por promoción
- Validación de márgenes mínimos

## Requisitos
- Odoo 18 Enterprise
- Módulos dependientes:
  - base
  - sale_management
  - product
  - account
  - sale_margin
  - as_product_last_price_tab
  - purchase
  - loyalty
  - crm
  - stock
  - report_xlsx
  - sale
  - l10n_mx_edi
  - stock_account
  - bi_manual_currency_exchange_rate

## Instalación
1. Copie este módulo en la carpeta de addons de Odoo
2. Actualice la lista de aplicaciones
3. Instale el módulo "Ahorasoft Lista de Precios por Línea de Productos en Ventas"
4. Configure las listas de precios y programas de lealtad según sea necesario

## Configuración
### Listas de Precios
- Cree las listas de precios necesarias en Ventas > Configuración > Listas de Precios
- Marque la opción "Tarifa Base" en las listas de precios que desee usar como base para cálculos

### Programas de Lealtad
- Cree los programas de lealtad en Ventas > Configuración > Programas de Lealtad
- Configure los campos adicionales en la pestaña "Configuración Adicional":
  - Lista de Precios
  - Tipo de Promoción
  - Dominio de Productos
  - Dominio de Clientes
  - Fechas de validez
  - Cantidad máxima permitida

## Uso
1. Cree un nuevo pedido de venta
2. Añada líneas de productos
3. Para cada línea, puede:
   - Hacer clic en el botón "Precios" para seleccionar una lista de precios específica
   - Hacer clic en el botón "Promo" para aplicar una promoción/programa de lealtad
4. El sistema calculará automáticamente los precios, márgenes y totales

## Soporte
Para soporte técnico, contacte a:
- Email: soporte@ahorasoft.com
- Website: http://www.ahorasoft.com

## Autor
- Ahorasoft

## Licencia
LGPL-3
