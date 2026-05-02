#!/bin/bash
#SBATCH -J crossword_puzzles
#SBATCH -A ACF-UTK0011
#SBATCH --partition=campus-gpu-large,campus-gpu
#SBATCH --qos=campus-gpu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4 
#SBATCH --gpus=1
#SBATCH --array=1-6%2
#SBATCH --mem=16G
#SBATCH --time=0-06:00:00
#SBATCH --output=logs/%A_%a.out
#SBATCH --error=logs/%A_%a.err

SUBMIT_DIR=$(pwd)
JOB_NAME="crossword_puzzles"
echo "SUBMIT_DIR is: $SUBMIT_DIR"
trap 'kill $OLLAMA_PID; cp -r $SCRATCH/$JOB_NAME/data $SUBMIT_DIR/' EXIT

# Each task gets its own port to avoid conflicts between concurrent jobs
OLLAMA_PORT=$((11434 + SLURM_ARRAY_TASK_ID))

# Move to scratch directory
cd $SCRATCH
mkdir -p $JOB_NAME
mkdir -p $SCRATCH/$JOB_NAME/logs

# Copy your project files over
cp -r $SUBMIT_DIR/src $SCRATCH/$JOB_NAME/
cp $SUBMIT_DIR/data_solve_crosswords.py $SCRATCH/$JOB_NAME/
cp $SUBMIT_DIR/solve_crossword.py $SCRATCH/$JOB_NAME/
cp $SUBMIT_DIR/crosswords_configs.txt $SCRATCH/$JOB_NAME/
cp -r $SUBMIT_DIR/puz_files $SCRATCH/$JOB_NAME/
cp $SUBMIT_DIR/pyproject.toml $SCRATCH/$JOB_NAME/
cp $SUBMIT_DIR/uv.lock $SCRATCH/$JOB_NAME/

cd $SCRATCH/$JOB_NAME
mkdir -p data/solve_crosswords

# Start Ollama server in the background on this task's port
OLLAMA_HOST="127.0.0.1:${OLLAMA_PORT}" ollama serve > logs/${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}_ollama.log 2>&1 &
OLLAMA_PID=$!

# Wait for server to be ready
echo "Waiting for Ollama to start on port $OLLAMA_PORT..."
until curl -s "http://127.0.0.1:${OLLAMA_PORT}" > /dev/null; do
    sleep 1
done
echo "Ollama ready."

# Read the config line for this array task
ARGS=$(sed -n "${SLURM_ARRAY_TASK_ID}p" crosswords_configs.txt)
OLLAMA_HOST="127.0.0.1:${OLLAMA_PORT}" uv run python -u data_solve_crosswords.py $ARGS

