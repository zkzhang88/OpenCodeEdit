import os
import json
from openai import OpenAI
import random
import datetime
import argparse
import subprocess
import time


MAX_RETRIES = 5  # 最大重试次数

# 处理每条记录并调用 API
def api_infer(input_path, output_path, recovery_file, model_name, num_completion=1, max_samples=None, output_fields=None,
                 continue_from_error=False, temperature=0.8, top_p=0.95, max_tokens=2048, save_every=1000, random_seed=None, debug=False):
    """
    从输入文件中读取记录，对每条记录调用 API 生成指导性文本，并将结果写入输出文件。
    
    Args:
        input_path (str): 输入文件路径
        output_path (str): 输出文件路径
        recovery_file (str): 恢复文件路径，用于记录未处理的记录用于出错时恢复
        model_name (str): 模型名称。请在 https://help.aliyun.com/zh/model-studio/getting-started/models 查看模型列表；
                          使用DeepSeek API 时，模型名称为 "deepseek-chat" 或 "deepseek-reasoner" 。
        num_completion (int): 每条输入数据生成的样本数量，默认为 1
        max_samples (int): 筛选的输入数据数目，默认为 None，即不限制
        output_fields (list): 输出字段列表，默认为 None，即输出所有字段
        continue_from_error (bool): 是否从上次出错的地方继续，默认为 False
        temperature (float): 温度参数，控制生成文本的多样性，默认为 0.8
        top_p (float): Top-p 参数，控制生成文本的多样性，默认为 0.95
        max_tokens (int): 生成文本的最大长度，默认为 2048
        save_every (int): 每生成多少条数据保存一次，默认为 1000
        random_seed (int): 随机种子，默认为 None
        debug (bool): 是否打印调试信息，默认为 False
    Returns:
        None
    """

    if model_name == "qwen3-32b":
        client = OpenAI(
        api_key="sk-xxxx", # Replace with your API Key
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        extra_body={"enable_thinking": False}  # 禁用思考模式
    elif model_name == "deepseek-chat":
        client = OpenAI(
        api_key="sk-xxxx", # Replace with your API Key
        base_url="https://api.deepseek.com",
        )
        extra_body={}
    else:
        raise ValueError(f"Unsupported model_name: {model_name}. Please use 'qwen3-32b' or 'deepseek-chat'.")

    # Print all the hyperparameters
    print(f"Model: {model_name}")
    print(f"Input path: {input_path}")
    print(f"Output path: {output_path}")
    print(f"Recovery path: {recovery_file}")
    print(f"Continue from error: {continue_from_error}")
    print(f"Number of completions: {num_completion}, Max samples: {max_samples}," 
          f"Temperature: {temperature}, Top-p: {top_p}, Max tokens: {max_tokens}")
    
    if continue_from_error:
        # 从临时文件中读取数据
        with open(recovery_file, 'r', encoding='utf-8') as temp_file:
            selected_lines = temp_file.readlines()
        
        # 从 output_path 中读取已经生成的数据行数
        with open(output_path, 'r', encoding='utf-8') as outfile:
            generated_lines = outfile.readlines()
            save_batch_counter = len(generated_lines)  # 从已生成的数据行数开始计数
        
    else:
        # 读取所有记录
        with open(input_path, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()

        if max_samples is not None:
            # 随机选取 m 条记录
            max_samples = min(len(lines), max_samples)  # 防止超出文件行数
            random.seed(random_seed)  # 固定随机种子，输入None则不固定种子
            selected_lines = random.sample(lines, max_samples)
        else:
            selected_lines = lines  # 选取所有记录

        # 将 selected_lines 写入临时文件，以便在出错时恢复
        with open(recovery_file, 'w', encoding='utf-8') as temp_file:
            temp_file.writelines(selected_lines)

        save_batch_counter = 0  # 计数器，用于记录生成的条数

    print(f"There have been {save_batch_counter} records saved to output file before.")

    with open(output_path, 'a', encoding='utf-8') as outfile:
        remaining_lines = selected_lines.copy() # 复制一份，用于记录剩余未处理的samples，以便在出错时恢复
        for i, line in enumerate(selected_lines):
            # 从 JSONL 读取 system 和 user 信息
            record = json.loads(line)
            system_content = record.get('system', 'You are a helpful assistant.')
            user_content_list = record.get('user', '')
            if isinstance(user_content_list, str):
                # 如果 user_content_list 是字符串，则将其转换为列表
                user_content_list = [user_content_list]

            current_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            print("\n")
            print(current_time)
            print(f"Processing input sample {i + 1} of {len(selected_lines)}")
            if debug:
                print(f"Input information:\nSystem: {system_content}\nUser: {user_content_list}")

            # 检查 user_content_list 的每个内容，如果有空的则跳过
            if any(not str(content).strip() for content in user_content_list):
                print("\033[91mWarning: One or more user content entries are empty. Skipping this record.\033[0m")
                continue

            # 调用 API
            api_busy = False  # 标记 API 是否繁忙
            for j in range(num_completion):
                input_messages = [{'role': 'system', 'content': system_content}]
                llm_response = []  # 用于存储每轮对话的 LLM 响应
                for round_k, user_input in enumerate(user_content_list):
                    input_messages.append({'role': 'user', 'content': user_input})

                    if debug:
                        print(f"Round {round_k + 1} input messages: {input_messages}")

                    # 调用 API 生成响应
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=input_messages,
                        temperature=temperature,
                        top_p=top_p,
                        max_tokens=max_tokens,
                        extra_body=extra_body
                    )

                    # 处理 API 繁忙的情况
                    if completion == "":
                        # 重新尝试5次
                        api_busy = True
                        for attempt in range(MAX_RETRIES):
                            time.sleep(10)  # 等待 10 秒后重试
                            print(f"API is busy, retrying {attempt + 1}/{MAX_RETRIES}...")
                            completion = client.chat.completions.create(
                                model=model_name,
                                messages=input_messages,
                                temperature=temperature,
                                top_p=top_p,
                                max_tokens=max_tokens,
                                extra_body={"enable_thinking": False}  # 禁用思考模式
                            )
                            if completion != "":
                                api_busy = False
                                break

                        if api_busy:
                            raise Exception("API is still busy after maximum retries. Please try again later.")
                    
                    llm_response.append(completion.choices[0].message.content)
                    input_messages.append({'role': 'assistant', 'content': completion.choices[0].message.content})  # 将 LLM 响应添加到输入消息中

                    if debug:
                        print(f"Round {round_k + 1} response: {llm_response[round_k]}")


                output_data = record.copy()  # 复制原始记录
                for k in range(len(llm_response)):
                    # 将每轮响应添加到 output_data 中
                    output_data[f'response_{k + 1}'] = llm_response[k]
                output_data['response'] = llm_response  # 所有轮响应的列表
                output_data['sample_index'] = j + 1

                # 准备输出结果
                if output_fields:
                    # 找出 output_fields 中不存在于 output_data 的字段
                    missing_fields = [key for key in output_fields if key not in output_data]

                    # 如果有缺失字段，打印警告或抛出异常
                    if missing_fields:
                        print(f"\033[91mWarning: The following fields are missing in output_data: {missing_fields}\033[0m")

                    # Retain only the fields specified in output_fields, and re-rank them by the order in output_fields
                    output_data = {key: output_data[key] for key in output_fields if key in output_data}

                if debug:
                    print(f"All fields in output_data: {list(output_data.keys())}")

                if debug:
                    if 'sample_index' in output_data:
                        print(f"sample_index: {output_data['sample_index']}\nOutput: {output_data['response']}")
                    
                # 写入结果到输出文件
                outfile.write(json.dumps(output_data, ensure_ascii=False) + '\n')
                save_batch_counter += 1  # 每写入一条生成的记录，计数器加 1

                # 每生成 save_every 条数据，保存一次文件，同时更新临时文件
                if save_batch_counter % save_every == 0:
                    outfile.flush()
                    print(f"Have saved {save_batch_counter} records to {output_path}")

                    # 保证在生成数据保存后再将 remaining_lines 写入临时文件
                    with open(recovery_file, 'w', encoding='utf-8') as temp_file:
                        temp_file.writelines(remaining_lines)
            
            # 从 remaining_lines 中删除已处理的 line
            remaining_lines.remove(line)


if __name__ == "__main__":
    # 输入和输出文件路径
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", type=str, required=True, help="Input file containing structured prompts")
    parser.add_argument("--output_file", type=str, required=True, help="Output file to save generated instructions")
    parser.add_argument("--recovery_file", type=str, required=True, help="File for recovering from error")
    parser.add_argument("--continue_from_error", action='store_true', help="Flag to continue from error")
    parser.add_argument("--temperature", type=float, default=0.8, help="Temperature for sampling")
    parser.add_argument("--top_p", type=float, default=0.95, help="Top-p for sampling")
    parser.add_argument("--max_tokens", type=int, default=2048, help="Maximum number of tokens for generation")
    parser.add_argument("--num_completion", type=int, default=1, help="Number of completions to generate for each prompt")
    parser.add_argument("--max_samples", type=int, default=None, help="Maximum number of samples to process")
    parser.add_argument("--save_every", type=int, default=20, help="Save output every n samples")
    parser.add_argument("--random_seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--debug", action='store_true', help="Enable debug mode for verbose logging")

    args = parser.parse_args()

    # model_name = "qwen2.5-coder-32b-instruct"
    model_name = "deepseek-chat"

    # 调用函数
    api_infer(
        input_path=args.input_file,
        output_path=args.output_file,
        recovery_file=args.recovery_file,
        continue_from_error=args.continue_from_error,
        model_name=model_name,
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
        num_completion=args.num_completion,
        max_samples=args.max_samples,
        save_every=args.save_every,
        random_seed=args.random_seed,
        debug=args.debug
    )
