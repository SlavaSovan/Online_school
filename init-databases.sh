#!/bin/sh

set -e


echo "=== Starting database creation ==="


create_database() {
    local db_name=$1
    local db_user=$2
    local db_pass=$3

    echo "--- Processing: $db_name ---"

    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        DO \$\$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$db_user') THEN
                CREATE USER $db_user WITH PASSWORD '$db_pass' LOGIN;
                RAISE NOTICE 'User % created', '$db_user';
            ELSE
                RAISE NOTICE 'User % already exists', '$db_user';
            END IF;
        END
        \$\$;
EOSQL


    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        SELECT 'CREATE DATABASE $db_name OWNER $db_user'
        WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db_name')\gexec
EOSQL


    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$db_name" <<-EOSQL
        ALTER DATABASE $db_name OWNER TO $db_user;
        
        -- Даем все права на базу
        GRANT ALL PRIVILEGES ON DATABASE $db_name TO $db_user;
        
        -- Даем права на схему public
        GRANT ALL ON SCHEMA public TO $db_user;
        ALTER SCHEMA public OWNER TO $db_user;
        
        -- Даем права на все будущие таблицы в public
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $db_user;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $db_user;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO $db_user;
EOSQL

    echo "Database $db_name is ready!"
    echo ""
}

create_database "$USERS_DB_NAME" "$USERS_DB_USER" "$USERS_DB_PASSWORD"
create_database "$COURSES_DB_NAME" "$COURSES_DB_USER" "$COURSES_DB_PASSWORD"
create_database "$TASKS_DB_NAME" "$TASKS_DB_USER" "$TASKS_DB_PASSWORD"

echo "=== All databases have been created successfully! ==="