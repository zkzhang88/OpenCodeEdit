from utils.purify_instruct_v2 import purify_instructions
from utils.purify_code_v4 import purify_code_from_jsonl
from utils.separate_instruct import separate_instruct
import os
import json
import argparse

def filter_singleline_data(input_file, output_file, field_names):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            delete_flag = False
            data = json.loads(line)
            for field_n in field_names:
                # if field_n in data and ('\n' not in data[field_n] or data[field_n].strip().endswith('.py')):
                # If the field content does not contain a newline character, or contains special characters, or starts with $, then delete this data
                if field_n in data and ('\n' not in data[field_n] or '\u2500' in data[field_n] or data[field_n].strip().startswith('$')):
                    delete_flag = True
                    break
            if not delete_flag:
                outfile.write(json.dumps(data) + '\n')

def extract_instruct(input_file, output_file):
    """
    Processes a model response file to extract, filter, and purify instructions and code, saving the final result to an output file.
    The function performs the following steps:
    1. Separates instructions and code from the input file (model response).
    2. Filters out entries with single-line code in specified fields.
    3. Purifies code segments by removing unwanted marks.
    4. Purifies instruction segments by removing unwanted marks.
    5. Writes the processed data to the specified output file.
    6. Cleans up temporary files created during processing.
    Args:
        input_file (str): Path to the input file containing model responses.
        output_file (str): Path to the output file where purified instructions and code will be saved.
    """

    base_name = 'purify_temp'
    extension = '.jsonl'
    counter = 0

    output_dir = os.path.dirname(os.path.abspath(output_file))
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Generate a temporary file name, check for conflicts
    while True:
        purify_temp_file = f"{base_name}_{counter}{extension}"
        if not os.path.exists(purify_temp_file):
            break
        counter += 1

    # Separate instructions and code from model response
    separate_instruct(input_file=input_file, output_file=purify_temp_file)

    # Generate a second temporary file name, check for conflicts
    while True:
        purify_temp_file_2 = f"{base_name}_{counter}{extension}"
        if not os.path.exists(purify_temp_file_2):
            break
        counter += 1

    # Filter out single-line data
    filter_singleline_data(input_file=purify_temp_file, output_file=purify_temp_file_2, field_names=['code_before', 'code_after'])

    # Generate a third temporary file name, check for conflicts
    while True:
        purify_temp_file_3 = f"{base_name}_{counter}{extension}"
        if not os.path.exists(purify_temp_file_3):
            break
        counter += 1

    # Purify code part
    purify_code_from_jsonl(input_file=purify_temp_file_2, output_file=purify_temp_file_3, purify_fields=["code_before", "code_after"], keep_language_mark=False)

    # Purify instruction part
    purify_instructions(input_file=purify_temp_file_3, output_file=output_file, purify_fields=["instruct_descriptive", "instruct_lazy"])

    # Delete temporary files
    os.remove(purify_temp_file)
    os.remove(purify_temp_file_2)
    os.remove(purify_temp_file_3)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Purify instructions and code from a JSONL file.")
    parser.add_argument("input_file", help="Path to the input JSONL file")
    parser.add_argument("output_file", help="Path to the output JSONL file")
    args = parser.parse_args()

    extract_instruct(args.input_file, args.output_file)
