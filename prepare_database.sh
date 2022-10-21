#!/bin/bash

export DATABASE_URL=$(heroku config:get DATABASE_URL)
export DATABASE_CONNECTION_POOL_URL=$(heroku config:get DATABASE_CONNECTION_POOL_URL)

if [ -z "$DATABASE_URL" ]
then
    echo "\$DATABASE_URL is empty."
else
    echo "\$DATABASE_URL is set."
fi

if [ -z "$DATABASE_CONNECTION_POOL_URL" ]
then
    echo "\$DATABASE_CONNECTION_POOL_URL is empty."
else
    echo "\$DATABASE_CONNECTION_POOL_URL is set."
fi

python BACE/database/check_database_connection.py
python BACE/database/setup_database.py