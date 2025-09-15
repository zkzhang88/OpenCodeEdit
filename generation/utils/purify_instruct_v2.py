import json

def purify_instructions(input_file, output_file, purify_fields=["instruct_descriptive", "instruct_lazy"]):
    """
    Reads a JSONL file line by line, purifies specified string fields in each JSON object by removing leading and trailing 
    special characters (such as backticks, asterisks, hashes, and newlines), and writes the modified objects to a new JSONL file.
    For each field in `purify_fields`, a new key with the suffix '_purify' is added to the output JSON object containing the purified string.
    If a specified field is not found in a JSON object, a warning is printed.
    Args:
        input_file (str): Path to the input JSONL file.
        output_file (str): Path to the output JSONL file where purified data will be written.
        purify_fields (list of str, optional): List of field names to purify in each JSON object. 
            Defaults to ["instruct_descriptive", "instruct_lazy"].
    Returns:
        None
    """

    def purify_string(s):
        # Remove leading and trailing ``` ### or **
        s = s.lstrip('-`*#\n ')  # Remove leading --- ``` ### ** and \n
        s = s.rstrip('-`*#\n ')  # Remove trailing --- ``` ### ** and \n
        return s

    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            data = json.loads(line)
            out_data = data.copy()  # Create a copy to avoid modifying the original data
            for field in purify_fields:
                if field in data:
                    out_data[f"{field}_purify"] = purify_string(data[field])
                else:
                    print(f"\033[91mWarning: Field '{field}' not found in data: {data}\033[0m")
            outfile.write(json.dumps(out_data, ensure_ascii=False) + '\n')


if "__main__" == __name__:
    input_file = 'rewrite_commits/seperated_rewrite_commits_ds.jsonl'
    output_file = 'rewrite_commits/purified_rewrite_commits_ds.jsonl'
    purify_instructions(input_file, output_file, purify_fields=["instruct_descriptive", "instruct_lazy"])