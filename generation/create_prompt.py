import json
import random
import difflib

from prompts_for_gen import get_prompts




def create_prompt(commit_input_path, oneshot_input_path, prompt_version, prompt_output_path, 
                  min_snippet_lines=5, max_snippet_lines=15, sample_num=1, random_seed=None):
    """
    Creates a prompt for a given set of input commit lines and a one-shot input file.
    Args:
        commit_input_path (str): Path to the JSONL file, each line representing a commit with keys 'commit', 'old_contents', 'new_contents', and 'message'.
        oneshot_input_path (str): Path to the one-shot input file containing example data.
        prompt_version (str): Version of the prompt template to use. Supported versions are 'v1', 'v2', and 'v3'.
        prompt_output_path (str): Path to the output JSONL file where the filled prompts will be written.
        sample_num (int, optional): Number of samples to generate in total. Defaults to 1.
        random_seed (int, optional): Seed for random number generator to ensure reproducibility. Defaults to None.
    Returns:
        None
    """
    
    system_prompt, user_prompt_template = get_prompts(prompt_version)

    # 从 oneshot_input_path 中读取数据
    with open(oneshot_input_path, 'r', encoding='utf-8') as oneshot_file:
        oneshot_lines = oneshot_file.readlines()

    # 随机种子
    random.seed(random_seed)

    skipped_records = 0  # 初始化跳过记录计数器

    def sample_code_snippet(code):
        """
        从 code 中随机抽取一段代码片段，长度在 min_snippet_lines 和 max_snippet_lines 之间。
        """

        lines = code.splitlines()
        total_length = len(lines)

        if total_length < min_snippet_lines:
            raise ValueError(f"Code has fewer lines than the minimum snippet length {min_snippet_lines}.")

        snippet_length = random.randint(min_snippet_lines, min(max_snippet_lines, total_length))
        start_line = random.randint(0, total_length - snippet_length)
        
        snippet = '\n'.join(lines[start_line:start_line+snippet_length])
        
        return snippet
        
    with open(prompt_output_path, 'w', encoding='utf-8') as output_file:
        # 从 commit_input_path 中随机抽取代码片段
        with open(commit_input_path, 'r', encoding='utf-8') as commit_file:
            commit_lines = commit_file.readlines()
            created_prompt_num = 0  # 已创建的提示数量
            while created_prompt_num < sample_num:
                # 跳过标志
                skip_flag = False
                # 随机选取两行 commit_lines
                selected_commit_lines = random.sample(commit_lines, 2)
                commit_contents = [json.loads(l) for l in selected_commit_lines]

                # 检查内容是否为空
                for commit_data in commit_contents:
                    # 如果 old_code、new_code 或 commit_num 为空，则跳过该记录
                    if not commit_data.get('old_contents', '') or not commit_data.get('new_contents', '') or not commit_data.get('commit', ''):
                        print(f"\033[91mWarning: Missing old/new code or commit number. Skipping this record.\033[0m")
                        skip_flag = True

                if skip_flag:
                    # 有内容为空，跳过
                    skipped_records += 1
                    continue

                commit_num = [commit_data['commit'] for commit_data in commit_contents]
                commit_message = [commit_data.get('message', '') for commit_data in commit_contents]

                try:
                    code_snippet = [sample_code_snippet(commit_data['old_contents']) for commit_data in commit_contents] 
                except ValueError as e:
                    # 如果代码行数少于 min_snippet_lines，跳过该记录
                    print(f"\033[91mWarning: {e}. Skipping this record.\033[0m")
                    skipped_records += 1
                    continue

                # 随机选取一条 one shot 数据
                oneshot_data = json.loads(random.choice(oneshot_lines))

                # 填充 user_prompt_template 中的示例字段
                if prompt_version.startswith('v5'):
                    user_prompt = [user_prompt_template[0].format(
                        code_snippet_1=code_snippet[0],
                        code_snippet_2=code_snippet[1],
                        code_before_shot=oneshot_data['code_before'],
                        desc_instr_shot=oneshot_data['instruct_descriptive'],
                        lazy_instr_shot=oneshot_data['instruct_lazy']
                    ),
                    user_prompt_template[1]]
                else:
                    raise ValueError("Unsupported prompt version")

                filled_prompt = {
                    "commit": commit_num,
                    "system": system_prompt,
                    "user": user_prompt,
                    "code_snippet": code_snippet,
                    "commit_message": commit_message
                }

                output_file.write(json.dumps(filled_prompt) + '\n')

                created_prompt_num += 1

    print(f"Total skipped records: {skipped_records}")  # 打印跳过记录的总数


