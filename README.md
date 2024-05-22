# ART-CoreEngine
Parser and code understanding engine 

> Please run `onClone.sh` when repo is cloned for the first time!!!!


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

> :warning: **Warning**<br>
SAVE AND BACKUP both `ai_log.csv` and `ai_cache_results.db` as this keeps track of AI artifacts. Deleting this file can result in having to redo OpenAI calls, costing money!