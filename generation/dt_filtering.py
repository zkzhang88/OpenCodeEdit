import os
import json
import logging
from utils.statistic_funcs import filter_by_modify_lines
from utils.statistic_funcs import filter_data_by_hdp_topic_analysis

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logging.getLogger('gensim').setLevel(logging.WARNING)


def dt_filtering(jsonl_path, field_name, data_format, output_path, random_seed=None, filter_settings=None):

    base_name = os.path.splitext(os.path.basename(jsonl_path))[0]
    abs_jsonl_path = os.path.abspath(jsonl_path)
    dir_name = os.path.dirname(abs_jsonl_path)

    ### Diff Filtering
    data_list = read_jsonl(jsonl_path)
    filtered_data = filter_by_modify_lines(data_list)
    output_filename = f"{base_name}_diff_filtered.jsonl"
    instruct_gen_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(instruct_gen_dir, "filtered")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)
    write_jsonl(filtered_data, output_path)

    ### HDP Topic Filtering
    filter_data_by_hdp_topic_analysis(
        jsonl_path=output_path,
        
    )


def read_jsonl(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data

def write_jsonl(data_list, file_path):
    dir_name = os.path.dirname(file_path)
    os.makedirs(dir_name, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data_list:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

