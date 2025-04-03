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
9. [Lista de precios personalizada](#lista-de-precios-personalizada)

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
6. Opcionalmente, seleccione los **Almacenes Visibles en API** para restringir los resultados a ubicaciones dentro de los almacenes seleccionados
7. Haga clic en el botón **Generar Nueva Clave**
8. Se mostrará un mensaje con la clave generada
9. La clave también aparecerá en el campo **Clave API (para copiar)**
10. Utilice el botón **Copiar al Portapapeles** para copiar la clave fácilmente

### Almacenes visibles en API

La configuración **Almacenes Visibles en API** permite:

- Filtrar los resultados para mostrar solamente stock de ubicaciones dentro de los almacenes seleccionados
- Si no se selecciona ningún almacén, la API mostrará el stock de todos los almacenes
- Esto afecta a ambos endpoints: `/nimax/stock` y `/nimax/stock_with_price`
- La estructura de la respuesta JSON se mantiene igual, solo se filtran los datos

Esta configuración es útil para:
- Restringir los datos a ciertos almacenes específicos para diferentes usuarios de la API
- Simplificar las respuestas para integraciones que solo necesitan datos de ciertos almacenes
- Segmentar el acceso a la información de stock por región o ubicación física

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

### Estructura de la respuesta

```json
[
  {
    "location": "Stock",
    "product_code": "PROD001",
    "product_name": "Producto A",
    "stock": 10,
    "reserved_quantity": 2,
    "attribute_line_ids": [
      {
        "attribute_name": "Color",
        "values": ["Rojo", "Azul"]
      }
    ]
  }
]
```

**Descripción de los campos:**
- **location**: Nombre de la ubicación donde se encuentra el stock
- **product_code**: Código del producto (default_code)
- **product_name**: Nombre completo del producto
- **stock**: Cantidad disponible (después de restar reservas y aplicar porcentaje de visibilidad)
- **reserved_quantity**: Cantidad del producto que está reservada (no disponible para la venta)
- **attribute_line_ids**: Lista simplificada de atributos asociados al producto y sus valores

Para más detalles sobre la estructura de `attribute_line_ids`, consulte la sección [Estructura de attribute_line_ids](#estructura-de-attribute_line_ids).

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

## Lista de precios personalizada

Cada usuario API puede tener configurada su propia lista de precios por defecto desde la sección "API de Stock" en la configuración del usuario. Si se configura una lista de precios, esta tendrá prioridad sobre la lista de precios del cliente al usar el endpoint `/nimax/stock_with_price`.

### Cliente predeterminado por usuario

Además de la lista de precios, cada usuario API puede tener configurado un cliente predeterminado (campo `as_partner_id`). Al configurar un cliente predeterminado:

- No es necesario incluir el parámetro `partner_id` en las llamadas a la API
- Todas las consultas usarán automáticamente el cliente configurado
- Se pueden realizar consultas más simples, solo indicando el producto y/o ubicación

Esta configuración es especialmente útil cuando un usuario API siempre consulta información para el mismo cliente, simplificando las integraciones y reduciendo el riesgo de errores.

### Orden de prioridad para listas de precios:

1. Lista de precios configurada en el usuario API (campo `as_pricelist`)
2. Lista de precios del cliente (propiedad `property_product_pricelist`)
3. Primera lista de precios activa en el sistema (como fallback)

### Endpoint `/nimax/stock_with_price`

Devuelve información de stock con precios NIMAX calculados. Requiere autenticación mediante API key.

**Método:** POST  
**URL:** `/nimax/stock_with_price`
**Tipo de respuesta:** JSON

#### Parámetros del cuerpo de la solicitud

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| api_key | string | Sí | Clave API para autenticación |
| partner_id | integer | Condicional | ID del cliente para determinar la lista de precios. No es necesario si el usuario API tiene configurado un cliente predeterminado |
| default_code | string | No | Código del producto a filtrar |
| location_id | integer | No | ID de la ubicación a filtrar |

**Nota sobre el cliente y lista de precios**: El sistema intentará primero usar el cliente configurado en el usuario API. Si no está configurado, usará el cliente especificado en `partner_id`. De forma similar, primero se intentará usar la lista de precios del usuario API, luego la del cliente.

#### Estructura de la respuesta

```json
[
  {
    "location": "FREF/Stock",
    "product_code": "AD09-00018A-AS",
    "product_name": "[AD09-00018A-AS] Bixolon ASSY-MECHANISM-III-R 20",
    "stock": 33,
    "reserved_quantity": 5,
    "nimax_price_usd": 42.36,
    "pricelist_name": "Public Pricelist USD",
    "pricelist_id": 1,
    "pricelist_currency": "USD",
    "partner_id": 123,
    "partner_name": "Nombre del Cliente",
    "attribute_line_ids": [
      {
        "attribute_name": "Color",
        "values": ["Rojo", "Azul"]
      }
    ]
  }
]
```

**Descripción de los campos:**
- **location**: Nombre de la ubicación donde se encuentra el stock
- **product_code**: Código del producto (default_code)
- **product_name**: Nombre completo del producto
- **stock**: Cantidad disponible (después de restar reservas y aplicar porcentaje de visibilidad)
- **reserved_quantity**: Cantidad del producto que está reservada (no disponible para la venta)
- **nimax_price_usd**: Precio calculado según la fórmula NIMAX
- **pricelist_name**: Nombre de la lista de precios utilizada
- **pricelist_id**: ID de la lista de precios utilizada
- **pricelist_currency**: Moneda de la lista de precios
- **partner_id**: ID del cliente consultado
- **partner_name**: Nombre del cliente consultado
- **attribute_line_ids**: Lista de líneas de atributo asociadas al producto

#### Estructura de attribute_line_ids

El campo `attribute_line_ids` contiene un arreglo con los atributos del producto (como color, tamaño, etc.) y sus posibles valores. Se ha simplificado para mostrar solo la información esencial:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| attribute_name | string | Nombre del atributo (por ejemplo: "Color", "Tamaño") |
| values | array | Lista de valores posibles para este atributo (como "Rojo", "Grande") |

Esta estructura simplificada facilita el procesamiento de las variantes de producto en las aplicaciones cliente, enfocándose solo en los datos necesarios para la identificación de atributos.

#### Cálculo del precio NIMAX

El valor `nimax_price_usd` se calcula utilizando la siguiente fórmula:

```
precio_base_usd = (product.list_price - (product.list_price * descuento_proveedor/100)) * 
                 costo_importacion/100 * 
                 (impuesto_importacion/100)

nimax_price_usd = precio_base_usd / (1 - beneficio_esperado/100)
```

Donde:
- `product.list_price`: Precio de lista del producto
- `descuento_proveedor`: Porcentaje de descuento del proveedor (del parámetro `tf_vendor_parameter_ids` asociado a la categoría del producto)
- `costo_importacion`: Porcentaje de costo de importación (campo `cost_deal_import`)
- `impuesto_importacion`: Porcentaje de impuesto de importación (campo `tf_import_tax` de la plantilla del producto)
- `beneficio_esperado`: Porcentaje de beneficio esperado (de la lista de precios, campo `expected_earning`)

Si el valor `expected_earning` de la lista de precios es igual o mayor a 100%, el precio NIMAX se establece en 0.

#### Ejemplo de cálculo

Para un producto con:
- Precio de lista (`list_price`): $100.00
- Descuento del proveedor: 20%
- Costo de importación: 50%
- Impuesto de importación: 30%
- Beneficio esperado: 25%

El cálculo sería:
```
precio_base_usd = (100 - (100 * 20/100)) * 50/100 * 30/100
                = 80 * 0.5 * 0.3
                = 12.00

nimax_price_usd = 12.00 / (1 - 25/100)
                = 12.00 / 0.75
                = 16.00
```

El precio NIMAX resultante sería $16.00.

#### Posibles errores específicos

| Código | Descripción | Solución |
|--------|-------------|----------|
| 400 | ID de cliente inválido | Verifique que el parámetro `partner_id` sea un ID válido de cliente existente |
| 400 | No se encontró una lista de precios válida | Asegúrese de que el usuario API tenga una lista de precios configurada o que el cliente tenga una lista de precios asignada |
| 404 | Cliente con ID X no encontrado | Verifique que el cliente existe en el sistema |

Si el cálculo del precio falla por alguna razón (por ejemplo, datos incompletos o incoherentes), el campo `nimax_price_usd` se establecerá en 0, pero la consulta seguirá devolviendo el resto de la información del producto.

#### Ejemplo de llamada con curl

```bash
curl -X POST \
  https://su-servidor-odoo.com/nimax/stock_with_price \
  -H 'Content-Type: application/json' \
  -d '{
    "api_key": "SU_CLAVE_API",
    "partner_id": 123,
    "default_code": "AD09-00018A-AS"
  }'
```

#### Ejemplo con cliente predeterminado configurado

Si el usuario API tiene configurado un cliente predeterminado, la llamada se simplifica:

```bash
curl -X POST \
  https://su-servidor-odoo.com/nimax/stock_with_price \
  -H 'Content-Type: application/json' \
  -d '{
    "api_key": "SU_CLAVE_API",
    "default_code": "AD09-00018A-AS"
  }'
```