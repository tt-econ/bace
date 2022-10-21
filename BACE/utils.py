import numpy as np
import pandas as pd
from scipy.stats import norm
import traceback

def check_thetas(theta_parameters):

    errors = []

    errors = check_keys(theta_parameters, errors)

    for theta_parameter in theta_parameters:

        # Check rvs() method
        errors = check_rvs(theta_parameter, errors)

        # Check pdf() method
        errors = check_pdf(theta_parameter, errors)

        # Check logpdf() method
        errors = check_logpdf(theta_parameter, errors)

    if len(errors) < 1:
        print("No errors detected in `theta_parameters`.")
    
    for error in errors:
        print(error)

def check_keys(theta_parameters, errors):

    param = 0
    for theta in theta_parameters:

        missing_keys = []

        try:
            name = theta["name"]
        except Exception as e:
            name = "theta_parameters[{param}]".format(param=param)
            missing_keys.append(e)

        try:
            theta["distribution_type"]
        except Exception as e:
            missing_keys.append(e)
        
        try:
            theta["distribution"]
        except Exception as e:
            missing_keys.append(e)

        if (len(missing_keys)>0):

            error = {
                "parameter": name,
                "missing_keys": missing_keys
            }

            errors.append(error)
    
        param += 1
    
    return errors

def check_rvs(theta_parameter, errors, N=100):

    # Store parameter name
    name = theta_parameter.get('name')

    try:
        
        # Attempt random sample
        theta_parameter.get("distribution").rvs(size=N)
        #print("Successfully sampled using rvs() method for parameter: {name}.".format(name=name))
        return errors

    except Exception as e:
        # Store error
        error = {
            "parameter": name,
            "method": "rvs()",
            "exception": e
        }

        errors.append(error)

        return errors

def check_pdf(theta_parameter, errors):

    # Store parameter name and check pdf for random values
    name = theta_parameter.get('name')
    x = np.random.uniform(low=-1e9, high=1e9, size=1000)

    try:
        # Attempt standard pdf
        pdf = theta_parameter.get("distribution").pdf(x)
        #print(f"Successfully used pdf() method for parameter: {name}.")

        if np.any(pdf < 0):
            
            # Define error
            error = {
                "parameter": name,
                "method": "pdf()",
                "exception": "Producing values less than 0."
            }

            errors.append(error)
        
        return errors
            
    except Exception as e:
        # Define error
        error = {
            "parameter": name,
            "method": "pdf()",
            "exception": e
        }
        errors.append(error)

        return errors

def check_logpdf(theta_parameter, errors):

    # Store parameter name and check pdf for random values
    name = theta_parameter.get('name')
    x = np.random.uniform(low=-1e9, high=1e9, size=1000)

    try:
        # Attempt standard pdf
        pdf = theta_parameter.get("distribution").pdf(x)
        #print(f"Successfully used pdf() method for parameter: {name}.")

        return errors
            
    except Exception as e:
        # Define error
        error = {
            "parameter": name,
            "method": "logpdf()",
            "exception": e
        }
        errors.append(error)

        return errors

def check_answers(answers):
    """
    This function ensures that all elements in answers are integers.
    This is required because Postgres columns must have a specified type.
    """
    # Accept int types and standard numpy int types
    accepted_types = (int, np.int32, np.int64)

    if all([isinstance(x, accepted_types) for x in answers]):
        print("No errors detected in `answers`.")
    else:
        print(f"Answers contains elements that are not integers.")
        
        for answer in answers:
            print(f"Answer: {answer}. Type {type(answer)}.")

def check_designs(generate_designs_dataframe):

    designs = generate_designs_dataframe()
    print(f"No errors detected in `generate_designs_dataframe()`. Shape of designs {designs.shape}")
    return designs

def check_likelihood(answers, thetas, designs, likelihood_pdf):
    """
    Function to check whether likelihood_pdf is producing values outside of the interval [0, 1].
    """
    flag_low = 0
    flag_high = 0

    for answer in answers:
        likelihoods = np.array([likelihood_pdf(answer, thetas, design) for _, design in designs.iterrows()])
        
        # Check if likelihood_pdf is producing values outside the interval [0, 1]
        for likelihood in likelihoods:

            if np.any(likelihood < 0):
                flag_low = 1
                
            if np.any(likelihood > 1):
                flag_high = 1

    if flag_low + flag_high == 0:
        print("No errors detected in `likelihood_pdf` for values sampled from prior distribution. All values are in the interval [0, 1].")
    else:
        print("Errors detected in likelihood_pdf.")
        if flag_low:
            print("likelihood_pdf is producing values < 0.")
        if flag_high:
            print("likelihood_pdf is producing values > 1")

    # Check whether likelihood produces errors for values outside of the prior_distribution
    sampled_thetas = pd.DataFrame(
        norm.rvs(size=thetas.shape, loc=thetas, scale=10*thetas.std()),
        columns = list(thetas.columns)
    )

    try:
        for answer in answers:
            likelihoods = np.array([likelihood_pdf(answer, sampled_thetas, design) for _, design in designs.iterrows()])
    except:
        print("""
        likelihood_pdf() producing errors after importance sampling.
        Make sure likelihood_pdf produces values in [0, 1] for all possible thetas.
        Common problems include overflow or division errors with numpy.exp and numpy.log functions.
        Traceback provided below.
        """)
        print(traceback.print_exc())

def sample_parameters(parameters, nsamples):
    """
    Produces a DataFrame containing 'nsamples' random samples for each parameter in theta_parameters

    Inputs:
        parameters (arr of dicts): Each element is an array specifying how to sample theta. Must specify:
            'name': Name of parameter
            'distribution_type': "continuous". Must be continuous for now. Placeholder for adding discrete option.
            'distribution': Distribution function that represents prior distribution. Note, any `scipy.stats` distribution satifies the method requirements. Must contain the following methods:
                `.rvs(size)`: Randomly sample `size` points.
                `.pdf(x)`: Returns pdf of observing x given the prior.
                `.logpdf(x)`: Returns logpdf of observing x given the prior.

    Returns:
        thetas (pd.DataFrame): Takes `nsamples` random samples for each parameter and forms pandas DataFrame representing draw from prior distribution.
    """

    # Generate arrays to be filled.
    thetas = []
    columns = []

    # Sample column of size nsamples for each parameter
    for theta in parameters:

        # Store parameter name
        colname = theta.get("name")

        # Randomly sample nsamples from theta["distribution"]
        random_sample = theta.get("distribution").rvs(size=nsamples)

        # Add to output
        thetas.append(random_sample)
        columns.append(colname)

    # Transpose columns and form DataFrame
    thetas = np.transpose(thetas)
    thetas = pd.DataFrame(thetas, columns=columns)

    # Return DataFrame nparameters * nsamples
    return(thetas)

def rename_cols(prefix, df):
    """
    Renames columns of a data frame by adding prefix to existing column names. Used for producing estimate outputs.
    Inputs:
        prefix (str): String to be added to existing column names
        df (DataFrame): DataFrame
    Returns:
        DataFrame with prefix added to existing column names.
    """
    column_map = {old_name: prefix + '_' + str(old_name) for old_name in df}
    return df.rename(columns=column_map).to_dict('records')[0]