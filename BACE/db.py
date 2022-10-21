import os
from psycopg_pool import ConnectionPool

#from BACE.user.configuration import min_connections, max_connections

DATABASE_URL = os.environ.get('DATABASE_CONNECTION_POOL_URL') or os.environ.get('DATABASE_URL')

# Connnection Pool Settings per Worker
min_connections = 1
max_connections = min_connections

connection_args = {
    # 'prepare_threshold': None
}

pool = ConnectionPool(
    DATABASE_URL,
    min_size=min_connections,
    max_size=max_connections,
    kwargs=connection_args
)

# Windows run this from powershell to test locally: 
# Windows Powershell: $env:DATABASE_URL=(heroku config:get DATABASE_URL)
# Bash for virtualenv: export DATABASE_URL=$(heroku config:get DATABASE_URL)
# Bash for virtualenv: export DATABASE_CONNECTION_POOL_URL=$(heroku config:get DATABASE_CONNECTION_POOL_URL)
        