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
                if field_n in data and ('\n' not in data[field_n] or '\u2500' in data[field_n] or data[field_n].strip().startswith('$')):
                    delete_flag = True
                    break
            if not delete_flag:
                outfile.write(json.dumps(data) + '\n')

def purify_instruct_and_code(input_file, output_file):
    base_name = 'purify_temp'
    extension = '.jsonl'
    counter = 0

    # 生成一个临时文件名，检查临时文件名是否冲突
    while True:
        purify_temp_file = f"{base_name}_{counter}{extension}"
        if not os.path.exists(purify_temp_file):
            break
        counter += 1

    # Separate instructions and code from model response
    separate_instruct(input_file=input_file, output_file=purify_temp_file)

    # 生成第二个临时文件名，检查临时文件名是否冲突
    while True:
        purify_temp_file_2 = f"{base_name}_{counter}{extension}"
        if not os.path.exists(purify_temp_file_2):
            break
        counter += 1

    # 过滤掉单行数据
    filter_singleline_data(input_file=purify_temp_file, output_file=purify_temp_file_2, field_names=['code_before', 'code_after'])

    # 生成第三个临时文件名，检查临时文件名是否冲突
    while True:
        purify_temp_file_3 = f"{base_name}_{counter}{extension}"
        if not os.path.exists(purify_temp_file_3):
            break
        counter += 1

    # 净化代码部分
    purify_code_from_jsonl(input_file=purify_temp_file_2, output_file=purify_temp_file_3, purify_fields=["code_before", "code_after"], keep_language_mark=False)

    # 净化指令部分
    purify_instructions(input_file=purify_temp_file_3, output_file=output_file, purify_fields=["instruct_descriptive", "instruct_lazy"])

    # 删除临时文件
    os.remove(purify_temp_file)
    os.remove(purify_temp_file_2)
    os.remove(purify_temp_file_3)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Purify instructions and code from a JSONL file.")
    parser.add_argument("input_file", help="Path to the input JSONL file")
    parser.add_argument("output_file", help="Path to the output JSONL file")
    args = parser.parse_args()

    purify_instruct_and_code(args.input_file, args.output_file)
