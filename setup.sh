#!/bin/bash
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    create user shellmine password 'shellmine';
    create database shellmining;
    grant all privileges on database shellmining to shellmine;
    \\connect shellmining;
    create table cmdline(
        id  bigserial primary key,
        ts  timestamp,
        cmd text[]
    );
EOSQL
