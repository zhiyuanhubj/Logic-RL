# Logic R1

Success to reproduce deepseek r1 zero on 2K Logic Puzzle Dataset.

## After Rule Based RL
- **Uncertainty marking** (flagging ambiguous steps for subsequent verification)
- **Multi-path exploration** (systematically testing alternative reasoning paths)
- **Analytical backtracking** (re-examining previous statements through re-analysis)
- **Progressive summarization** (maintaining intermediate conclusions via explicit summarization steps)
- **Final-answer verification** (performing comprehensive consistency checks before output)
- **Multilingual code-switching in reasoning** (exhibiting Chinese reasoning traces despite English-only training data, with final answers maintained in English)

[Model Output Example](response.png) | [Average Output Length](mean_length.png)

## Installation
```bash
conda create -n logic python=3.9
pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu121
pip3 install vllm==0.6.3 ray
pip3 install flash-attn --no-build-isolation
pip install -e .  # For verl integration
pip install wandb IPython matplotlib
```

## Data Preparation

### Base Model Configuration
```bash
python ./examples/data_preprocess/kk.py \
    --local_dir {processed_data_path} \
    --data_path {raw_data_path}
```

### Instruct-Tuned Model Configuration
```bash
python ./examples/data_preprocess/kk.py \
    --template_type=qwen-instruct \
    --local_dir {processed_data_path} \
    --data_path {raw_data_path}
```

## Training Execution
```bash
conda activate logic
bash main_grpo.sh  # 4 A100 80G
```

## Implementation Details
- **Reward Modeling**: Customizable scoring functions implemented in `verl/utils/reward_score/kk.py`
- **Training Configuration**: Reference implementation in `scripts/train_ppo.sh`
- **Hardware Requirements**: Default 4-GPU configuration (modifiable in `kk.sh`)
- **Monitoring**: Integrated Weights & Biases logging (requires prior `wandb login`)


## Acknowledgements
[TinyZero](https://github.com/Jiayi-Pan/TinyZero).
```