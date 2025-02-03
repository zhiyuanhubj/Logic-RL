export N_GPUS=4
export BASE_MODEL=Qwen/Qwen2.5-3B
export DATA_DIR=~/data/kk
export ROLLOUT_TP_SIZE=1
export EXPERIMENT_NAME=kk-qwen2.5-3b
export VLLM_ATTENTION_BACKEND=XFORMERS

bash ./scripts/train_ppo.sh