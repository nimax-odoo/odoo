# Manual de Usuario - API de Stock para Odoo 15

## Índice
1. [Introducción](#introducción)
2. [Instalación](#instalación)
3. [Configuración](#configuración)
4. [Uso de la API](#uso-de-la-api)
5. [Ejemplos prácticos](#ejemplos-prácticos)
6. [Pruebas con Postman](#pruebas-con-postman)
7. [Solución de problemas](#solución-de-problemas)
8. [Preguntas frecuentes](#preguntas-frecuentes)

## Introducción

La API de Stock es una interfaz de programación que permite consultar la disponibilidad de stock en Odoo 15 de manera segura y eficiente. Esta API es de solo lectura, lo que significa que únicamente permite consultar información sin realizar modificaciones en los datos.

### Características principales

- **Consulta de stock en tiempo real**: Obtenga información actualizada sobre la disponibilidad de productos.
- **Filtrado flexible**: Consulte por código de producto o ubicación específica.
- **Seguridad integrada**: Autenticación mediante clave API única por usuario.
- **Respuestas optimizadas**: Formato JSON simplificado y enfocado en los datos esenciales.
- **Agrupación automática**: Los resultados duplicados se agrupan automáticamente, sumando las cantidades.
- **Compatibilidad**: Soporte para métodos anteriores para facilitar la transición.
- **Control de visibilidad**: Posibilidad de configurar el porcentaje de stock visible por usuario.

## Instalación

1. Asegúrese de tener Odoo 15 instalado y funcionando correctamente.
2. Instale el módulo "as_stock_api" desde el menú Aplicaciones:
   - Vaya a **Aplicaciones** en el menú principal
   - Quite el filtro "Aplicaciones" para ver todos los módulos
   - Busque "Ahorasoft Inventario API"
   - Haga clic en "Instalar"
3. Espere a que la instalación se complete.
4. Reinicie el servidor Odoo para asegurar que todos los cambios se apliquen correctamente.

## Configuración

### Configuración de usuario

Cada usuario que necesite acceder a la API debe tener su propia clave API configurada:

1. Vaya a **Configuración > Usuarios y Compañías > Usuarios**
2. Seleccione el usuario que necesita acceso a la API
3. Vaya a la pestaña **API de Stock**
4. Active la casilla **API de Stock Habilitada**
5. Configure el **Porcentaje de Stock a Mostrar** (por defecto 100%)
6. Haga clic en el botón **Generar Nueva Clave**
7. Se mostrará un mensaje con la clave generada
8. La clave también aparecerá en el campo **Clave API (para copiar)**
9. Utilice el botón **Copiar al Portapapeles** para copiar la clave fácilmente

### Permisos necesarios

El usuario debe tener los siguientes permisos para utilizar la API:

- Permisos de lectura en el modelo `stock.quant`
- Pertenencia al grupo "Inventario/Usuario" o superior

Para verificar o modificar los permisos:

1. Vaya a **Configuración > Usuarios y Compañías > Usuarios**
2. Seleccione el usuario
3. Vaya a la pestaña **Acceso a aplicaciones**
4. Asegúrese de que tenga acceso a "Inventario" con nivel "Usuario" o superior

## Uso de la API

### Endpoint principal

```
POST /nimax/stock
```

### Parámetros de solicitud

La API acepta los siguientes parámetros en el cuerpo JSON de la solicitud:

| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|-------------|-------------|
| api_key | string | Sí | Clave API del usuario |
| default_code | string | No | Código del producto a consultar |
| location_id | integer | No | ID de la ubicación a consultar |

### Códigos de estado HTTP

| Código | Descripción |
|--------|-------------|
| 200 | Solicitud exitosa |
| 400 | Parámetros inválidos |
| 401 | No se proporcionó API key |
| 403 | API key inválida o sin permisos |
| 404 | Producto con el código especificado no encontrado |
| 500 | Error interno del servidor |

## Ejemplos prácticos

### Consultar todo el stock disponible

```bash
curl -X POST \
  https://su-servidor-odoo.com/nimax/stock \
  -H 'Content-Type: application/json' \
  -d '{
    "api_key": "SU_CLAVE_API"
  }'
```

### Consultar stock de un producto específico

```bash
curl -X POST \
  https://su-servidor-odoo.com/nimax/stock \
  -H 'Content-Type: application/json' \
  -d '{
    "api_key": "SU_CLAVE_API",
    "default_code": "PROD001"
  }'
```

### Consultar stock en una ubicación específica

```bash
curl -X POST \
  https://su-servidor-odoo.com/nimax/stock \
  -H 'Content-Type: application/json' \
  -d '{
    "api_key": "SU_CLAVE_API",
    "location_id": 8
  }'
```

### Consultar stock de un producto en una ubicación específica

```bash
curl -X POST \
  https://su-servidor-odoo.com/nimax/stock \
  -H 'Content-Type: application/json' \
  -d '{
    "api_key": "SU_CLAVE_API",
    "default_code": "PROD001",
    "location_id": 8
  }'
```

## Pruebas con Postman

La API incluye una colección de Postman preconfigurada para facilitar las pruebas:

### Descarga de la colección

1. En el formulario de usuario, después de generar una clave API, haga clic en el botón **Descargar Colección de Postman**
2. Se descargará un archivo JSON con la colección preconfigurada con su clave API

### Importación en Postman

1. Abra Postman
2. Haga clic en el botón **Import** (Importar)
3. Seleccione el archivo JSON descargado
4. La colección "Odoo 15 - API de Stock" aparecerá en el panel izquierdo

### Configuración de variables

La colección ya viene preconfigurada con su clave API, pero puede necesitar ajustar otras variables:

1. Haga clic en los tres puntos (...) junto al nombre de la colección
2. Seleccione **Edit** (Editar)
3. Vaya a la pestaña **Variables**
4. Configure las siguientes variables:
   - `base_url`: URL base de su instancia de Odoo (por defecto: http://localhost:8069)
   - `default_code`: Código del producto que quiere consultar
   - `location_id`: ID de la ubicación que quiere consultar
   - `product_id`: ID del producto (para pruebas de compatibilidad)

### Ejecución de pruebas

La colección incluye ejemplos para todos los casos de uso comunes:

- Consultar todo el stock
- Consultar por código de producto
- Consultar por ubicación
- Consultar por código de producto y ubicación
- Pruebas de error (sin API key, con API key inválida)
- Ejemplos de compatibilidad (método GET, parámetro product_id)

Para ejecutar una prueba, simplemente seleccione la solicitud deseada y haga clic en **Send** (Enviar).

## Solución de problemas

### Error 401: No se proporcionó API key

**Problema**: La solicitud no incluye una clave API.

**Solución**: Asegúrese de incluir el parámetro `api_key` en el cuerpo de la solicitud JSON.

### Error 403: API key inválida

**Problema**: La clave API proporcionada no es válida o el usuario no tiene los permisos necesarios.

**Solución**:
- Verifique que la clave API sea correcta
- Asegúrese de que el usuario tenga la API habilitada
- Verifique que el usuario tenga permisos de lectura en `stock.quant`

### Error 404: Producto no encontrado

**Problema**: El código de producto especificado no existe en el sistema.

**Solución**:
- Verifique que el código de producto sea correcto
- Compruebe que el producto exista en Odoo y tenga un código asignado

### Error 500: Error interno del servidor

**Problema**: Ha ocurrido un error inesperado en el servidor.

**Solución**:
- Revise los logs del servidor Odoo para obtener más detalles
- Contacte con el administrador del sistema

### Resultados vacíos

**Problema**: La API devuelve un array vacío aunque debería haber stock.

**Solución**:
- Verifique que el producto tenga stock en ubicaciones internas
- Compruebe que no esté filtrando por una ubicación incorrecta
- Asegúrese de que el usuario tenga acceso a las ubicaciones donde hay stock

## Preguntas frecuentes

### ¿Puedo modificar el stock a través de la API?

No, esta API es de solo lectura por razones de seguridad. Para modificar el stock, debe utilizar la interfaz de usuario de Odoo o desarrollar una API personalizada con las medidas de seguridad adecuadas.

### ¿Cómo puedo obtener el ID de una ubicación?

El ID de ubicación se puede encontrar en la URL cuando se visualiza una ubicación en Odoo. Por ejemplo, en la URL `https://su-servidor-odoo.com/web#id=8&model=stock.location`, el ID es 8.

### ¿La API devuelve stock en ubicaciones virtuales?

No, la API solo devuelve stock en ubicaciones internas (tipo = 'internal'). Las ubicaciones virtuales, de proveedor, cliente, etc. no se incluyen en los resultados.

### ¿Cómo se manejan los productos sin código?

Para productos sin código (`default_code`), el campo `product_code` en la respuesta aparecerá como una cadena vacía (""). Se recomienda asignar códigos a todos los productos para facilitar su identificación.

### ¿Qué sucede si hay múltiples registros para el mismo producto en la misma ubicación?

La API agrupa automáticamente los resultados por ubicación y código de producto, sumando las cantidades disponibles. Esto proporciona una vista consolidada del stock total disponible.

### ¿Puedo mostrar solo un porcentaje del stock real en la API?

Sí, cada usuario puede configurar un "Porcentaje de Stock a Mostrar" en su perfil. Por ejemplo, si configura 80%, la API mostrará solo el 80% del stock real para todas las consultas realizadas con la clave API de ese usuario. Esto puede ser útil para:

- Mantener un margen de seguridad en los sistemas externos
- Evitar sobrevender productos en tiendas online
- Tener en cuenta posibles discrepancias de inventario
- Crear diferentes niveles de visibilidad para distintos usuarios o sistemas

El valor se configura usando el widget de porcentaje de Odoo, donde puede seleccionar fácilmente el porcentaje deseado. Si el porcentaje se deja en 100% (valor por defecto), se mostrará el stock real completo.

### ¿Puedo limitar el número de resultados devueltos?

Actualmente, la API devuelve todos los resultados que coinciden con los criterios de filtrado. Si necesita limitar los resultados, debe implementar esta lógica en su aplicación cliente.

---

Para más información o soporte técnico, contacte con Ahorasoft:
- Web: [http://www.ahorasoft.com](http://www.ahorasoft.com)
- Email: soporte@ahorasoft.com