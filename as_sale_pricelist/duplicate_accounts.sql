-- Consulta para encontrar códigos de cuentas duplicados por compañía

-- 1. Identificar los códigos duplicados por compañía
SELECT 
    company_id, 
    code, 
    COUNT(*) AS cuenta,
    ARRAY_AGG(id) AS account_ids,
    ARRAY_AGG(name) AS account_names
FROM 
    account_account
WHERE 
    code IS NOT NULL
GROUP BY 
    company_id, code
HAVING 
    COUNT(*) > 1
ORDER BY 
    company_id, code;

-- 2. Verificar los detalles de las cuentas duplicadas
SELECT 
    id, 
    code, 
    name, 
    company_id, 
    deprecated, 
    used, 
    create_date
FROM 
    account_account
WHERE 
    (company_id, code) IN (
        SELECT 
            company_id, 
            code
        FROM 
            account_account
        GROUP BY 
            company_id, code
        HAVING 
            COUNT(*) > 1
    )
ORDER BY 
    company_id, code, id;

-- 3. Solución: Añadir sufijo numérico a las cuentas duplicadas (para compañías activas)
-- ¡ADVERTENCIA! Realiza un backup antes de ejecutar esta actualización
WITH duplicates AS (
    SELECT 
        id,
        code,
        company_id,
        ROW_NUMBER() OVER(PARTITION BY company_id, code ORDER BY id) AS rn
    FROM 
        account_account
    WHERE 
        (company_id, code) IN (
            SELECT 
                company_id, 
                code
            FROM 
                account_account
            GROUP BY 
                company_id, code
            HAVING 
                COUNT(*) > 1
        )
),
company_active AS (
    SELECT id FROM res_company WHERE active = true
)
UPDATE account_account aa
SET code = aa.code || '_' || d.rn
FROM duplicates d, company_active ca
WHERE aa.id = d.id
  AND d.rn > 1  -- Mantener el código original para el primer registro
  AND d.company_id = ca.id;  -- Solo actualizar cuentas de compañías activas

-- 4. Verificar que no queden duplicados
SELECT 
    company_id, 
    code, 
    COUNT(*) AS cuenta
FROM 
    account_account
GROUP BY 
    company_id, code
HAVING 
    COUNT(*) > 1; 