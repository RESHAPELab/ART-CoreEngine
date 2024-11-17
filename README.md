# ART-CoreEngine
Parser and code understanding engine
<br>
By Anonymous

## ART Project Overview:

1. A training and prediction engine --> CoreEngine Repository (this Repository)
2. An interactive UI that utilizes CoreEngine --> Art-UI Repository 

> See the video located in `docs/demo.mp4` to see how this works.


**This README covers the training and prediction engine aspect, the CoreEngine**  

## Core Engine Structure
There are two sides to the CoreEngine.
1. Training models, both LLM models and Random Forest models.
2. Prediction API, allows the models to be queried to classify issues.
It is the Prediction API that is called by outside projects (like the UI)

### Training models
The program uses a passed in configuration JSON file (see `/docs/repo-extractor/user/configuration_opts.md` for more information). 

The JSON file specifies the repository to extract. It also specifies the range of Issue/PRs to extract.
In training, the CoreEngine extracts all the PRs as specified in the JSON file and trains
either a Random Forest model, a single GPT model, or a combined binary classification GPT model. The model
type is specified in the JSON file. After training, it 
saves the model at the location specified in the JSON configuration.

> Training was done from 11 repositories. [See dataset document for a list of which ones](/docs/DATASETS.md)

#### Example instructions for training a model:
> Make sure poetry is installed [See here for instructions](https://python-poetry.org/docs/)
1. Run `poetry install` -- this sets up the virtual environment
2. Run `poetry run python3 -m spacy download en_core_web_md` to download the language file
3. Create a GitHub Personal Access Token to use for downloading issues from GitHub and save it in a file
4. Set up a configuration file for training like below (see [example pre-filled configuration](/input/config_example.json) for default)

5. Set an environment variable in a `.env` file with the `OPENAI_API_KEY` set to an OpenAI key
6. Place a GitHub key in a file located at `auth_path` as specified in the `config.json`. (Default: `input/mp_auth.txt`)
6. Run `poetry run python3 main.py path/to/config.json` where the json is the one set 
up from step three. This will download, analyze, and train the model. It stores the results in 
a cache, preventing repeated calls.


> If you want to see the AI calls in real time, run
> `tail -n 100 -f output/ai_log.csv`

#### output format:
- `ai_log.csv` This is the log of all AI calls done.
- `main.db` This is the main SQLite file that manages all the run artifacts. Deleting this file will prompt complete environment regeneration.
- `ai_cache_results.db` This will be a backup persistent database. Not recommended to delete, as deleting will result in replayed calls to OpenAI

> :warning: **Warning**<br>
SAVE `ai_result_backup.db` in the `output` directory as this keeps track of AI artifacts. Deleting this file can result in having to redo OpenAI calls, costing money!

> :information_source: **Info**<br>
If you want to restart the analysis from a clean state, delete **ONLY** the `main.db` file in the `output` directory. You should rarely have to delete `main.db`, except when switching repositories. `main.db` caches all extracted data to prevent re-download.


### Predicting issues from the saved models.

After a model is trained, it can be used to predict an issue's domains. 
Import `CoreEngine.src.external.External_Model_Interface` and `CoreEngine.src.database_manager.DatabaseManager` These then can be used to query the models.

Set up the database connection:
``` python
# Defaults are set to the ones implemented in the CoreEngine basic conf `config_example.json`
db = CoreEngine.DatabaseManager(
    dbfile="./output/main.db",
    cachefile="./ai_result_backup.db",
    label_file="./data/subdomain_labels.json",
)
external_gpt_combined = CoreEngine.External_Model_Interface(
openai_key,
db,
"./output/gpt_combined_model.pkl",
"./data/domain_labels.json",
"./data/subdomain_labels.json",
"./data/formatted_domain_labels.json",
f"example cache key-{repo_name}",
"./output/response_cache/",
)

external_gpt = CoreEngine.External_Model_Interface(
openai_key,
db,
"./output/gpt_model.pkl",
"./data/domain_labels.json",
"./data/subdomain_labels.json",
"./data/formatted_domain_labels.json",
f"example cache key-{repo_name}",
"./output/response_cache/",
)

# Get the model (RF)  The model is automatically detected by the model file.
external_rf = CoreEngine.External_Model_Interface(
openai_key,
db,
"./output/rf_model.pkl",
"./data/domain_labels.json",
"./data/subdomain_labels.json",
"./data/formatted_domain_labels.json",
f"example cache key-{repo_name}",
"./output/response_cache/",
)
```

Now, to predict an issue, one only must do this: (Notice `Issue` is of type `CoreEngine.src.Issue`)
``` python
issue = CoreEngine.Issue(
    1,
    "Database connection fails when power goes off.",
    """Hey, I noticed that when I unplug my computer, the database server on my computer stops working. This is definitely an issue.""",
)
print(external_rf.predict_issue(issue))
```
See an example in `example_external.py`

> Note, gpt_combined outputs in a slightly different format: a dictionary with the key of the domain and the value being a list of the 
> subdomains.


