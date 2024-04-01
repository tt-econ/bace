from datetime import datetime, timezone

# Add variables to user's `profile` (created when `create_profile` route is called)
def add_to_profile(profile, **kwargs):
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

def convert_design(design, profile, request_data, choice_message=choice_message,  **kwargs):
    # Function to convert design for output.
    # Note: To work correctly with the native /survey route, add the html you want to save for each option to output as f'message_{answer_val}_{Q}' where Q will be populated as survey in app/app.py.

    # Number of questions
    Q = request_data.get('question_number') or len(profile.get('design_history'))

    output_design = {f'{key}_{Q}': value for key, value in design.items()}

    output_design[f'message_0_{Q}'] = choice_message("Pen A", design['price_a'], design['color_a'], design['type_a'])
    output_design[f'message_1_{Q}'] = choice_message("Pen B", design['price_b'], design['color_b'], design['type_b'])

    return output_design

# Survey CTO Integration Functions
def convert_design_surveycto(design, profile, request_data, split_to_rows = "|", split_to_vars = ":", **kwargs):
    # Function to convert design for SurveyCTO route.
    # Output produces a single string that captures the design.
    # Rows are separated by split_to_rows (default = "|")
    # Values within rows are separated by split_to_vars (default = ":")
    # E.g. output = "color:blue:black|type:gel:fountain" maps to a table in SurveyCTO of:
    #
    #       color   | blue  | black
    #       type    | gel   | fountain   
    # 
    # See BACE SurveyCTO plug-in and BACE Manual for more details.

    output = ""
    vars = ['price', 'color', 'type']

    for var in vars:
        if var == 'price':
            # Format as currency with two decimal places
            row = f"{var}{split_to_vars}${design.get(f'{var}_a'):,.2f}{split_to_vars}${design.get(f'{var}_b'):,.2f}"
        else:
            row = f"{var}{split_to_vars}{design.get(f'{var}_a')}{split_to_vars}{design.get(f'{var}_b')}"

        output += row + split_to_rows

    print(output)

    return {'output': output}

def convert_dict_to_string(obj, parent_key='', split_to_rows='|', split_to_vars=':'):
    # Function to convert a nested dictionary into a string formatted to integrate with SurveyCTO
    output = []

    for key, val in obj.items():
        # Build the full key path using underscore for nested keys
        new_key = f"{parent_key}_{key}" if parent_key else key

        if isinstance(val, dict):
            # Recursively handle nested dictionaries
            nested_output = convert_dict_to_string(val, new_key, split_to_rows, split_to_vars)
            output.append(nested_output)
        else:
            # For non-dictionary values, format them as "key:value"
            output.append(f"{new_key}{split_to_vars}{val}")

    return split_to_rows.join(output)