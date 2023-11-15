import random
import string
from locust import HttpUser, task, between

from app.bace.user_config import answers

def random_survey_id():
    letters = string.ascii_letters
    survey_id = 'test' + ''.join(random.choice(letters) for i in range(10))
    return survey_id

class AppUser(HttpUser):

    wait_time = between(2, 4) # Wait time between questions

    def on_start(self):

        self.question_count=0

        # Generate Random Survey ID
        survey_id = random_survey_id()

        print(f'Creating survey_id {survey_id}...')
        # Create Profile and set profile_id attribute
        create_profile = self.client.post('/create_profile', json={"survey_id": survey_id})

        self.profile_id = create_profile.json()['profile_id']

        print(f"Created profile {self.profile_id}...")

        self.question_count += 1


    @task
    def update_and_choose(self):

        # Randomly selected answer.
        random_answer = random.choice(answers)

        # Prepare Json for Request Body
        json_load = {
            'profile_id': self.profile_id,
            'answer': random_answer
        }

        # Perform PUT request to /update_and_choose
        self.client.post('/update_profile', json=json_load)

        # Update question_count for AppUser
        self.question_count += 1
    
