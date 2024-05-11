# Survey CTO Integration Functions

def convert_design_surveycto(design, profile, request_data, split_to_rows="|", split_to_vars=":"):
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
