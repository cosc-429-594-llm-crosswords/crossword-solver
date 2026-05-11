# crossword-solver

In this project, we aim to use large language models (LLMs) to solve the NYT mini crossword. The final algorithm uses a tree-based approach, incorporating self-consistency and external suggestions, to solve each clue on the board sequentially.

## Project Structure

Here is an overview of the project structure:

```
├── data_collection.py
├── generate_dataset.ipynb
├── graphs
│   ├── clue_graphs.ipynb
│   ├── crosswords_solutions.ipynb
│   └── ranking_crosswords_graphs.ipynb
├── issac
│   ├── crosswords_configs.txt
│   ├── data_get_guesses.py
│   ├── data_solve_crosswords.py
│   └── guesses_configs.txt
├── solve_crossword.py
├── src
│   ├── classes
│   │   ├── clue.py
│   │   ├── crossword_puzzle.py
│   │   ├── guesses.py
│   │   └── ranked_clues.py
│   ├── constants.py
│   ├── data_collection
│   │   └── download_puz_file.py
│   ├── helpers
│   │   └── sanitize_guess.py
│   └── prompts
│       ├── get_clue_difficulty_with_llm.py
│       └── get_guesses_with_self_consistency.py
├── submit_crosswords.sh
└── submit_guesses.sh
```

### Files

- `solve_crossword.py`: This file is used to solve individual crosswords and contains the main crossword solving algorithm
- `data_collection.py`: This file is used to scrape .puz files in bulk
- `generate_dataset.ipynb`: This file is used to create a CSV file with all of the individual clues used to test the algorithm
- `submit_crossword.sh`: This shell script is used to solve a crossword in bulk using a batch job on ISAAC-NG
- `submit_guesses.sh`: This shell script is used to test the algorithm's ability to generate guesses in bulk using a batch job on ISAAC-NG

### Directories

- `src/`: This directory contains the main source code for the solving algorithm, including the data structures, LLM prompts, and helper functions.
- `graphs/`: This directory contains the source code to produce the graphs used in the paper and presentation
- `issac/`: This directory contains the code to run the solving algorithm in batch jobs on the University of Tennessee’s ISAAC-NG supercomputing cluster

## Setup/Usage

To manage the project and Python dependencies, we use UV. To install UV, please follow the instructions on their [installation page](https://docs.astral.sh/uv/getting-started/installation/). To download llama 3.1 locally, please follow the instruction on the [Ollama Documentation](https://ollama.com/library/llama3.1).

1. Use the following command to download all the dependencies

```sh
uv sync
```

2. If you are in a Jupyter notebook, select the `crossword-solver` environment in the top right part of the notebook

### How to collect the crosswords

To download the crossword puzzle files in bulk, please run the following command (this may take some time to download everything):

```sh
uv run data_collection.py --outlet <crossword_outlet> --start <start_year> --end <ending_year> --username <your username> --password <password>
```

- `outlet`: The crossword provider in the xword-dl format (Ex, nty for New York Times)
- `start`: The starting year to collect crosswords from
- `end`: The ending year to collect crosswords from
- `username` (optional): Your crossword provider account’s username (only some providers require your account’s username)
- `password` (optional): Your crossword provider account’s password (only some providers require your account’s password)

Here is an example command to get all the New York Times’ mini crossword from Jan 1, 2014 to Dec 31, 2015

```sh
uv run data_collection.py --outlet ntym --start 2014 --end 2025
```

### How to solve a crossword

Run the following command to solve a crossword:

```sh
uv run solve_crossword.py --filepath <file_name> --ranking <ranking_algorithm>
```

- `filepath`: The name of the .puz crossword file in the puz_files directory that you wish to solve
- `ranking`: Which ranking algorithm to use to solve the puzzle. Options include: VAGUENESS_AND_COMPLEXITY_PLUS_KNOWN_LETTERS (default), VAGUENESS_AND_COMPLEXITY, NONE

Here is an example command to solve the New York Times mini from Jan 1, 2025

```sh
uv run solve_crossword.py --filepath nytm_2025_01_01 --ranking VAGUENESS_AND_COMPLEXITY_PLUS_KNOWN_LETTERS
```

### How to solve crosswords on ISSAC

1. Define the command line arguments for each job in the `issac/crosswords_configs.txt` file
2. Change the `#SBATCH --array=1-6%2` line in the `submit_crosswords.sh` file to the number of jobs you have (Ex. `#SBATCH --array=1-6%2` for 6 jobs, `#SBATCH --array=1-4%2` for 4 jobs)
3. Run the following command to start the job (This may take a few hours)

```shell
sbatch submit_crosswords.sh
```

### How to test guesses on ISSAC

1. Define the command line arguments for each job in the `issac/guesses_configs.txt` file
2. Change the `#SBATCH --array=1-6%2` line in the `submit_guesses.sh` file to the number of jobs you have (Ex. `#SBATCH --array=1-6%2` for 6 jobs, `#SBATCH --array=1-4%2` for 4 jobs)
3. Run the following command to start the job (This may take a few hours)

```shell
sbatch submit_guesses.sh
```

## Acknowledgements

As a part of this project, we used several key external libraries:

- [thisisparker/xword-dl](https://github.com/thisisparker/xword-dl): This open-source python utility was used to scrape `.puz` files from various news outlets (New York Times, Washington Post, USA Today)
- [alexdej/puzpy](https://github.com/alexdej/puzpy): This library was used to read data from the `.puz` file such as clues, solutions, board size, etc
- [Datamuse](https://www.datamuse.com/api/): This external API was used to provide suggestions by providing a list of words that fit the search criteria
- [Ollama](https://ollama.com/library/llama3.1): We used Ollama to run LLMs locally, specifically Llama 3.1
- [LlamaIndex](https://www.llamaindex.ai/): We used LlamaIndex as our argentic framework to call the local Ollama LLM

## AI Usage

We used to following AI tools to help with the development of this project:

- GitHub Copilot was used to refactor and simplify the crossword solving algorithm
- Claude (through the browser) to help with the batch job scripts for ISAAC
