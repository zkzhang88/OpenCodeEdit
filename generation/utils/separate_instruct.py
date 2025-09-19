import json

def separate_instruct(input_file, output_file, check_missing=False):
    count_missing = 0
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            data = json.loads(line)
            response_1 = data.get("response_1", "")
            response_2 = data.get("response_2", "")
            user = data.get("user", "")
            commit_num = data.get("commit", "")
            
            # Extracting new code, descriptive and lazy instructs
            # check if the response contains the instructs
            old_code_marks = ["### [Program Before Edit]", "[Program Before Edit]", "### Program Before Edit"]
            old_code = any(instr in response_1 for instr in old_code_marks)
            descriptive_marks = ["### [Descriptive]", "[Descriptive]", "### Descriptive"]
            descriptive = any(instr in response_1 for instr in descriptive_marks)
            lazy_marks = ["### [Lazy]", "[Lazy]", "### Lazy"]
            lazy = any(instr in response_1 for instr in lazy_marks)
            end_marks = ["###", "---", "[Program Before Edit]", "```"]

            new_code_marks = ["### [Program After Edit]", "[Program After Edit]", "### Program After Edit"]
            new_code = any(instr in response_2 for instr in new_code_marks)

            if not old_code or not new_code or not descriptive or not lazy:
                print("\033[91mMissing instructs in the response!!!\033[0m")
                count_missing += 1
                if check_missing:
                    with open('missing_instructs.jsonl', 'a', encoding='utf-8') as missing_file:
                        missing_file.write(json.dumps(data) + '\n')
                continue

            # Extracting the old_code, instructs and new_code
            old_code_content = ""
            new_code_content = ""
            descriptive_content = ""
            lazy_content = ""

            if old_code:
                start = max((response_1.find(mark) + len(mark) for mark in old_code_marks if mark in response_1), default=-1)
                if start == -1:
                    continue

                end = min((response_1.find(mark) for mark in descriptive_marks if mark in response_1), default=-1)
                if end == -1:
                    continue

                old_code_content = response_1[start:end].strip()
                if old_code_content.endswith("### "):
                    old_code_content = old_code_content[:-4].strip()

            if descriptive:
                start = max((response_1.find(mark) + len(mark) for mark in descriptive_marks if mark in response_1), default=-1)
                if start == -1:
                    continue
                end = min((response_1.find(mark) for mark in lazy_marks if mark in response_1), default=-1)
                if end == -1:
                    continue
                descriptive_content = response_1[start:end].strip()
                if descriptive_content.endswith("### "):
                    descriptive_content = descriptive_content[:-4].strip()

            if lazy:
                start = max((response_1.find(mark) + len(mark) for mark in lazy_marks if mark in response_1), default=-1)
                if start == -1:
                    continue
                end = min((response_1.find(mark, start) for mark in end_marks if mark in response_1[start:]), default=-1)
                if end == -1:
                    end = len(response_1)
                lazy_content = response_1[start:end].strip()

            if new_code:
                start = max((response_2.find(mark) + len(mark) for mark in new_code_marks if mark in response_2), default=-1)
                if start == -1:
                    continue
                new_code_content = response_2[start:].strip()

            # Check if any of the extracted contents are empty
            if not new_code_content or not descriptive_content or not lazy_content:
                print("\033[91mError: One or more instructs are empty!\033[0m")
                count_missing += 1
                if check_missing:
                    with open('missing_instructs.jsonl', 'a', encoding='utf-8') as missing_file:
                        missing_file.write(json.dumps(data) + '\n')
                continue


            separated_data = {
                "commit": commit_num,
                "code_snippet": data.get("code_snippet", []),
                "code_before": old_code_content,
                "code_after": new_code_content,
                "instruct_descriptive": descriptive_content,
                "instruct_lazy": lazy_content
            }
            
            outfile.write(json.dumps(separated_data) + '\n')

    print(f"Seperation finished, with {count_missing} missing instructs.")
