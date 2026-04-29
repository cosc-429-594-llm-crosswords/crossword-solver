#!/bin/bash
#SBATCH --job-name=crossword_test1
#SBATCH --array=1-8%2          # 1 - N % j where N = number of lines in configs.txt and 2 is number of simultaneous jobs
#SBATCH --cpus-per-task=4 
#SBATCH --gres=gpu:1  
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=logs/%A_%a.out
#SBATCH --error=logs/%A_%a.err

SUBMIT_DIR=$(pwd)
trap "cp -r $SCRATCH/crossword_test1/data $SUBMIT_DIR/" EXIT

source activate my-project-name

# Each task gets its own port to avoid conflicts between concurrent jobs
OLLAMA_PORT=$((11434 + SLURM_ARRAY_TASK_ID))

# Move to scratch directory
cd $SCRATCH
mkdir -p crossword_test1

# Copy your project files over
cp -r $SUBMIT_DIR/src $SCRATCH/crossword_test1/
cp $SUBMIT_DIR/run_experiment.py $SCRATCH/crossword_test1/
cp $SUBMIT_DIR/crossword_clues.csv $SCRATCH/crossword_test1/
cp $SUBMIT_DIR/configs.txt $SCRATCH/crossword_test1/

cd $SCRATCH/crossword_test1
mkdir -p data/get_guesses_per_clue

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
ARGS=$(sed -n "${SLURM_ARRAY_TASK_ID}p" configs.txt)
OLLAMA_HOST="127.0.0.1:${OLLAMA_PORT}" uv run data_get_guesses.py $ARGS

# Shut down the Ollama server when done
kill $OLLAMA_PID
