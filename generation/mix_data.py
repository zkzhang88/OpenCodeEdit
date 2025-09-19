import json
import random
import yaml

def construct_data(input_lines, instr_type, model_name=None):
    constructed_data = []
    for line in input_lines:
        data = json.loads(line)
        if instr_type == 'descriptive':
            instruction = data.get('instruct_descriptive_purify', '')
        elif instr_type == 'lazy':
            instruction = data.get('instruct_lazy_purify', '')
        else:
            raise ValueError("instr_type must be either 'descriptive' or 'lazy'")

        if not instruction:
            continue  # Skip if instruction is empty

        commit = data.get('commit', '')
        if isinstance(commit, list):
            commit = ",".join(str(x) for x in commit)
        code_snippet = data.get('code_snippet', '')
        code_before = data.get('code_before_purify', '')
        code_after = data.get('code_after_purify', '')

        if model_name:
            model_instr_type = f"{model_name}_{instr_type}"
        else:
            model_instr_type = f"unknown_{instr_type}"

        constructed_entry = {
            "commit": commit,
            "code_snippet": code_snippet,
            "code_before_purify": code_before,
            "code_after_purify": code_after,
            "instruct_purify": instruction,
            "instr_type": model_instr_type
        }
        constructed_data.append(constructed_entry)
    return constructed_data

def sample_and_mix(input_files, output_file, instr_types, model_names, ratios, total_samples, random_seed=None):
    if random_seed is not None:
        random.seed(random_seed)  # Set the random seed for reproducibility

    if len(input_files) != len(ratios):
        raise ValueError("The number of input files must match the number of ratios.")
    if not abs(sum(ratios) - 1.0) < 1e-6:
        raise ValueError("Ratios must sum to 1.")

    # Use the largest remainder method to allocate sample counts and avoid rounding errors
    raw_counts = [r * total_samples for r in ratios]
    samples_per_file = [int(count) for count in raw_counts]
    remainder = total_samples - sum(samples_per_file)
    # Allocate remaining samples according to the fractional part in descending order
    if remainder > 0:
        fractional_parts = [(i, raw_counts[i] - samples_per_file[i]) for i in range(len(raw_counts))]
        fractional_parts.sort(key=lambda x: x[1], reverse=True)
        for i in range(remainder):
            samples_per_file[fractional_parts[i][0]] += 1

    constructed_data = []
    for file, num_samples, instr_type, model_name in zip(input_files, samples_per_file, instr_types, model_names):
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if num_samples > len(lines):
                raise ValueError(f"Not enough data in {file} to sample {num_samples} items.")
            sampled_lines = random.sample(lines, num_samples)

        constructed_data.extend(construct_data(sampled_lines, instr_type=instr_type, model_name=model_name))

    # Unify the commit field to ensure it is a string
    for item in constructed_data:
        commit = item.get("commit")
        if isinstance(commit, list):
            item["commit"] = ",".join(str(x) for x in commit)

    # Shuffle the constructed data
    random.shuffle(constructed_data)

    # Write the constructed data to the output file in JSONL format
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in constructed_data:
            f.write(json.dumps(item) + '\n')

if __name__ == "__main__":
    with open("mix_config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    sample_and_mix(
        input_files=config["input_files"],
        output_file=config["output_file"],
        ratios=config["ratios"],
        instr_types=config["instr_types"],
        model_names=config["model_names"],
        total_samples=config["total_samples"],
        random_seed=config.get("random_seed", None)
    )