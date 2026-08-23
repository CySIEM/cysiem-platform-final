-- Creates the role/database services/assets expects (see its .env.example).
-- Additive only - does not touch any existing role/database.
-- Run as: psql -U postgres -h localhost -f scripts/setup_test_postgres.sql
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'cysiem') THEN
        CREATE ROLE cysiem WITH LOGIN PASSWORD 'cysiem';
    END IF;
END
$$;

SELECT 'CREATE DATABASE cysiem_layer3 OWNER cysiem'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'cysiem_layer3')\gexec
