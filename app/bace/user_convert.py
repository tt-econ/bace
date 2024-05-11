from datetime import datetime, timezone

# Add variables to user's `profile` (created when `create_profile` route is called)
def add_to_profile(profile):
    # example: add timestamp to profile
    profile['timestamp'] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return profile

def choice_message(label, price, color, pen_type):

    price = '${:,.2f}'.format(price)

    # Create the HTML table
    html_table = f"""
        <table width='300px' border='1' cellpadding='1' cellspacing='1' style='font-family: Arial, Tahoma, "Helvetica Neue", Helvetica, sans-serif; border-collapse:collapse; background-color:#eee9e7; color:black;'>
            <tbody>
                <tr>
                    <th style="text-align: center; background-color: #ded4ce;"><b>{label}</b></th>
                </tr>
                <tr>
                    <td style="text-align: center;"><em>Price:</em><br> {price}</td>
                </tr>
                <tr>
                    <td style="text-align: center;"><em>Pen Color:</em><br> {color}</td>
                </tr>
                <tr>
                    <td style="text-align: center;"><em>Pen Type:</em><br> {pen_type}</td>
                </tr>
            </tbody>
        </table>
    """
    return html_table

def convert_design(design, profile, request_data):
    # Function to convert design for output.
    # Note: To work correctly with the native /survey route,
    #    add the html you want to save for each option to output
    #    as f'message_{answer_val}_{Q}' as in the example below.

    # Number of questions
    Q = request_data.get('question_number') or len(profile.get('design_history'))

    output_design = {f'{key}_{Q}': value for key, value in design.items()}

    output_design[f'message_0_{Q}'] = choice_message("Pen A", design['price_a'], design['color_a'], design['type_a'])
    output_design[f'message_1_{Q}'] = choice_message("Pen B", design['price_b'], design['color_b'], design['type_b'])

    return output_design
