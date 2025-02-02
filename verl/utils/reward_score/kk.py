import re
import random

def extract_solution(solution_str):
    """Extract the answer from the solution string with logging"""   
    # 分割处理
    if "Assistant:" in solution_str:
        solution_str = solution_str.split("Assistant:", 1)[1]
        # print("[DEBUG extract_solution] 仅模型回复部分")
        # print(solution_str)
    elif "<|im_start|>assistant" in solution_str:
        solution_str = solution_str.split("<|im_start|>assistant", 1)[1]
        print("[DEBUG extract_solution] 仅模型回复部分")
    else:
        print("[DEBUG extract_solution] 未能找到模型回复")
        return None

    # 提取答案
    answer_pattern = r'<answer>(.*?)</answer>'
    matches = list(re.finditer(answer_pattern, solution_str, re.DOTALL))
    if matches:
        final_answer = matches[-1].group(1).strip()
    else:
        print("[DEBUG extract_solution] 未能提取模型conclusion")
        final_answer = None
    
    return final_answer,solution_str

def parse_solution_text_format(solution_text_format):
    """解析标准答案时打印详细信息"""
    
    expected_statuses = {}
    for idx, line in enumerate(solution_text_format.split('\n')):
        line = line.strip()
        
        match = re.search(r'\b([A-Za-z]+)\b.*?\b(knight|knave)\b', line, re.IGNORECASE)
        if match:
            name = match.group(1)
            status = match.group(2).lower()
            expected_statuses[name] = status
        else:
            print(f"[DEBUG parse_solution_text_format] 第{idx}行未匹配到有效内容")
    
    return expected_statuses

def parse_answer(answer_text, expected_names):
    """解析模型答案时打印详细信息"""
    
    predicted_statuses = {}
    print(f"[DEBUG parse_answer] 需要匹配的名字列表: {expected_names}")
    
    for name in expected_names:
        pattern = re.compile(rf'\b{re.escape(name)}\b.*?\b(knight|knave)\b', re.IGNORECASE)
        match = pattern.search(answer_text)
        if match:
            status = match.group(1).lower()
            predicted_statuses[name] = status
        else:
            print(f"[DEBUG parse_answer] 未找到{name}的身份预测")
            return None
    
    return predicted_statuses

def compute_score(solution_str, ground_truth, method='strict', format_reward=1, answer_reward=1):
    """带详细日志的评分函数"""
    # 随机打印控制（每8次打印一次）
    # do_print = random.randint(1, 8) == 1
    do_print = 1
    if do_print:
        print("\n" + "="*100)
        print("[DEBUG compute_score] 开始处理新样本")
        print(f"[DEBUG compute_score]完整对话: {solution_str}")
        print("="*50)
    # 解析标准答案
    solution_text_format = ground_truth.get('solution_text_format', '')
    print(f"Ground Truth:{solution_text_format}")
    print("="*50)
    expected_statuses = parse_solution_text_format(solution_text_format)
    expected_names = list(expected_statuses.keys())
    print(f"expected names: {expected_names}")
    

    # 提取模型答案
    answer_text,solution_str = extract_solution(solution_str)
    print(f"answer text!!!{solution_str}")
    # 格式验证
    has_think = '</think>' in solution_str
    has_answer = '<answer>' in solution_str
    think_pos = solution_str.find('</think>') #只出现一次
    answer_pos = solution_str.find('<answer>')
    format_ok = has_think and has_answer and (think_pos < answer_pos)
    
    if do_print:
        print(f"[DEBUG compute_score] 格式检查结果:")
        print(f"  - 包含</think>: {has_think}")
        print(f"  - 包含<answer>: {has_answer}")
        print(f"  - </think>位置: {think_pos}, answer位置: {answer_pos}")
        print(f"  - 格式是否有效: {format_ok}")

    # 计算奖励
    format_reward_value = format_reward if format_ok else -1
    
    answer_reward_value = 0
    if format_ok and answer_text is not None:
        predicted_statuses = parse_answer(answer_text, expected_names)
        if do_print:
            print(f"[DEBUG compute_score] 模型预测身份结果: {predicted_statuses}")
            print(f"[DEBUG compute_score] Ground truth身份结果: {expected_statuses}")
        
        if predicted_statuses == expected_statuses:
            answer_reward_value = answer_reward
            if do_print:
                print("[DEBUG compute_score] 答案完全匹配!")
        else:
            answer_reward_value = -1
            if do_print:
                print("[DEBUG compute_score] 答案不匹配")
    else:
        if do_print:
            print("[DEBUG compute_score] 格式无效或答案为空")
    
    total_reward = format_reward_value + answer_reward_value
    if do_print:
        print(f"[DEBUG compute_score] 最终奖励计算:")
        print(f"  - 格式奖励: {format_reward_value}")
        print(f"  - 答案奖励: {answer_reward_value}")
        print(f"  - 总奖励: {total_reward}")
        print("="*100 + "\n")
    
    return total_reward