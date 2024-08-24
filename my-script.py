import os
import re

# Path to the directory containing .scss files
scss_directory = 'xmodule/assets/'

# Path to the variables file
variables_file = 'variables.txt'

# Read the variables from the variables file
with open(variables_file, 'r') as vf:
    variables = [line.strip() for line in vf.readlines() if line.strip()]


# Function to replace variables in a file
def replace_variables_in_file(file_path, variables):
    with open(file_path, 'r') as file:
        content = file.read()

    for variable in variables:
        # Regular expression pattern to detect variable usage
        variable_pattern = re.escape(variable)

        # Regex pattern to check for arithmetic operations involving the variable
        arithmetic_pattern = rf'(\({variable_pattern}\s*[\*/]\s*[0-9.]+\))|([0-9.]+\s*[\*/]\s*{variable_pattern})'

        # Find and replace arithmetic operations with `calc()`
        matches = re.findall(arithmetic_pattern, content)
        for match in matches:
            full_match = match[0] or match[1]  # Either the first or second capture group will match
            calc_expression = re.sub(variable_pattern, f'var(--{variable[1:]})', full_match)
            calc_expression = f'calc({calc_expression})'
            content = content.replace(full_match, calc_expression)

        # Standard replacement of variable usage with var()
        pattern = rf'([^:])({variable_pattern})([^a-zA-Z0-9_-]|$)'
        replacement = rf'\1var(--{variable[1:]})\3'
        content = re.sub(pattern, replacement, content)

    with open(file_path, 'w') as file:
        file.write(content)


# Walk through the directory and find all .scss files
for root, _, files in os.walk(scss_directory):
    for file in files:
        if file.endswith('.scss'):
            file_path = os.path.join(root, file)
            print(f"Processing file: {file_path}")
            replace_variables_in_file(file_path, variables)

print("Variable replacement completed.")
