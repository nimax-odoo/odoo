``` python
# First, check if the table exists and is empty
env.cr.execute("SELECT COUNT(*) FROM coupon_program")
count = env.cr.fetchone()[0]
print(f"coupon_program table exists with {count} records")

# Check if there are sale orders with references to non-existent coupon programs
env.cr.execute("""
    SELECT COUNT(*) 
    FROM sale_order 
    WHERE last_promo_id IS NOT NULL
""")
invalid_refs = env.cr.fetchone()[0]
print(f"Found {invalid_refs} sale orders with promotion references")

# Solution 1: Clean up invalid references in sale_order table
env.cr.execute("""
    UPDATE sale_order
    SET last_promo_id = NULL
    WHERE last_promo_id IS NOT NULL
""")
updated = env.cr.rowcount
print(f"Updated {updated} sale orders to remove invalid promotion references")

# Solution 2: If you prefer to keep a reference, create a dummy coupon_program
# First, get the distinct promo_ids that are referenced
env.cr.execute("""
    SELECT DISTINCT last_promo_id
    FROM sale_order
    WHERE last_promo_id IS NOT NULL
""")
referenced_promo_ids = [row[0] for row in env.cr.fetchall()]
print(f"Found {len(referenced_promo_ids)} distinct promotion IDs referenced: {referenced_promo_ids}")

# Option to create placeholder records for these missing IDs
if referenced_promo_ids:
    for promo_id in referenced_promo_ids:
        env.cr.execute("""
            INSERT INTO coupon_program (
                id, name, discount_type, discount_percentage, program_type, 
                promo_code_usage, reward_type, company_id, create_date, write_date
            ) VALUES (
                %s, %s, 'percentage', 0, 'promotion_program',
                'no_code_needed', 'discount', %s, NOW(), NOW()
            )
            ON CONFLICT (id) DO NOTHING
        """, (promo_id, f'Placeholder Program {promo_id}', env.company.id))
    print(f"Created {len(referenced_promo_ids)} placeholder coupon programs")

# Commit the changes
env.cr.commit()
print("Changes committed successfully")

# Verify the constraint is now satisfied
try:
    env.cr.execute("SELECT 1 FROM coupon_program LIMIT 1")
    print("coupon_program table is accessible")
    
    # Try to delete a promo (if any exist now)
    if referenced_promo_ids:
        # This is just a test to see if we can delete - don't actually commit this
        env.cr.execute("DELETE FROM coupon_program WHERE id = %s", (referenced_promo_ids[0],))
        env.cr.rollback()  # Roll back the test delete
        print("Test deletion succeeded - constraint issue resolved")
except Exception as e:
    print(f"Error during verification: {e}")




# First, identify if the wizard model table exists
env.cr.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'as_sale_order_promo_wizard_line'
    )
""")
table_exists = env.cr.fetchone()[0]
print(f"Wizard table exists: {table_exists}")

if table_exists:
    # Option 1: Delete all records in the wizard table (safe for transient models)
    env.cr.execute("""
        DELETE FROM as_sale_order_promo_wizard_line
    """)
    deleted_count = env.cr.rowcount
    print(f"Deleted {deleted_count} records from as_sale_order_promo_wizard_line")
    
    # Option 2: If you want to be more targeted, only delete records that reference the program being deleted
    # This requires knowing which program ID you're trying to delete
    promo_id_to_delete = 5076  # Replace with the ID you're trying to delete
    env.cr.execute("""
        DELETE FROM as_sale_order_promo_wizard_line
        WHERE sh_promo_id = %s
    """, (promo_id_to_delete,))
    targeted_deleted = env.cr.rowcount
    print(f"Deleted {targeted_deleted} wizard records referencing program ID {promo_id_to_delete}")
    
    # Option 3: As a last resort, drop the constraint (use with caution)
    env.cr.execute("""
        ALTER TABLE as_sale_order_promo_wizard_line 
        DROP CONSTRAINT IF EXISTS as_sale_order_promo_wizard_line_sh_promo_id_fkey
    """)
    print("Dropped the constraint as_sale_order_promo_wizard_line_sh_promo_id_fkey")
    
    # Option 4: Re-add constraint with CASCADE delete
    env.cr.execute("""
        ALTER TABLE as_sale_order_promo_wizard_line 
        ADD CONSTRAINT as_sale_order_promo_wizard_line_sh_promo_id_fkey
        FOREIGN KEY (sh_promo_id) REFERENCES coupon_program(id) ON DELETE CASCADE
    """)
    print("Re-added constraint with CASCADE delete option")

# Commit changes
env.cr.commit()
print("Changes committed successfully")
```

# Parches de proceso de migracion de odoo.sh

``` sql
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


ALTER TABLE res_partner 
ADD COLUMN partner_company_registry_placeholder VARCHAR;


DELETE FROM tf_history_promo 
WHERE promo_id NOT IN (SELECT id FROM coupon_program);
```


# Get cursor from env
cr = env.cr

# Create coupon_program table
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

# Add column to res_partner
cr.execute("""
    ALTER TABLE res_partner 
    ADD COLUMN partner_company_registry_placeholder VARCHAR;
""")

# Delete records from tf_history_promo
cr.execute("""
    DELETE FROM tf_history_promo 
    WHERE promo_id NOT IN (SELECT id FROM coupon_program);
""")

# Commit the transaction
env.cr.commit()