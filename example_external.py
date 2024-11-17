# Example usage of how to use the core engine in other programs.
# You will need:
# the path to `main.db`. Default: ./output/main.db`
# the path to `ai_result_backup.db`. Default: ./output/ai_result_backup.db
# the path to a trained model file. Default: `./output/rf_model.pkl` (and) `./output/gpt_model.pkl` (and) `./output/gpt_combined_model.pkl`
# the path to the domain_labels.json file. Default: `./data/subdomain_labels.json`
# the path to the response_cache. This will get automatically generated if not existent.
#   This stores responses to the predict_issue() so it avoids rerunning from GPT.
# Open AI Key

# This program downloads all open and closed issues from a given repository and
# classifies them and stores result in a CSV. This is a good example of how to
# use the CoreEngine in other projects. Import CoreEngine rather than src however.

import os
import time
from dotenv import load_dotenv
import pandas as pd
import tqdm
import src as CoreEngine
from __init__ import (
    __version__,
)  # When using this in another project, this line is not needed

load_dotenv()

if __name__ == "__main__":
    db = CoreEngine.DatabaseManager(
        dbfile="./output/main.db",
        cachefile="./ai_result_backup.db",
        label_file="./data/subdomain_labels.json",
    )

    # Recommended to use os.getenv(). Look up dotenv()
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key is None:
        print("Environment variable `OPENAI_API_KEY` is not set.")
        exit()

    # Set here to extract
    repo_owner = "JabRef"
    repo_name = "JabRef"

    # Get the model (GPT)
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

    # A very simple Issue struct. Init: number, title, body
    #
    # To use/edit, just do this:
    #
    # issue = CoreEngine.Issue(...)
    # issue.number --> number
    # issue.title --> title
    # issue.body --> body

    issue = CoreEngine.Issue(
        2,
        "Database connection fails when power goes off.",
        """Hey, I noticed that when I unplug my computer, the database server on my computer stops working.
                This is definitely an issue.""",
    )

    # issue = CoreEngine.Issue(
    #     10,
    #     "Input-output operations fail during high data transfer",
    #     """When performing input-output operations with high data transfer rates, the
    #     system fails to manage the operations correctly.
    #     This issue occurs particularly when transferring data rates exceed 100MB/s.
    #     The input-output handling mechanism should be reviewed and optimized to ensure efficient and error-free
    #     data transfer, regardless of the volume and rate of data""",
    # )

    # issue = CoreEngine.Issue(
    #     10,
    #     "Graphics system failing. Window does not go into fullscreen",
    #     """When starting the program, the window fails to enter full screen and
    #     gives a message saying that the system ran out of video memory.
    #     This results in a graphics system crash.

    #     This occurs particularly when running other fullscreen programs at the same time.
    #     The graphics handling mechanism should be reviewed and optimized to ensure efficient and error-free
    #     video transfer, regardless of what other programs are utilizing video ram""",
    # )

    print("gpt: ", external_gpt.predict_issue(issue))  # Returns top 3 domains.
    print("rf: ", external_rf.predict_issue(issue))  # Returns top 3 domains.
    print(
        "gpt-combined: ", external_gpt_combined.predict_issue(issue)
    )  # Returns top 3 domains.

    # It is also possible to download a repository's open issues like this:
    # Below gets at most 100 open issues and at most 200 closed issues and classifies each one.

    exit()

    # Below is for dumping all the issues to a csv.

    # Get open issues
    issues = CoreEngine.git_helper_get_issues(
        owner=repo_owner,
        repo=repo_name,
        open_issues=True,
        access_token=None,
    )

    data_out = {
        "Issue Number": [],
        "Issue Title": [],
        "Issue Body": [],
        "Is Open": [],
        "GPT Predictions": [],
        "RF Predictions": [],
    }

    # if len(issues) > 100:
    #     issues = issues[:100]
    print(f"Classifying {len(issues)} open issues....")

    for issue in tqdm.tqdm(issues, leave=False):
        # issue is of type CoreEngine.Issue, issues opened.
        try:
            prediction_gpt = external_gpt.predict_issue(issue)
            prediction_rf = external_rf.predict_issue(issue)
            prediction_gpt_combo = external_gpt_combined.predict_issue(issue)
        except:
            continue

        data_out["Issue Number"].append(issue.number)
        data_out["Issue Title"].append(issue.title)
        data_out["Issue Body"].append(issue.body)
        data_out["Is Open"].append(True)
        data_out["GPT Predictions"].append(prediction_gpt)
        data_out["RF Predictions"].append(prediction_rf)
        data_out["GPT_COMBINED Predictions"].append(prediction_gpt_combo)

    # Get closed issues
    issues = CoreEngine.git_helper_get_issues(
        owner=repo_owner,
        repo=repo_name,
        open_issues=False,
        access_token=None,
    )

    # if len(issues) > 200:
    #     issues = issues[:200]

    print(f"Classifying {len(issues)} closed issues....")
    for issue in tqdm.tqdm(issues, leave=False):
        # issue is of type CoreEngine.Issue, issues closed.
        try:
            prediction_gpt = external_gpt.predict_issue(issue)
            prediction_rf = external_rf.predict_issue(issue)
            prediction_gpt_combo = external_gpt_combined.predict_issue(issue)
        except:
            continue

        data_out["Issue Number"].append(issue.number)
        data_out["Issue Title"].append(issue.title)
        data_out["Issue Body"].append(issue.body.replace('"', "'"))
        data_out["Is Open"].append(False)
        data_out["GPT Predictions"].append(prediction_gpt)
        data_out["RF Predictions"].append(prediction_rf)
        data_out["GPT_COMBINED Predictions"].append(prediction_gpt_combo)
    data = pd.DataFrame(data=data_out)
    data["Issue Body"] = data["Issue Body"].apply(CoreEngine.classifier.clean_text)

    with open(f"output/{repo_owner}_{repo_name}_issue_extract.csv", "w") as file:
        data.to_csv(file)

    db.close()  # always close the database when done!
