from app.bace.user_config import answers, theta_params

def main():

    file = 'qualtrics/survey_template.txt'
    question_text = 'Which option do you prefer?'
    NQ=10

    # Create file and add header
    add_header(file=file)

    # Add Questions for each
    add_questions(NQ=NQ, answers=answers, file=file, question=question_text)

    # Add text to display estimates
    add_estimates(file=file)

def add_header(file):
    with open(file, mode='w') as output_file:
        output_file.write('[[AdvancedFormat]]\n\n')

def add_questions(NQ, answers, file, question):

    with open(file, mode='a') as output_file:

        for q in range(1, NQ+1):
            output_file.write(f"[[Block:BACE Question {q}]]\n")
            output_file.write(f"[[Question:MC:SingleAnswer:Horizontal]]\n")
            output_file.write(f"[[ID:BACE_q_{q}]]\n")
            output_file.write(f"{question}\n\n")
            output_file.write(f"[[AdvancedChoices]]\n")

            for i, answer in enumerate(answers):
                output_file.write(f"[[Choice:{i}]]\n")
                output_file.write(f"${{e://Field/message_{answer}_{q}}}\n")

            output_file.write(f"\n")

def add_estimates(file):

    statistics = ['mean', 'median']
    params = theta_params.keys()


    with open(file, mode='a') as output_file:
        output_file.write('[[Block: Display Estimates]]\n')
        output_file.write('[[Question:Text]]\n')
        output_file.write(f'Estimates\n\n')

        for param in params:
            for stat in statistics:
                output_file.write(f'{param} ({stat}): ${{e://Field/{param}.{stat}}}\\n')




if __name__=="__main__":
    print('Generating survey template...')
    main()