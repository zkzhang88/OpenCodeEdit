import json

def load_instructions_from_jsonl(file_path, field_name, data_format):
    """
    Load instruction data and corresponding 'commit' fields from a JSONL file.

    Args:
        file_path (str): Path to the JSONL file.
        field_name (str or list): Field name(s) to extract instruction content.
            - For 'sharegpt': a single field specifying the conversation list.
            - For general format: one or two field names to concatenate.
        data_format (str): Format type ("sharegpt" or other).

    Returns:
        tuple: (instructions, commits)
            - instructions (list of str): Extracted instruction texts.
            - commits (list of str): Corresponding 'commit' values.

    Raises:
        KeyError: If required fields are missing.
        ValueError: If no user message is found in 'sharegpt' format.

    Notes:
        - Each line in the JSONL file must be a valid JSON object.
        - For 'sharegpt', extracts and joins all user messages from the conversation field.
        - For general format, concatenates specified fields with a newline if two are provided.
    """
    
    instructions = []
    commits = []

    # Ensure field_name is a list
    if isinstance(field_name, str):
        field_name = [field_name]

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            # Check commit field
            if "commit" not in data:
                raise KeyError(f"'commit' field does not exist in data: {data}")
            
            # ShareGPT format processing
            if data_format == "sharegpt":
                if field_name[0] not in data:
                    raise KeyError(f"Field {field_name[0]} does not exist in data: {data}")
                user_messages = [
                    turn["content"] for turn in data[field_name[0]]
                    if turn.get("role") == "user"
                ]
                if not user_messages:
                    raise ValueError(f"No conversation with role='user' found: {data}")
                instructions.append("\n".join(user_messages))
                commits.append(data["commit"])

            # General format processing
            # Check field_name
            elif len(field_name) == 2:
                if field_name[0] not in data or field_name[1] not in data:
                    raise KeyError(f"One of the fields in {field_name} does not exist in data: {data}")
                instructions.append(f"## Code Before:\n{data[field_name[0]]}\n## Instruction:\n{data[field_name[1]]}\n## Code After:\n")
                commits.append(data["commit"])
            elif field_name[0] in data:
                instructions.append(data[field_name[0]])
                commits.append(data["commit"])
            else:
                raise KeyError(f"Field {field_name[0]} does not exist in data: {data}")
    return instructions, commits