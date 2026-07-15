-- Run as PostgreSQL superuser. psql variables DB_NAME/DB_USER/DB_PASSWORD are required.
\set ON_ERROR_STOP on

SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'DB_USER', :'DB_PASSWORD')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'DB_USER')
\gexec

SELECT format('ALTER ROLE %I LOGIN PASSWORD %L', :'DB_USER', :'DB_PASSWORD')
\gexec

SELECT format('CREATE DATABASE %I OWNER %I', :'DB_NAME', :'DB_USER')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'DB_NAME')
\gexec

SELECT format('ALTER DATABASE %I OWNER TO %I', :'DB_NAME', :'DB_USER')
\gexec

