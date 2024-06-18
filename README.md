# ART-CoreEngine
By Dylan Johnson, Benjamin Carter, and Hunter Jenkins
Parser and code understanding engine

> Please run `onClone.sh` when repo is cloned for the first time!!!!

## ART Project Core Flow:

```

    |-------------------------|
    |      GitHub PR's        | ---
    |-------------------------|    |
                                   |
                                   |
    |-------------------------|    |
    | Datamining JSONToCSV.py | <---
    |                         | -------
    |-------------------------|       |
                                      |  datamining.pkl Contains table of PRs and files changed
    |-------------------------|       |
    |         main.py         | <------
    |                         | -----
    |-------------------------|      |
                                     |  main.db   Contains all PRs, files changed, and AI Classifications.
                                     |      More verbose and supports SQL
    |-------------------------|      |  core_engine_output.csv   Contains all PRs
    |                         |      |      and AI Classifications as one table
    | Predictions Team        |  <---
    |-------------------------|


```

> An example flow for data training:
>  1. Mine data into the given JSON (OSL-repo-extractor)
>  2. Run JSONToCSV.py from the ART-Mining Repository
>  3. Copy the resulting `datamining.pkl` to this repository into the
`output directory.`
>  4. Setup the environment [See Build Instructions](#build-instructions)
>  5. Run `main.py`
>  6. Copy the resulting `core_engine_output.csv` and `main.db`
into the predictions repository ART-Predictions.
>  7. Run the predictions program.

---

If you want to see the AI calls in real time, run
`tail -n 100 -f output/ai_log.csv`

---

## output format:
- `ai_log.csv` This is the log of all AI calls done. DO NOT DELETE
- `datamining.pkl` This is the data from the datamining team. DO NOT DELETE.
Download this from the google drive or run ART-Mining's JSONToCSV.py script
- `main.db` This is the main database file that manages all the run artifacts. Deleting this file will prompt complete environment regeneration.
- `ai_cache_results.db` This will be a backup persistent database. DO NOT DELETE.
- `downloadedFiles/*` Everything in this is temporary. It will automatically be deleted on deletion of main.db. This stores all the processed files from the program.
- `core_engine_output.csv` This is for predictions team.

> :warning: **Warning**<br>
SAVE AND BACKUP both `ai_log.csv` and `ai_result_backup.db` in the `output` directory as this keeps track of AI artifacts. Deleting this file can result in having to redo OpenAI calls, costing money!

> :information_source: **Info**<br>
If you want to restart the analysis, delete **ONLY** the `main.db` file in the `output` directory.

## Build Instructions:

`ART-CoreEngine` can be run on your local machine:

1. Clone the repository
1. Execute `chmod +x onClone.sh` to allow for running the `onClone.sh` script
1. Execute `./onClone.sh` to set up the new environment
1. Place your OpenAI API key in the project's `.env` file: `OPENAI_API_KEY=abcdefg.....`
1. Install all project dependencies into a new virtual environment: `poetry install --no-root`
1. Run the project through this virtual environment by executing `poetry run python ProgramAnalyzer.py`

- After running the program, outputs will be saved in `generatedFiles/main.db`
- You may view output as CSV for the predictions team in `generatedFiles/core_engine_output.csv`.
- To view the output, you may have to copy `main.db` to a temp directory and then open it there. Use DB Browser from https://sqlitebrowser.org/.
