# file: data_processing.py

import os
from datasets import Dataset, load_dataset
from tqdm import tqdm
from verl.utils.hdfs_io import copy, makedirs
import argparse
import json

def make_prefix(dp, template_type):
    """
    构造 prompt，引导模型输出对公式里各个变量(如 A、B、C...)的真值赋值。
    dp['quiz'] 假设是题目，或一堆公式+问题描述。
    """
    quiz = dp['quiz']
    if template_type == 'base':
        prefix = (
            "The user asks a question, and the Assistant solves it. "
            "The assistant first thinks about the reasoning process in the mind and then provides the user "
            "with the final answer. The reasoning process and answer are enclosed within <think> </think> and "
            "<answer> </answer> tags, respectively, i.e., <think> reasoning process here </think><answer> answer here </answer>. "
            "Now the user asks you to solve a logical formula assignment problem. After thinking, when you finally reach a conclusion, "
            "clearly state the truth value of each variable within <answer> </answer> tags, for example:\n\n"
            "<answer>\n(1) A is true\n(2) B is false\n(3) C is true\n</answer>\n\n"
            f"User: {quiz}\nAssistant: <think>"
        )
    elif template_type == 'qwen-instruct':
        prefix = (
            "<|im_start|>system\n"
            "You are a helpful assistant. The assistant first thinks about the reasoning process in the mind "
            "and then provides the user with the final answer. The reasoning process and answer are enclosed "
            "within <think> </think> and <answer> </answer> tags, respectively, i.e. <think> reasoning process </think>"
            "<answer> final answer </answer>.\n"
            "Now the user has a logical formula problem. After thorough thinking, once you reach a conclusion, "
            "please list the truth value of each variable within <answer>...</answer> to satisfy the formulas, for example:\n"
            "<answer>\n(1) A is true\n(2) B is false\n...</answer>.\n"
            "<|im_end|>\n"
            "<|im_start|>user\n"
            f"{quiz}\n"
            "<|im_end|>\n"
            "<|im_start|>assistant\n"
            "<think>"
        )
    else:
        # 如果有其它模板类型，可再扩展
        prefix = f"User: {quiz}\nAssistant: <think>"
    return prefix

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--local_dir', default='/home/user/data/logic_instruct')
    parser.add_argument('--hdfs_dir', default=None)
    parser.add_argument('--data_path', default='/home/user/mem-logic/logic_data.jsonl')
    parser.add_argument('--train_size', type=int, default=900)
    parser.add_argument('--test_size', type=int, default=100)
    parser.add_argument('--template_type', type=str, default='qwen-instruct')
    
    args = parser.parse_args()
    
    data_source = 'logic_assignment'
    TRAIN_SIZE = args.train_size
    TEST_SIZE = args.test_size

    # Load custom JSONL dataset
    def gen_from_jsonl(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                yield json.loads(line)
    
    raw_dataset = Dataset.from_generator(gen_from_jsonl, gen_kwargs={'path': args.data_path})
    print("Dataset size:", len(raw_dataset))

    assert len(raw_dataset) >= TRAIN_SIZE + TEST_SIZE
    train_dataset = raw_dataset.select(range(TRAIN_SIZE))
    test_dataset = raw_dataset.select(range(TRAIN_SIZE, TRAIN_SIZE + TEST_SIZE))

    def make_map_fn(split):
        def process_fn(example, idx):
            # 构造prompt
            question = make_prefix(example, template_type=args.template_type)
            # 假设 example 里也存有 "solution_text_format" 字段，
            # 其内容形如:
            # (1) A is false
            # (2) B is false
            # (3) C is false
            # (4) D is true
            solution = {
                "solution_text_format": example['solution_text_format'],  # ground truth
                "statements": example.get('statements', [])
            }
            data = {
                "data_source": data_source,
                "prompt": [{
                    "role": "user",
                    "content": question,
                }],
                "ability": "logic",
                "reward_model": {
                    "style": "rule",
                    "ground_truth": solution
                },
                "extra_info": {
                    'split': split,
                    'index': idx,
                }
            }
            return data
        return process_fn

    train_dataset = train_dataset.map(function=make_map_fn('train'), with_indices=True)
    test_dataset = test_dataset.map(function=make_map_fn('test'), with_indices=True)

    local_dir = args.local_dir
    os.makedirs(os.path.expanduser(local_dir), exist_ok=True)

    train_dataset.to_parquet(os.path.join(local_dir, 'train.parquet'))
    test_dataset.to_parquet(os.path.join(local_dir, 'test.parquet'))

    if args.hdfs_dir is not None:
        makedirs(args.hdfs_dir)
        copy(src=local_dir, dst=args.hdfs_dir)

if __name__ == '__main__':
    main()

