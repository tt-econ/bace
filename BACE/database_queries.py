from psycopg.rows import class_row
import pickle

from .models import FindProfile

def create_and_insert_profile(pool, survey_id, thetas):
    """
    Create new entry in the profiles table in the PostgreSQL Database.
    Inputs:
        db_url: database_url to create connection
        survey_id: str specifying survey id for given profile
        thetas: DataFrame with population of sampled thetas for a given profile.
    
    Returns:
        new_profile_id (int): Unique serial primary key used to access a profile in the database. 
    """

    # Specify query and values.
    query = """
    INSERT INTO profiles (survey_id, thetas)
    VALUES (%s, %s)
    RETURNING profile_id;
    """

    # Store thetas as pickled array of bytes.
    values = (survey_id, bytes(pickle.dumps(thetas)))

    # Execute query and store unique new_profile_id
    with pool.connection() as conn:
        with conn.cursor(row_factory=class_row(FindProfile)) as cur:
            new_profile_id = cur.execute(query, values, prepare=False).fetchone()

    return new_profile_id

def get_profile(pool, profile_id):
    """
    Query db_url for profile associated with profile_id.
    
    Inputs:
        db_url (str): database url for creating connection
        profile_id (int): Integer primary key for profile in database

    Returns:
        this_profile (dict) = {
            'profile_id': int,
            'survey_id': str,
            'design_history': list,
            'answer_history': list,
            'thetas': pandas.DataFrame
        }

    """

    # Specify query and values
    query = 'SELECT * FROM profiles where profile_id = %s;'
    values = (profile_id, )

    # Find element in profiles with profile_id=profile_id. Store profile.
    with pool.connection() as conn:
        this_profile = conn.execute(query, values, prepare=False).fetchone()

    # Convert output into dictionary.
    # Unpickle thetas.
    this_profile = {
        'profile_id': this_profile[0],
        'survey_id': this_profile[1],
        'design_history': this_profile[2],
        'answer_history': this_profile[3],
        'thetas': pickle.loads(this_profile[4])
    }    
    return this_profile

def update_design_history(pool, profile_id, design_history):
    """
    Update design history after selecting first design.
    
    Inputs:
        db_url (str): Database connection string
        profile_id (int): Primary key for identifying profile in database
        design_history (list): List containing history of designs.

    Returns:
        Null
    """

    # Query to update design history for existing profile entry.
    update_query = """
    UPDATE profiles
    SET design_history = %s
    WHERE profile_id = %s;
    """

    values = (list(design_history), int(profile_id))

    # Update profile.
    with pool.connection() as conn:
        conn.execute(update_query, values, prepare=False)
        print(f'Updated profile {profile_id}.')



def update_full_profile(pool, this_profile):
    """
    Update design history and thetas after filtering population and selecting next design..
    
    Inputs:
        db_url (str): Database connection string
        this_profile (dict):
            profile_id (int): Primary key for identifying profile in database
            design_history (list): List containing history of designs.
            answer_history (list): List containing history of answers.
            thetas (DataFrame): DataFrame containing population of thetas to be pickled and stored with profile.

    Returns:
        Null
    """

    # Query to update design_history, answer_history, and thetas table for existing profile.
    update_query = """
    UPDATE profiles
    SET
        design_history = %s,
        answer_history = %s,
        thetas = %s
    WHERE profile_id = %s;
    """

    # Set up query values. Pickle thetas table prior to storing.
    design_history = list(this_profile['design_history'])
    answer_history = list(this_profile['answer_history'])
    pickled_thetas = pickle.dumps(this_profile['thetas'])
    profile_id = int(this_profile['profile_id'])

    values = (
        design_history,
        answer_history, 
        pickled_thetas, 
        profile_id
    )
    
    # Execute query.
    with pool.connection() as conn:
        conn.execute(update_query, values, prepare=False)
        print(f'Updated profile {profile_id}.')

def update_final(pool, this_profile):

    """
    Update answer_history and thetas after filtering population and selecting next design.
    Performed after final update. No new design chosen.
    
    Inputs:
        db_url (str): Database connection string
        this_profile (dict):
            profile_id (int): Primary key for identifying profile in database.
            answer_history(list): List containing history of answers.
            thetas (DataFrame): DataFrame containing population of thetas to be pickled and stored with profile.
    Returns:
        null
    """

    # Query to update thetas for existing profile.
    update_query = """
    UPDATE profiles
    SET 
        answer_history = %s,
        thetas = %s
    WHERE profile_id = %s;
    """

    # Set up values. Pickle thetas prior to storing.
    answer_history = list(this_profile['answer_history'])
    pickled_thetas = pickle.dumps(this_profile['thetas'])
    profile_id = int(this_profile['profile_id'])

    values = (
        answer_history,
        pickled_thetas, 
        profile_id
    )

    # Execute query.
    with pool.connection() as conn:
        conn.execute(update_query, values, prepare=False)
        print(f'Updated profile {profile_id}.')