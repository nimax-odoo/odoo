def migrate(cr, version):
    """
    Propósito: Eliminar constraint de FK y limpiar registros problemáticos antes de la migración
    Parámetros:
        - cr: Cursor de la base de datos
        - version: Versión desde la que se migra
    """
    # [as_check_coupon_program_table] Verificar si existe la tabla coupon_program
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'coupon_program'
        )
    """)
    table_exists = cr.fetchone()[0]
    
    # Si la tabla no existe, la creamos
    if not table_exists:
        print("[MIGRACIÓN] La tabla coupon_program no existe. Creándola...")
        cr.execute("""
            CREATE TABLE coupon_program (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                active BOOLEAN DEFAULT TRUE,
                program_type VARCHAR,
                rule_id INTEGER,
                reward_id INTEGER,
                company_id INTEGER,
                sequence INTEGER,
                maximum_use_number INTEGER,
                create_uid INTEGER,
                create_date TIMESTAMP WITHOUT TIME ZONE,
                write_uid INTEGER,
                write_date TIMESTAMP WITHOUT TIME ZONE
            );
        """)
        print("[MIGRACIÓN] Tabla coupon_program creada correctamente.")
    
    # [as_drop_tf_history_promo_fk] Eliminando constraint de tf_history_promo
    cr.execute("""
        ALTER TABLE tf_history_promo 
        DROP CONSTRAINT IF EXISTS tf_history_promo_promo_id_fkey;
    """)
    print("[MIGRACIÓN] Constraint tf_history_promo_promo_id_fkey eliminado.")
    
    # [as_clean_tf_history_promo_records] Eliminando registros problemáticos
    cr.execute("""
        DELETE FROM tf_history_promo 
        WHERE promo_id NOT IN (SELECT id FROM coupon_program);
    """)
    deleted_count = cr.rowcount
    print(f"[MIGRACIÓN] {deleted_count} registros inválidos eliminados de tf_history_promo.")
    
    # [as_drop_sale_order_fk] Eliminando constraint de sale_order
    cr.execute("""
        ALTER TABLE sale_order 
        DROP CONSTRAINT IF EXISTS sale_order_last_promo_id_fkey;
    """)
    print("[MIGRACIÓN] Constraint sale_order_last_promo_id_fkey eliminado.")
    
    # [as_drop_wizard_line_fk] Eliminando constraint de as_sale_order_promo_wizard_line
    cr.execute("""
        ALTER TABLE as_sale_order_promo_wizard_line 
        DROP CONSTRAINT IF EXISTS as_sale_order_promo_wizard_line_sh_promo_id_fkey;
    """)
    print("[MIGRACIÓN] Constraint as_sale_order_promo_wizard_line_sh_promo_id_fkey eliminado.")
    
    # [as_create_dummy_coupon_programs_from_sale_order] Crear registros dummy para IDs faltantes en sale_order
    cr.execute("""
        SELECT DISTINCT last_promo_id
        FROM sale_order
        WHERE last_promo_id IS NOT NULL
          AND NOT EXISTS (
            SELECT 1 FROM coupon_program WHERE id = sale_order.last_promo_id
          );
    """)
    missing_ids_sale_order = [row[0] for row in cr.fetchall()]
    
    # [as_create_dummy_coupon_programs_from_wizard] Crear registros dummy para IDs faltantes en wizard
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'as_sale_order_promo_wizard_line'
        )
    """)
    wizard_table_exists = cr.fetchone()[0]
    
    missing_ids_wizard = []
    if wizard_table_exists:
        cr.execute("""
            SELECT DISTINCT sh_promo_id
            FROM as_sale_order_promo_wizard_line
            WHERE sh_promo_id IS NOT NULL
              AND NOT EXISTS (
                SELECT 1 FROM coupon_program WHERE id = as_sale_order_promo_wizard_line.sh_promo_id
              );
        """)
        missing_ids_wizard = [row[0] for row in cr.fetchall()]
        
        # Asegurar que el ID 1 está incluido (mencionado en el error)
        if 1 not in missing_ids_wizard and 1 not in missing_ids_sale_order:
            missing_ids_wizard.append(1)
            print("[MIGRACIÓN] Añadido ID 1 específicamente mencionado en el error del wizard.")
    
    # Combinar todos los IDs faltantes
    all_missing_ids = list(set(missing_ids_sale_order + missing_ids_wizard))
    
    if all_missing_ids:
        print(f"[MIGRACIÓN] Se encontraron {len(all_missing_ids)} IDs de promociones faltantes: {all_missing_ids}")
        
        # Crear registros dummy para cada ID faltante
        for promo_id in all_missing_ids:
            cr.execute("""
                INSERT INTO coupon_program (
                    id, name, active, program_type, sequence, company_id, 
                    create_date, write_date
                ) VALUES (
                    %s, %s, TRUE, 'promotion_program', 10, 1, NOW(), NOW()
                )
                ON CONFLICT (id) DO NOTHING;
            """, (promo_id, f'Promoción Migrada #{promo_id}'))
        
        print(f"[MIGRACIÓN] Creados {len(all_missing_ids)} registros dummy en coupon_program.")
    else:
        print("[MIGRACIÓN] No se encontraron IDs de promociones faltantes.")
    
    # [as_remove_invalid_studio_views] Eliminando vistas personalizadas Studio inválidas
    problematic_xmlids = [
        ('studio_customization', 'odoo_studio_default__196210e8-46f4-4b47-8813-cc46fba85226'),  # res.groups
        ('studio_customization', 'odoo_studio_default__edaa40be-4ec0-44c4-9e36-ac44297d01f7'),  # account.invoice.report
        ('studio_customization', 'odoo_studio_default__8bdfe25f-c543-4aa0-8f1c-62a58ddae5d7'),  # sale.report
        ('studio_customization', 'odoo_studio_sale_ord_03a6a22d-ba44-4933-ae9c-2a6fd6b42e08'),   # sale.order con group_discount_per_so_line
        ('studio_customization', 'default_tree_view_fo_ba3b0c9a-0502-40e2-a28f-bca5c43a5c63'),  # Vista inválida de res.groups
        ('studio_customization', 'default_tree_view_fo_eba71b22-6d7f-46f0-b71c-fd6d5056648b'),  # Vista inválida de account.invoice.report
        ('studio_customization', 'default_tree_view_fo_c108e071-2113-4a4d-9fc3-041c61ba1f20')   # Vista inválida de sale.report
    ]
    
    # Verificar si existe la tabla ir_ui_view
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'ir_ui_view'
        )
    """)
    ir_ui_view_exists = cr.fetchone()[0]
    
    if ir_ui_view_exists:
        # Eliminar vistas Studio problemáticas
        for module, name in problematic_xmlids:
            # Obtenemos el ID de la vista
            cr.execute("""
                SELECT v.id
                FROM ir_ui_view v
                JOIN ir_model_data d ON v.id = d.res_id
                WHERE d.model = 'ir.ui.view'
                  AND d.module = %s
                  AND d.name = %s;
            """, (module, name))
            
            view_ids = cr.fetchall()
            for view_id in view_ids:
                if view_id and view_id[0]:
                    # Eliminar la vista
                    cr.execute("""
                        DELETE FROM ir_ui_view
                        WHERE id = %s;
                    """, (view_id[0],))
                    
                    # Eliminar su entrada en ir_model_data
                    cr.execute("""
                        DELETE FROM ir_model_data
                        WHERE model = 'ir.ui.view'
                          AND res_id = %s;
                    """, (view_id[0],))
                    
                    print(f"[MIGRACIÓN] Eliminada vista Studio personalizada con ID {view_id[0]} (xmlid: {module}.{name}).")
        
        # También buscar y eliminar todas las vistas con errores de validación que mencionen group_discount_per_so_line
        cr.execute("""
            UPDATE ir_ui_view v
            SET active = FALSE
            FROM ir_model_data d
            WHERE v.id = d.res_id
              AND d.model = 'ir.ui.view'
              AND d.module = 'studio_customization'
              AND v.arch_db::text LIKE '%product.group_discount_per_so_line%';
        """)
        updated_count = cr.rowcount
        print(f"[MIGRACIÓN] Desactivadas {updated_count} vistas Studio adicionales con referencias obsoletas a product.group_discount_per_so_line.")
        
    # [as_fix_ms_query_not_null] Comprobar y arreglar la tabla ms_query
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'ms_query'
        )
    """)
    ms_query_exists = cr.fetchone()[0]
    
    if ms_query_exists:
        # Verificar si hay registros con valor NULL en la columna query
        cr.execute("""
            SELECT COUNT(*) FROM ms_query WHERE query IS NULL;
        """)
        null_count = cr.fetchone()[0]
        
        if null_count > 0:
            # Actualizar los registros con valores NULL
            cr.execute("""
                UPDATE ms_query SET query = '' WHERE query IS NULL;
            """)
            print(f"[MIGRACIÓN] Actualizados {null_count} registros con query NULL en tabla ms_query.")
    
    # [as_fix_duplicated_fields] Eliminar o renombrar campos Studio duplicados
    # Comprobar si existe ir_model_fields
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'ir_model_fields'
        )
    """)
    model_fields_exists = cr.fetchone()[0]
    
    if model_fields_exists:
        # Buscar los IDs de los modelos relevantes
        cr.execute("""
            SELECT id FROM ir_model WHERE model = 'sale.order'
        """)
        sale_order_model_id = cr.fetchone()
        
        if sale_order_model_id:
            sale_order_model_id = sale_order_model_id[0]
            
            # Manejar campos duplicados de "Usuario Final"
            # Buscar campos x_studio_usuario_final y x_studio_usuario_final_1
            cr.execute("""
                SELECT id, name FROM ir_model_fields 
                WHERE model_id = %s AND 
                (name = 'x_studio_usuario_final' OR name = 'x_studio_usuario_final_1')
            """, (sale_order_model_id,))
            
            duplicated_fields = cr.fetchall()
            for field_id, field_name in duplicated_fields:
                # Desactivar o renombrar el campo
                new_label = '"[OBSOLETO] Usuario Final (Studio)"'  # Formato JSON válido con comillas
                cr.execute("""
                    UPDATE ir_model_fields 
                    SET field_description = %s 
                    WHERE id = %s
                """, (new_label, field_id))
                print(f"[MIGRACIÓN] Campo {field_name} renombrado a {new_label}")
    
    # Log para confirmar la ejecución exitosa
    print("[MIGRACIÓN] Constraints eliminados y datos migrados correctamente.") 