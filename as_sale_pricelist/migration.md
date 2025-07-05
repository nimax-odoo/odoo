# Proceso de Migración y Actualización

Este documento detalla los pasos necesarios para corregir problemas con la secuencia de IDs en la tabla `coupon_program` y para asegurar la correcta funcionalidad después de cambios recientes.

## Corrección de Secuencia de IDs en `coupon_program`

Se detectaron inconsistencias en los IDs de la tabla `coupon_program`, posiblemente causando errores o conflictos. Los siguientes pasos SQL se ejecutan para reestablecer la secuencia de IDs y asegurar la integridad de la tabla:

1.  **Crear la Secuencia:**
    Se crea una nueva secuencia llamada `coupon_program_id_seq`. Esta secuencia se encargará de generar automáticamente los nuevos IDs numéricos para la tabla.
    ```sql
    CREATE SEQUENCE coupon_program_id_seq
        START WITH 1
        INCREMENT BY 1
        NO MINVALUE
        NO MAXVALUE
        CACHE 1;
    ```

2.  **Asignar Secuencia como Default:**
    Se configura la columna `id` de la tabla `coupon_program` para que utilice la secuencia `coupon_program_id_seq` recién creada como valor por defecto al insertar nuevos registros. Esto asegura que cada nuevo programa de cupones obtenga un ID único y secuencial.
    ```sql
    ALTER TABLE coupon_program
    ALTER COLUMN id SET DEFAULT nextval('coupon_program_id_seq');
    ```

3.  **Establecer Clave Primaria (si es necesario):**
    Se asegura que la columna `id` sea la clave primaria de la tabla `coupon_program`. Esto es fundamental para la integridad referencial y el rendimiento de las consultas. Si ya es clave primaria, este comando no tendrá efecto.
    ```sql
    ALTER TABLE coupon_program
    ADD CONSTRAINT coupon_program_pkey PRIMARY KEY (id);
    ```
4.  **Limpiar Registros Inválidos:**
    Se eliminan registros de la tabla `coupon_program` que puedan tener un `id` nulo o cero, ya que estos registros son inválidos y pueden causar problemas durante las operaciones.
    ```sql
    DELETE FROM coupon_program WHERE id IS NULL OR id = 0;
    ```

## Actualización de Módulos Odoo

Después de realizar cambios estructurales o solucionar problemas como los descritos, es crucial actualizar ciertos módulos clave de Odoo para asegurar que el sistema reconozca los cambios, limpie cachés internas y reconstruya dependencias correctamente.

Se recomienda encarecidamente actualizar los siguientes módulos:

1.  **`base`**: Actualizar el módulo base de Odoo fuerza una recarga profunda de las estructuras del sistema, incluyendo el registro de modelos, vistas y menús. Es útil para resolver problemas de caché persistentes o inconsistencias después de cambios manuales en la base de datos.
2.  **`l10n_mx`**: El módulo principal de la localización mexicana. Actualizarlo asegura que cualquier ajuste relacionado con configuraciones, impuestos o datos maestros específicos de México esté correctamente cargado.
3.  **`l10n_mx_edi`**: El módulo encargado de la facturación electrónica (CFDI) para México. Actualizarlo es vital después de cualquier cambio que pueda afectar los reportes de factura, la generación de XML o la validación del SAT, para asegurar que las plantillas y la lógica de EDI estén al día.

La actualización se realiza típicamente desde la línea de comandos del servidor Odoo, por ejemplo:

```bash
# Reemplaza <tu_config> y <tu_db> con los valores correctos
python3 odoo-bin -c <tu_config> -d <tu_db> -u base,l10n_mx,l10n_mx_edi --stop-after-init
```

O desde la interfaz de Odoo, buscando estos módulos en la lista de Aplicaciones y usando la opción "Actualizar". 