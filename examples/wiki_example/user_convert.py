# Number of Questions -> /survey route
nquestions = 15

# Set treatment variables
def set_treatments(profile, **kwargs):
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

def convert_design(design, profile, request_data, choice_message=choice_message,  **kwargs):

    # Number of questions
    Q = request_data.get('question_number') or len(profile.get('design_history'))

    output = {f'{key}_{Q}': value for key, value in design.items()}

    output[f'message_0_{Q}'] = choice_message("Pen A", design['price_a'], design['color_a'], design['type_a'])
    output[f'message_1_{Q}'] = choice_message("Pen B", design['price_b'], design['color_b'], design['type_b'])

    return output