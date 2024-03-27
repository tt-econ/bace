from datetime import datetime, timezone
import random

# Set treatment variables
def add_to_profile(profile, **kwargs):
    profile['timestamp'] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return profile

def choice_message(label, price, color, pen_type):

    price = '${:,.2f}'.format(price)

    # Create the HTML table
    html_table = f"""
        <table style="background-color: lightgray; border-collapse: collapse; border: 1px solid black;">
            <tbody>
                <tr>
                    <th style="padding: 10px"><b>{label}</b></th>
                </tr>
                <tr>
                    <td style="padding: 10px; border-top: 1px solid black"><strong>Price:</strong> {price}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-top: 1px solid black"><strong>Pen Color:</strong> {color}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-top: 1px solid black"><strong>Pen Type:</strong> {pen_type}</td>
                </tr>
            </tbody>
        </table>
    """
    return html_table

def convert_design_ab(design):
    design_ab = dict()

    # mid point of price is between 3 and 3.6
    mid_price = (random.random() * .2 + 1) * 3
    design_ab['price_a'] = mid_price - design['price_diff'] / 2
    design_ab['price_b'] = mid_price + design['price_diff'] / 2

    if design['color_diff'] == 1:
        design_ab['color_a'] = 'Black'
        design_ab['color_b'] = 'Blue'
    elif design['color_diff'] == 0:
        if random.randint(0, 1):
            design_ab['color_a'] = 'Blue'
            design_ab['color_a'] = 'Blue'
        else:
            design_ab['color_a'] = 'Black'
            design_ab['color_a'] = 'Black'
    else:
        design_ab['color_a'] = 'Blue'
        design_ab['color_b'] = 'Black'

    if design['type_diff'] == 1:
        design_ab['type_a'] = 'Ballpoint'
        design_ab['type_b'] = 'Gel'
    elif design['type_diff'] == 0:
        if random.randint(0, 1):
            design_ab['type_a'] = 'Gel'
            design_ab['type_a'] = 'Gel'
        else:
            design_ab['type_a'] = 'Ballpoint'
            design_ab['type_a'] = 'Ballpoint'
    else:
        design_ab['type_a'] = 'Gel'
        design_ab['type_b'] = 'Ballpoint'

    return design_ab

def convert_design(design, profile, request_data, choice_message=choice_message,  **kwargs):

    # Number of questions
    Q = request_data.get('question_number') or len(profile.get('design_history'))

    design_ab = convert_design_ab(design)

    output = {f'{key}_{Q}': value for key, value in design_ab.items()}

    output[f'message_0_{Q}'] = choice_message("Pen A", design_ab['price_a'], design_ab['color_a'], design_ab['type_a'])
    output[f'message_1_{Q}'] = choice_message("Pen B", design_ab['price_b'], design_ab['color_b'], design_ab['type_b'])

    return output
