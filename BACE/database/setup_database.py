import os
import psycopg

# Prior to running:
# Run `source BACE/database/store_database_url.sh` from command line.
# Access DATABASE_URL from heroku in command line using `heroku config:get DATABASE_URL`
# Windows Powershell: $env:DATABASE_URL=(heroku config:get DATABASE_URL)
# Bash for virtualenv: export DATABASE_URL=$(heroku config:get DATABASE_URL)
DATABASE_URL=os.environ.get('DATABASE_URL')

# True will replace the existing profiles table. 
# Make sure to save any required information from this table before deleting.
delete_profiles_table = False 

create_query = """
CREATE TABLE profiles (
    profile_id SERIAL PRIMARY KEY,
    survey_id VARCHAR(50),
    design_history float[][] DEFAULT array[]::float[][],
    answer_history INT[] DEFAULT array[]::integer[],
    thetas BYTEA
);
"""

delete_query = "DROP TABLE IF EXISTS profiles;"

prompt = "Are you sure that you want to delete the profiles table. Any unsaved data will be lost. Type 'Y' to confirm."
duplicate_table_prompt = "Profiles table already exists. Change `delete_profiles_table` flag to True in BACE/database/setup_database.py if you want to delete this table. Make sure to save any important data first."

def run_query(DATABASE_URL, delete_profiles_table = False, prompt = prompt):
    """
    Function for setting up the required table in Postgres.
    If no table exists, this will create a new profiles table in the database at DATABASE_URL.
    If a table already exists, user can delete the existing table and create a new one by specifing delete_profiles_table=True.
    """

    if (DATABASE_URL is None):
        print("The variable DATABASE_URL is not defined on your local computer. No connection will be made.")
        print("Make sure that BACE/database/store_database_url.sh was run correctly.")
        print("Alternatively, see https://devcenter.heroku.com/articles/heroku-postgresql#local-setup for further instructions.")
        return 1

    # Initial connection
    with psycopg.connect(conninfo=DATABASE_URL) as conn:

        if delete_profiles_table:

            # Confirm that user wants to delete existing profiles table.
            confirm_delete = str(input(prompt)).upper()

            if confirm_delete == "Y":

                # Delete existing table.
                conn.execute(delete_query)
                print("Deleted existing profiles table.")

            else:

                # Deletion failed for some reason.
                print("Failed to confirm delete. Exiting without changing profiles.")
                return 1
        
        try:

            # Attempt to create new profiles table.
            conn.execute(create_query)
            print('Successfully created new profiles table.')

        except psycopg.errors.DuplicateTable:

            # Raise error if profiles table exists
            print(duplicate_table_prompt)
            return 1

if __name__ == "__main__":
    run_query(DATABASE_URL, delete_profiles_table)
