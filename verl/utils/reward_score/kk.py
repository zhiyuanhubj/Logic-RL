import re

def extract_solution(solution_str):
    """Extract the answer from the solution string."""
    # Remove everything before the first "Assistant:"
    if "Assistant:" in solution_str:
        solution_str = solution_str.split("Assistant:", 1)[1]
    elif "<|im_start|>assistant" in solution_str:
        solution_str = solution_str.split("<|im_start|>assistant", 1)[1]
    else:
        return None
    solution_str = solution_str.split('\n')[-1]

    answer_pattern = r'<answer>(.*?)</answer>'
    match = re.finditer(answer_pattern, solution_str, re.DOTALL)
    matches = list(match)
    if matches:
        final_answer = matches[-1].group(1).strip()
    else:
        final_answer = None
    return final_answer

def parse_solution_text_format(solution_text_format):
    """Parse the solution_text_format to get expected statuses."""
    expected_statuses = {}
    for line in solution_text_format.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Use regex to extract name and status
        match = re.search(r'\b([A-Za-z]+)\b.*?\b(knight|knave)\b', line, re.IGNORECASE)
        if match:
            name = match.group(1)
            status = match.group(2).lower()
            expected_statuses[name] = status
    return expected_statuses

def parse_answer(answer_text, expected_names):
    """Parse the answer text to extract predicted statuses for each name."""
    if not answer_text:
        return None
    predicted_statuses = {}
    # Check each expected name
    for name in expected_names:
        # Case-sensitive name search, case-insensitive status
        pattern = re.compile(rf'\b{re.escape(name)}\b.*?\b(knight|knave)\b', re.IGNORECASE)
        match = pattern.search(answer_text)
        if not match:
            return None  # Missing a name
        status = match.group(1).lower()
        predicted_statuses[name] = status
    return predicted_statuses

def compute_score(solution_str, ground_truth, method='strict', format_reward=1, answer_reward=1):
    """Compute the reward for the kk_logic task."""
    # Extract the expected solution from ground_truth's solution_text_format
    solution_text_format = ground_truth.get('solution_text_format', '')
    expected_statuses = parse_solution_text_format(solution_text_format)
    expected_names = list(expected_statuses.keys())  # Names derived from solution_text_format
    
    # Extract the model's answer
    answer_text = extract_solution(solution_str)
    
    # Check format: <think> before <answer>
    has_think = '<think>' in solution_str
    has_answer = '<answer>' in solution_str
    think_pos = solution_str.find('<think>')
    answer_pos = solution_str.find('<answer>')
    format_ok = has_think and has_answer and (think_pos < answer_pos)
    
    # Calculate format reward
    format_reward_value = format_reward if format_ok else -1
    
    # Calculate answer reward
    answer_reward_value = 0  # Default if format is invalid
    if format_ok and answer_text is not None:
        predicted_statuses = parse_answer(answer_text, expected_names)
        if predicted_statuses is not None and predicted_statuses == expected_statuses:
            answer_reward_value = answer_reward
        else:
            answer_reward_value = -1
    
    total_reward = format_reward_value + answer_reward_value
    return total_reward