# Example usage of how to use the core engine in other programs.
# You will need:
# the path to `main.db`. Default: ./output/main.db`
# the path to `ai_result_backup.db`. Default: ./output/ai_result_backup.db
# the path to a trained model file. Default: `./output/rf_model.pkl`
# the path to the domain_labels.json file. Default: `./data/subdomain_labels.json`
# Open AI Key

import src as CoreEngine


if __name__ == "__main__":
    db = CoreEngine.DatabaseManager(
        dbfile="./output/main.db",
        cachefile="./ai_result_backup.db",
        label_file="./data/subdomain_labels.json",
    )

    # Recommended to use os.getenv(). Look up dotenv()
    # openai_key = os.getenv("OPENAI_API_KEY")
    openai_key = "KEY"
    external = CoreEngine.External_Model_Interface(
        openai_key, db, "./output/rf_model.pkl", "./data/subdomain_labels.json"
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
        1,
        "Database connection fails when power goes off.",
        """Hey, I noticed that when I unplug my computer, the database server on my computer stops working.
                This is definitely an issue.""",
    )
    print(external.predict_issue(issue))  # Returns string of top domain.

    # It is also possible to download a repository's open issues like this:
    issues = CoreEngine.git_helper_get_open_issues(
        owner="JabRef", repo="JabRef", access_token="A Github Key"
    )  # Note, it will query GitHub for this.

    for issue in issues:
        # issue is of type CoreEngine.Issue
        print(issue.title, external.predict_issue(issue))

    db.close()  # always close the database when done!
