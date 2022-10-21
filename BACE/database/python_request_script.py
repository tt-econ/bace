import requests
import random
import json

# Specify your application's name.
app_name = "protected-savannah-15694"

print(f"Running test for application with name: {app_name}")

url_base = f"https://{app_name}.herokuapp.com/standard/"
survey_id = "test123"

header = {
    'Content-Type': 'application/json'
}

# Attempt to connect to base url to confirm connection is working.
status_code = requests.get(f"https://{app_name}.herokuapp.com/").status_code
assert status_code == 200, f"""
Is {app_name} the name of your application? If not, make sure that `app_name` is specified correctly in the file 'BACE/database/python_request_script.py'. 
If `app_name` is correct, make sure that at least one dyno is up and running using `heroku ps:scale web=1`.
"""

# Get Request to random_design
print('Random Design...')
url_random = url_base + "random_design"

random_design = requests.request("GET", url_random, headers=header)
print(random_design.json())

# Create Profile
print('Creating profile...')
url_create = url_base + "create_profile"

payload_create = json.dumps({
    "survey_id": survey_id
})

new_profile = requests.request("POST", url_create, headers=header, data=payload_create)
new_profile = new_profile.json()
print(new_profile)

# Store profile_id
profile_id = new_profile['profile_id']
print(f'profile_id={profile_id}')

# First Design
print('Obtaining first design...')

url_first = url_base + "first_design"

payload_first = json.dumps({
    "profile_id": profile_id
})

first_design = requests.request("PUT", url_first, headers=header, data=payload_first)
first_design = first_design.json()
print(f'First design: {first_design}')

# Update and choose next design
print('Update and choose next design...')

url_next = url_base + "update_and_choose"

payload_next = json.dumps({
    "profile_id": profile_id,
    "answer": random.getrandbits(1)
})

next_design = requests.request("PUT", url_next, headers=header, data=payload_next)
next_design = next_design.json()
print(f'Next design: {next_design}')

# Update and return estimates
print('Update and return estimates...')

url_return = url_base + "update_and_return_estimates"

payload_return = json.dumps({
    "profile_id": profile_id,
    "answer": random.getrandbits(1)
})

estimates = requests.request("PUT", url_return, headers=header, data=payload_return)
estimates = estimates.json()
print(f'Estimates: {estimates}')
