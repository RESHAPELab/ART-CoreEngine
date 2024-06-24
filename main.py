"""Provides driver functionality for running the GitHub extractor."""

import argparse
from datetime import datetime
import glob
import os
import pickle
import sys

from dotenv import load_dotenv  # do a pip install dotenv
import pandas as pd

from src import (
    ai_taxonomy,
    database_init,
    database_manager,
    open_issue_classification as classifier,
    processing,
)
from src.repo_extractor import (
    conf,
    extractor,
    schema,
    utils,
)


def main():
    """Driver function for GitHub Repo Extractor."""
    print("Connecting to database...")
    init_db()

    cfg_dict: dict = get_user_cfg()
    cfg_obj = conf.Cfg(cfg_dict, schema.cfg_schema)
    db = database_manager.DatabaseManager()

    gh_ext = extractor.Extractor(cfg_obj)
    prs = gh_ext.get_repo_issues_data(db)

    api_labels = utils.read_jsonfile_into_dict(
        cfg_obj.get_cfg_val("api_domain_label_listing")
    )
    sub_labels = utils.read_jsonfile_into_dict(
        cfg_obj.get_cfg_val("api_subdomain_label_listing")
    )
    ai = ai_taxonomy.AICachedClassifier(api_labels, sub_labels, db)

    for pr in prs:
        print(f"\nClassifying files from PR {pr} for predictions training ")

        # Here is where ASTs and classification are done;
        # all the "heavy lifting" of the core engine
        processing.process_files(ai, db, pr)

    db.save()

    method = cfg_dict["classification_method"]

    print("\nPreparing data frame")
    df = get_prs_df(db, prs)

    if method == "gpt":
        system_message, assistant_message = classifier.generate_system_message(
            sub_labels, df
        )
        classifier.generate_gpt_messages(system_message, assistant_message, df)

        llm_classifier = classifier.fine_tune_gpt()

        # Save Model
        with open(cfg_dict["classification_model_save"], "wb") as f:
            dat = {
                "time_saved": datetime.now(),
                "model": llm_classifier,
                "type": "gpt",
            }
            pickle.dump(dat, f)
        # classifier.save_model(llm_classifier)
        print(f"Your model has been saved {llm_classifier}")

    if method == "rf":
        df = df.drop(
            columns=[
                "PR #",
                "Pull Request",
                "created_at",
                "closed_at",
                "userlogin",
                "author_name",
                "most_recent_commit",
                "filename",
                "file_commit",
                "api",
                "function_name",
                "api_domain",
                "subdomain",
            ]
        )
        df = df.dropna()

        print("\nTraining Model...")
        x_text_features, _ = classifier.extract_text_features(df)

        # Transform labels
        y_df, _ = classifier.transform_labels(df)

        # Combine features
        x_combined = classifier.create_combined_features(x_text_features)

        # Perform MLSMOTE to augment the data

        if len(prs) < 3:
            print("Too Few PRs to train! Quitting")
            return

        print("\nbalancing classes...")
        x_augmented, y_augmented = classifier.perform_mlsmote(
            x_combined, y_df, n_sample=500
        )

        print("\nTraining RF model...")
        x_combined = pd.concat([x_combined, x_augmented], axis=0)
        y_combined = pd.concat([y_df, y_augmented], axis=0)

        # Train
        clf = classifier.train_random_forest(x_combined, y_combined)

        # Save Model
        with open(cfg_dict["classification_model_save"], "wb") as f:
            dat = {
                "time_saved": datetime.now(),
                "model": clf,
                "type": "rf",
            }
            pickle.dump(dat, f)
        print(f"Your model has been saved {clf}")

    db.close()
    sys.exit()


def init_db():
    """TODO."""
    base_path: str = "./output/"
    downloads_path: str = base_path + "downloaded_files/"

    for file in glob.glob(downloads_path + "*"):
        os.remove(file)

    os.makedirs(downloads_path, exist_ok=True)
    database_init.start()

    #  def setup_db():
    #      """TODO."""
    #      database_init.populate_db_with_mining_data()
    #      database_init.setup_caches()


def get_user_cfg() -> dict:
    """
    Get path to and read from configuration file.

    :return: dict of configuration values
    :rtype: dict
    """
    cfg_path = get_cli_args()

    return utils.read_jsonfile_into_dict(cfg_path)


def get_cli_args() -> str:
    """
    Get initializing arguments from CLI.

    Returns:
        str: path to file with arguments to program
    """
    # establish positional argument capability
    arg_parser = argparse.ArgumentParser(
        description="Mines data from GitHub repositories",
    )

    # add repo input CLI arg
    arg_parser.add_argument(
        "extractor_cfg_file",
        help="Path to JSON configuration file",
    )

    return arg_parser.parse_args().extractor_cfg_file


def get_prs_df(db: database_manager.DatabaseManager, prs):
    """Todo."""
    df = db.get_df(prs)
    columns_to_convert = df.columns[15:]
    df[columns_to_convert] = df[columns_to_convert].map(lambda x: 1 if x > 0 else 0)
    df["issue text"] = df["issue text"].apply(classifier.clean_text)
    df["issue description"] = df["issue description"].apply(classifier.clean_text)
    df = classifier.filter_domains(df)

    return df


if __name__ == "__main__":
    main()
