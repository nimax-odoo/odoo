# Colección de Postman para API de Stock

Esta carpeta contiene una colección de Postman para probar la API de Stock de Odoo 15.

## Contenido

- `as_stock_api_collection.json`: Colección de Postman con todos los endpoints disponibles.

## Instrucciones de uso

1. Descarga e instala [Postman](https://www.postman.com/downloads/) si aún no lo tienes.
2. Abre Postman y haz clic en "Import" (Importar).
3. Selecciona el archivo `as_stock_api_collection.json`.
4. Una vez importada, verás la colección "Odoo 15 - API de Stock" en el panel izquierdo.

## Configuración de variables

Antes de usar la colección, debes configurar las variables:

1. Haz clic en los tres puntos (...) junto al nombre de la colección y selecciona "Edit" (Editar).
2. Ve a la pestaña "Variables".
3. Configura las siguientes variables:
   - `base_url`: URL base de tu instancia de Odoo (por defecto: http://localhost:8069)
   - `api_key`: Tu clave API generada en Odoo
   - `default_code`: Código del producto que quieres consultar (por ejemplo: "PROD001")
   - `location_id`: ID de la ubicación que quieres consultar (opcional)

## Endpoints disponibles

La colección incluye los siguientes endpoints:

1. **Consultar Stock**: Obtiene el stock de todos los productos en todas las ubicaciones.
2. **Consultar Stock por Código de Producto**: Filtra el stock por el código de un producto específico.
3. **Consultar Stock por Ubicación**: Filtra el stock por una ubicación específica.
4. **Consultar Stock por Código de Producto y Ubicación**: Filtra el stock por código de producto y ubicación.
5. **Consultar Stock sin API Key**: Prueba de error cuando no se proporciona API key.
6. **Consultar Stock con API Key Inválida**: Prueba de error cuando se proporciona una API key inválida.
7. **Consultar Stock por ID de Producto (Obsoleto)**: Usa el parámetro product_id obsoleto (mantenido por compatibilidad).
8. **Consultar Stock (GET - Obsoleto)**: Usa el método GET obsoleto (mantenido por compatibilidad).

## Método HTTP

La API utiliza el método POST para mayor seguridad, enviando los parámetros en el cuerpo JSON de la solicitud en lugar de en la URL. Esto es especialmente importante para la API key, que debe mantenerse confidencial.

Ejemplo de cuerpo de solicitud:
```json
{
  "api_key": "tu_clave_api",
  "default_code": "PROD001",
  "location_id": 8
}
```

El método GET y el parámetro product_id siguen disponibles por compatibilidad, pero se recomienda usar POST con default_code.

## Respuestas esperadas

- **200 OK**: La solicitud se completó correctamente y devuelve los datos de stock.
- **400 Bad Request**: Parámetros inválidos.
- **401 Unauthorized**: No se proporcionó API key.
- **403 Forbidden**: API key inválida o usuario sin permisos.
- **404 Not Found**: Producto con el código especificado no encontrado.
- **500 Internal Server Error**: Error en el servidor.

## Ejemplo de respuesta exitosa

```json
[
  {
    "location": "Stock",
    "product_code": "PROD001",
    "product_name": "Producto A",
    "stock": 10.0
  }
]
``` 