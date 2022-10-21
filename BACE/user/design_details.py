import numpy as np
import pandas as pd

# Base price of pen
base_price = 2

# Specify list of different characteristics that are possible
characteristics = {
    'color': {
        "label": "Ink Color",
        "values": [
            "Blue",
            "Black"          
        ],
        "description": "Color of pen's ink."
    },
    'pen_type': {
        "label": "Pen Type",
        "values": [
            "Ballpoint",
            "Fountain"
        ],
        "description": "Style of pen"
    }
}

def convert_design(design, characteristics, question_no=0, base_price=base_price):
    """
    Helper function to convert question information into Qualtrics readable format.
    Inputs:
        design: Next optimal design
        characteristics (dict): Dictionary with all possible characteristics.
        question_no (int): Question number for labeling output variables. (Useful for Qualtrics embedded data)
        base_price: Price for base pen.
    Output:
        base (dict): Dictionary object with characteristics for the base option
        treat (dict): Dictionary object with characteristics for the treated option
        design (dict): Dictionary object with design characteristics.
    """

    base = {}
    treat = {}

    # Set price values
    base["price_"+str(question_no)] = np.round(float(base_price), 2)
    treat["price_"+str(question_no)] = np.round(float(base_price + design[0]), 2)

    # Set color values
    base_color, treat_color = map_designs(design[1])
    base["color_" + str(question_no)] = characteristics["color"]["values"][base_color]
    treat["color_" + str(question_no)] = characteristics["color"]["values"][treat_color]

    # Set type values
    base_type, treat_type = map_designs(design[2])
    base["type_" + str(question_no)] = characteristics["pen_type"]["values"][base_type]
    treat["type_" + str(question_no)] = characteristics["pen_type"]["values"][treat_type]

    # Rename columns in design
    new_design = {}
    new_design["q_" + str(question_no)] = design.tolist()

    # Add question message:
    base["choice_message_" + str(question_no)] = choice_message("base", "Option A", question_no)
    treat["choice_message_" + str(question_no)] = choice_message("treat", "Option B", question_no)

    return base, treat, new_design

def map_designs(difference):

    if difference == 1:
        return 0, 1
    elif difference == -1:
        return 1, 0
    else:
        level = int(np.random.uniform() < 0.5)
        return level, level

def choice_message(option, option_title, question_no=0):

    answer_choice = (
        f'<table border="1" cellpadding="1" cellspacing="1" style="width:320px;">'
        f'<tbody><tr><td style="text-align: center;">'
        f'{option_title}'
        '</td></tr><tr><td style="text-align: center;">'
        '<strong>Price</strong><br>'
        '$${e://Field/'
        f'response.{option}.price_{question_no}'
        '}</td></tr><tr><td style="text-align: center;">'
        '<strong>Ink Color</strong><br>'
        '${e://Field/'
        f'response.{option}.color_{question_no}'
        '}</td></tr><tr><td style="text-align: center;">'
        '<strong>Pen Type</strong><br>'
        '${e://Field/'
        f'response.{option}.type_{question_no}'
        '}</td></tr></tbody></table>'
    )

    return answer_choice
