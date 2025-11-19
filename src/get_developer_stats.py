#! /usr/bin/env python

# You will need:
# - `main.db`. Default: ./output/main.db`
# - `ai_result_backup.db`. Default: ./output/ai_result_backup.db
# - trained model file. Default: `./output/rf_model.pkl`
# - domain_labels.json and subdomain_labels.json file. 
#   Default: `./data/domain_labels.json`, `./data/subdomain_labels.json`
# - configuration file: Default: None

import requests
import argparse
import os
import time
import pandas as pd
import tqdm
import src as CoreEngine

# Override the Issue class to track the developer who closed the issue.
# Likewise, update the get issue function to fill in the developer fields
class _Issue(CoreEngine.issue_class.Issue):
    def __init__(self, number: int,
                 title: str,
                 body: str = "",
                 dev_name: str = "",
                 dev_id: str = "" ):

        super().__init__(number, title, body)
        self.dev_name = dev_name
        self.dev_id = dev_id

def get_issues(owner, repo, access_token, open_issues=True, max_count=None):
    data = []
    # GitHub API URL for fetching issues
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    # Headers for authentication
    if access_token is not None:
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }
    else:
        headers = { "Accept": "application/vnd.github.v3+json" }

    if max_count is None: page_q = 100
    else: page_q = 20

    if open_issues:
        params = {
            "state": "open",
            "per_page": page_q,  # Number of issues per page (maximum is 100)
            "page": 1,           # Page number to start fetching from
        }
    else:
        params = {
            "state": "closed",
            "per_page": page_q,  # Number of issues per page (maximum is 100)
            "page": 1,  # Page number to start fetching from
        }

    issues = []
    while True:
        # fetch issues until error. When no max_count supplied
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break

        issues_page = response.json()

        if not issues_page:
            break

        issues.extend(issues_page)

        if max_count is not None and max_count // page_q < params["page"]:
            break

        params["page"] += 1

    # Add extracted issues to dataframe
    for i in issues:
        if i["body"] is None:
            i["body"] = ""

        cur_issue = _Issue(  i["number"], i["title"],
                             i["body"],  i["user"]["login"],
                             i["user"]["id"] )
        data.append(cur_issue)
    print(f"Total issues fetched: {len(issues)}")

    return data

def get_cli_args():
    """
    Get initializing arguments from CLI.
    Returns:
        str: path to file with arguments to program
    """
    # establish positional argument capability
    arg_parser = argparse.ArgumentParser( description="Get developer expertise"
                                         "from contribution history")
    # add repo input CLI arg
    arg_parser.add_argument( "extractor_cfg_file", help="Path to JSON"
                            "configuration file")
    args = arg_parser.parse_args()
    return args.extractor_cfg_file

def get_developer_stats( repo_owner,
                         repo_name,
                         access_token, # github access token
                         openai_key,   # open ai api key
                         limit ):      # how many issues to mine

    db = CoreEngine.DatabaseManager(
        dbfile="./output/main.db",
        cachefile="./ai_result_backup.db",
        label_file="./data/subdomain_labels.json",
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

    data_out = {
        "Issue Number": [],
        "Issue Title": [],
        "Issue Body": [],
        "Is Open": [],
        "RF Predictions": [],
        "developer_name": [],
        "developer_id": [],
    }

    print('Fetching closed issues...')

    # Get closed issues
    issues = get_issues(
        owner=repo_owner,
        repo=repo_name,
        open_issues=False,
        access_token=access_token,
        max_count = limit,
    )

    print(f"Classifying {len(issues)} closed issues....")
    for issue in tqdm.tqdm(issues, leave=False):
        # issue is of type CoreEngine.Issue, issues closed.
        try:
            prediction_rf = external_rf.predict_issue(issue)
        except:
            continue

        data_out["Issue Number"].append(issue.number)
        data_out["Issue Title"].append(issue.title)
        data_out["Issue Body"].append(issue.body.replace('"', "'"))
        data_out["Is Open"].append(False)
        data_out["RF Predictions"].append(prediction_rf)

        # get developer information for each solved issue 
        data_out["developer_name"].append( issue.dev_name )
        data_out["developer_id"].append( issue.dev_id )

    data = pd.DataFrame(data=data_out)
    data["Issue Body"] = data["Issue Body"].apply(CoreEngine.classifier.clean_text)

    # # save the issues fetched, and their domain labels
    # with open(f"output/{repo_owner}_{repo_name}_issue_extract.csv", "w") as file:
    #     data.to_csv(file)

    # get the developer <--> domain  <--> frequency mapping

    df = data.explode('RF Predictions')

    df = df.groupby( ['developer_name', 'developer_id', 'RF Predictions'] ).size().reset_index(name='frequency')

    df = df.sort_values( by=[ 'developer_name', 'developer_id', 'frequency'], ascending=False )

    df.rename( columns = {'RF Predictions': 'Domain'}, inplace=True )

    # with open( f'output/{repo_owner}_{repo_name}_developer_information.csv', "w" ) as f:
    #     df.to_csv( f, index = False )

    db.close()

    return df



######## FOR USE FROM CLI #########
if __name__ == "__main__":
    cfg_path = get_cli_args()
    cfg_dict = CoreEngine.utils.read_jsonfile_into_dict(cfg_path)

    repo_owner      = cfg_dict["repo_owner"]
    repo_name       = cfg_dict["repo_name"]
    access_token    = cfg_dict["github_token"]
    openai_key      = cfg_dict["openai_key"]
    limit           = int(cfg_dict["limit"])

    df = get_developer_stats( repo_owner, repo_name, access_token, openai_key,
                             limit )

    with open( f'output/{repo_owner}_{repo_name}_developer_information.csv', "w" ) as f:
        df.to_csv( f, index = False )
