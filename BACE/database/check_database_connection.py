import traceback
import psycopg
import os

DATABASE_URL=os.environ.get('DATABASE_URL')
    
if (DATABASE_URL is None):

    print("The variable DATABASE_URL is not defined on your local computer. No connection will be made.")
    print("Make sure that BACE/database/store_database_url.sh was run correctly.")
    print("Alternatively, see https://devcenter.heroku.com/articles/heroku-postgresql#local-setup for further instructions.")

else:

    try:

        print('Attempting connection.')

        with psycopg.connect(DATABASE_URL) as conn:
            print('Connection successful.')

    except Exception as e:
        
        print('No connection made.')
        traceback.print_exc()