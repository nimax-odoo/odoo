# Especificaciones del Módulo as_account_payment

## Modelos

### account.payment (Herencia)
- Agrega campos para manejo de tipo de cambio y documentos EDI XML
- Campos nuevos:
  - xml_exchange_rate (Float): Tipo de cambio desde XML EDI (TipoCambioP)
  - inverse_company_rate (Float): Tasa inversa de la moneda relativa a la moneda de la compañía
  - xml_file (Binary): Archivo XML para subir/reemplazar
  - xml_filename (Char): Nombre del archivo XML
  - as_edi_doc (Char): Nombre del documento EDI adjunto

- Funcionalidades principales:
  - Corrección de EquivalenciaDR en documentos EDI XML
  - Subida y reemplazo de documentos XML EDI
  - Cálculo automático de tasas de cambio inversas

## Vistas

### account.payment.form (Herencia)
- Agrega campos para visualizar y gestionar documentos EDI:
  - Campo de solo lectura para mostrar documento EDI actual
  - Campo para subir nuevo archivo XML
  - Botón para subir/reemplazar XML

## Plantillas

### payment20 (Herencia)
- Modifica el template para usar el inverso del tipo de cambio en EquivalenciaDR

## Seguridad
- Acceso a documentos EDI para todos los usuarios (lectura)
- Acceso a documentos EDI para usuarios base (lectura/escritura)

# Especificaciones del Módulo as_ecommerce_expire_cart

## Modelos

### website (Herencia)
- Agrega configuración para expiración de carritos
- Campo cart_expire_delay: Tiempo en horas para expirar carritos

### sale.order (Herencia)
- Agrega campo cart_expire_date para controlar expiración
- Lógica para prevenir expiración en casos específicos

### res.config.settings (Herencia)
- Configuración del tiempo de expiración de carritos

## Vistas

### Configuración del Sitio Web
- Opciones para configurar tiempo de expiración de carritos

### Plantillas Frontend
- Temporizador de expiración en el carrito
- Integración con el widget de cantidad del carrito

## JavaScript

### WebsiteSaleCartExpireTimer
- Widget para mostrar temporizador de cuenta regresiva
- Actualización automática del tiempo restante
- Refresco de fecha de expiración

## Tareas Programadas
- Tarea para expirar carritos automáticamente cada 5 minutos

# Especificaciones del Módulo as_product_last_price_tab

## Modelos

### product.template (Herencia)
- Agrega pestaña de últimos precios
- Muestra histórico de precios de compra y venta

## Vistas

### product.template.form (Herencia)
- Nueva pestaña para mostrar últimos precios
- Información de últimas compras y ventas 