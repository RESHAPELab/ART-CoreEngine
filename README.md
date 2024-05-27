# ART-CoreEngine
By Dylan Johnson, Benjamin Carter, and Hunter Jenkins
Parser and code understanding engine 

> Please run `onClone.sh` when repo is cloned for the first time!!!!

# ART Project Core Flow:

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
    | ProgramAnalyzer.py      | <------
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
`generatedFiles directory.`
>  4. Setup the environment [See Build Instructions](#build-instructions)
>  5. Run `ProgramAnalyzer.py`
>  6. Copy the resulting `core_engine_output.csv` and `main.db`
into the predictions repository ART-Predictions.
>  7. Run the predictions program.

---

If you want to see the AI calls in real time, run 
`tail -n 100 -f generatedFiles/ai_log.csv`

---

## generatedFiles format:
- `ai_log.csv` This is the log of all AI calls done. DO NOT DELETE
- `datamining.pkl` This is the data from the datamining team. DO NOT DELETE. 
Download this from the google drive or run ART-Mining's JSONToCSV.py script
- `main.db` This is the main database file that manages all the run artifacts. Deleting this file will prompt complete environment regeneration.
- `ai_cache_results.db` This will be a backup persistent database. DO NOT DELETE.
- `downloadedFiles/*` Everything in this is temporary. It will automatically be deleted on deletion of main.db. This stores all the processed files from the program.
- `core_engine_output.csv` This is for predictions team.

> :warning: **Warning**<br>
SAVE AND BACKUP both `ai_log.csv` and `ai_result_backup.db` in the `generatedFiles` directory as this keeps track of AI artifacts. Deleting this file can result in having to redo OpenAI calls, costing money!

> :information_source: **Info**<br>
If you want to restart the analysis, delete **ONLY** the `main.db` file in the `generatedFiles` directory.

## Build Instructions:

Also, you can run it on your local machine. 

1. To do that, I would clone the repository into a temporary place (not to interfere with anything you currently have.)
2. Switch to the CombinedLargeEngine branch. Pull all changes
3. do `chmod +x onClone.sh` This is a script that sets up the new environment
4. run `./onClone.sh`
5. set the `.env` file in the root of the repository to be this: `OPENAI_API_KEY=abcdefg.....`
6. You should be good to go now: `python3 ProgramAnalyzer.py`
7. Output saved in `generatedFiles/main.db`
8. View output as CSV for the predictions team in `generatedFiles/core_engine_output.csv`

To view the output, you may have to copy `main.db` to a temp directory and then open it there. Use DB Browser from https://sqlitebrowser.org/