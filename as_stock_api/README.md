# API de Stock para Odoo 15

## Descripción
Este módulo proporciona una API REST para consultar la disponibilidad de stock en Odoo 15. La API es de solo lectura y permite filtrar por producto y ubicación.

## Características
- Endpoint REST para consultar stock disponible
- Filtrado por código de producto (default_code) y ubicación
- Autenticación mediante clave API por usuario
- Respuestas en formato JSON simplificadas y enfocadas
- Optimización de consultas para minimizar la carga del servidor
- Fácil visualización y copia de la clave API
- Colección de Postman para pruebas rápidas
- Descarga directa de la colección preconfigurada con la clave API del usuario
- Logs detallados de todas las interacciones para auditoría y depuración
- Manual de usuario accesible públicamente en formato web
- Control de porcentaje de stock visible por usuario

## Instalación
1. Instalar el módulo en Odoo 15
2. Configurar la clave API en el formulario de usuario (pestaña "API de Stock")

## Configuración
1. Acceder al formulario de usuario (Configuración > Usuarios y Compañías > Usuarios)
2. Ir a la pestaña "API de Stock"
3. Activar la opción "API de Stock Habilitada"
4. Configurar el "Porcentaje de Stock a Mostrar" (por defecto 100%)
5. Hacer clic en "Generar Nueva Clave" para obtener una clave API
6. La clave API se mostrará en un mensaje y en el campo "Clave API (para copiar)"
7. Usar el botón "Copiar al Portapapeles" para copiar la clave
8. Opcionalmente, descargar la colección de Postman preconfigurada con su clave API

## Uso
### Endpoint
```
POST /nimax/stock
```

### Cuerpo de la solicitud (JSON)
```json
{
  "api_key": "YOUR_API_KEY",
  "default_code": "PROD001",  // Opcional
  "location_id": 8  // Opcional
}
```

### Respuesta
```json
[
  {
    "location": "Stock",
    "product_code": "PROD001",
    "product_name": "Producto A",
    "stock": 10.0
  },
  ...
]
```

### Códigos de estado
- `200`: Solicitud exitosa
- `400`: Parámetros inválidos
- `401`: No se proporcionó API key
- `403`: API key inválida o sin permisos
- `404`: Producto con el código especificado no encontrado
- `500`: Error interno del servidor

### Compatibilidad
El método GET y el parámetro product_id siguen disponibles por compatibilidad, pero se recomienda usar POST con default_code:

```
GET /nimax/stock?api_key=YOUR_API_KEY&product_id=1&location_id=8
```

## Pruebas con Postman
El módulo incluye una colección de Postman para facilitar las pruebas:

1. En el formulario de usuario, después de generar una clave API, hacer clic en el botón "Descargar Colección de Postman"
2. Importar el archivo descargado en Postman
3. La colección ya estará configurada con su clave API y lista para usar
4. Ejecutar las solicitudes predefinidas

La colección incluye ejemplos de todas las operaciones posibles usando el método POST con default_code, así como ejemplos de los métodos obsoletos para referencia.

Alternativamente, puede descargar la colección manualmente desde `static/postman/as_stock_api_collection.json` y configurar las variables manualmente.

Para más detalles, consultar el archivo `static/postman/README.md`.

## Documentación
El módulo incluye un manual de usuario completo accesible públicamente en:

```
https://su-servidor-odoo.com/nimax/stock/manual
```

Este manual contiene información detallada sobre la instalación, configuración, uso de la API, ejemplos prácticos, solución de problemas y preguntas frecuentes.

## Seguridad
- La API es de solo lectura
- Cada usuario tiene su propia clave API
- Solo usuarios con la API habilitada y con permisos de lectura en `stock.quant` pueden acceder
- La protección CSRF está desactivada para las solicitudes a la API
- Se recomienda usar POST para enviar la clave API en el cuerpo de la solicitud en lugar de en la URL
- Todos los accesos y respuestas se registran en el log para auditoría
- Control de visibilidad de stock por usuario mediante porcentaje configurable

## Logs
El módulo registra detalladamente todas las interacciones:
- Solicitudes recibidas (endpoint, método, parámetros, IP, user agent)
- Respuestas enviadas (endpoint, código de estado, datos)
- Errores y excepciones

Las claves API se ocultan en los logs por seguridad.

## Autor
Ahorasoft (http://www.ahorasoft.com)

## Versión
1.0.20 