def create_prompt_rewrite_commit(commit_input_path, oneshot_input_path, prompt_version, prompt_output_path, shuffle=False, random_seed=None):
    system_prompt, user_prompt_template = get_prompts(prompt_version)

    skipped_records = 0  # 初始化跳过记录计数器

    # 新增：用于收集所有输出数据
    output_data = []

    # 从 oneshot_input_path 中读取数据
    with open(oneshot_input_path, 'r', encoding='utf-8') as oneshot_file:
        oneshot_lines = oneshot_file.readlines()

    with open(commit_input_path, 'r', encoding='utf-8') as commit_file:
        for line in commit_file:
            data = json.loads(line)
            commit_num = data.get('commit', '')
            old_code = data.get('old_contents', '')
            new_code = data.get('new_contents', '')
            commit_message = data.get('message', '')

            # 如果任意一个变量为空，则跳过该记录
            if not old_code:
                print(f"\033[91mWarning: Old code is empty. Skipping this record.\nCommit number: {commit_num}\033[0m")
                skipped_records += 1
                continue
            if not new_code:
                print(f"\033[91mWarning: New code is empty. Skipping this record.\nCommit number: {commit_num}\033[0m")
                skipped_records += 1
                continue
            if not commit_message:
                print(f"\033[91mWarning: Commit message is empty. Skipping this record.\nCommit number: {commit_num}\033[0m")
                skipped_records += 1
                continue

            # 随机选取一条 one shot 数据
            oneshot_data = json.loads(random.choice(oneshot_lines))

            if prompt_version.startswith('v5.9'):
                # 生成 diff
                diff = difflib.unified_diff(old_code.splitlines(), new_code.splitlines(), lineterm='')
                unified_diff = '\n'.join(diff)
                
                user_prompt = user_prompt_template[0].format(
                    code_before=old_code,
                    code_diff=unified_diff,
                    commit_message=commit_message,
                    desc_instr_shot=oneshot_data['instruct_descriptive'],
                    lazy_instr_shot=oneshot_data['instruct_lazy']
                )
            else:
                raise ValueError("Unsupported prompt version")

            filled_prompt = {
                "commit": commit_num,
                "system": system_prompt,
                "user": user_prompt,
                "old_code": old_code,
                "new_code": new_code,
                "commit_message": commit_message
            }

            # 修改：收集到 output_data
            output_data.append(json.dumps(filled_prompt))

    # shuffle 功能
    if shuffle:
        random.shuffle(output_data)

    # 写入文件
    with open(prompt_output_path, 'w', encoding='utf-8') as output_file:
        for item in output_data:
            output_file.write(item + '\n')

    print(f"Total skipped records: {skipped_records}")  # 打印跳过记录的总数


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Create prompts for code generation or commit rewriting.")
    parser.add_argument('--prompt_type', type=str, default='rewrite_commit', help="Type of prompt to create: 'code_extend' or 'rewrite_commit'")
    args = parser.parse_args()

    if args.prompt_type == 'code_extend':
        # Create prompts for code extension
        create_prompt(
            commit_input_path='data/commitpackft_python_cleaned.jsonl',
            oneshot_input_path='create_prompt/few-shot/1-shot-prompt_final_chose.jsonl',
            prompt_version='v5.1',
            prompt_output_path='data/prompts/prompt_v5_1.jsonl',
            min_snippet_lines=5,
            max_snippet_lines=15,
            sample_num=100000,
            random_seed=42
        )
    elif args.prompt_type == 'rewrite_commit':
        # Create prompts for commit rewriting
        create_prompt_rewrite_commit(
            commit_input_path='data/commitpackft_python_cleaned.jsonl',
            oneshot_input_path='create_prompt/few-shot/1-shot-prompt_final_chose.jsonl',
            prompt_version='v5.9',
            prompt_output_path='data/prompts/prompt_rewrite_commit.jsonl',
            random_seed=42
        )