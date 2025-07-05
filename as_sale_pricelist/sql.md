ALTER TABLE coupon_program
    ALTER COLUMN "id"                   SET DATA TYPE int4 USING "id"::int4,
    ALTER COLUMN "rule_id"              SET DATA TYPE int4 USING "rule_id"::int4,
    ALTER COLUMN "reward_id"            SET DATA TYPE int4 USING "reward_id"::int4,
    ALTER COLUMN "company_id"           SET DATA TYPE int4 USING "company_id"::int4,
    ALTER COLUMN "create_uid"           SET DATA TYPE int4 USING "create_uid"::int4,
    ALTER COLUMN "create_date"          SET DATA TYPE timestamp USING "create_date"::timestamp,
    ALTER COLUMN "as_price_list"        SET DATA TYPE int4 USING "as_price_list"::int4,
    ALTER COLUMN "PRICE_UNIT_USD"       SET DATA TYPE float8 USING "PRICE_UNIT_USD"::float8,
    ALTER COLUMN "COST_NIMAX_USD"       SET DATA TYPE float8 USING "COST_NIMAX_USD"::float8,
    ALTER COLUMN "DISCOUNT_AMOUNT_USD"  SET DATA TYPE float8 USING "DISCOUNT_AMOUNT_USD"::float8,
    ALTER COLUMN "COSTO"                SET DATA TYPE float8 USING "COSTO"::float8,
    ALTER COLUMN "as_type"              SET DATA TYPE varchar,
    ALTER COLUMN "validity_duration"    SET DATA TYPE int4 USING "validity_duration"::int4,
    ALTER COLUMN "website_id"           SET DATA TYPE int4 USING "website_id"::int4,
    ALTER COLUMN "tf_max_gifted_qty"    SET DATA TYPE float8 USING "tf_max_gifted_qty"::float8,
    ALTER COLUMN "write_uid"            SET DATA TYPE int4 USING "write_uid"::int4,
    ALTER COLUMN "name"                 SET DATA TYPE varchar,
    ALTER COLUMN "active"               SET DATA TYPE boolean USING "active"::boolean,
    ALTER COLUMN "write_date"           SET DATA TYPE timestamp USING "write_date"::timestamp,
    ALTER COLUMN "tf_gifted_qty"        SET DATA TYPE float8 USING "tf_gifted_qty"::float8,
    ALTER COLUMN "sequence"             SET DATA TYPE int4 USING "sequence"::int4,
    ALTER COLUMN "maximum_use_number"   SET DATA TYPE int4 USING "maximum_use_number"::int4,
    ALTER COLUMN "program_type"         SET DATA TYPE varchar,
    ALTER COLUMN "promo_code_usage"     SET DATA TYPE varchar,
    ALTER COLUMN "promo_code"           SET DATA TYPE varchar,
    ALTER COLUMN "promo_applicability"  SET DATA TYPE varchar;


-- Crear la secuencia (ajustada al valor más alto actual)
DO $$
DECLARE
    max_id integer;
BEGIN
    SELECT MAX("id") INTO max_id FROM coupon_program;

    -- Crear secuencia nueva
    EXECUTE 'CREATE SEQUENCE IF NOT EXISTS coupon_program_id_seq START ' || (COALESCE(max_id, 0) + 1);
END$$;




-- Setear default con la nueva secuencia
ALTER TABLE coupon_program
    ALTER COLUMN "id" SET DEFAULT nextval('coupon_program_id_seq'),
    ADD PRIMARY KEY ("id");
