"""Provides driver functionality for running the GitHub extractor."""

import argparse
from datetime import datetime
import glob
import os
import pickle
import sys

import pandas as pd

import src as CoreEngine  # change to `import CoreEngine.src as CoreEngine` in submodules

from dotenv import load_dotenv
from __init__ import __version__


def main():
    """Driver function for GitHub Repo Extractor. Used to TRAIN models"""
    print("Connecting to database...")

    load_dotenv()
    init_db()

    cfg_path, skip_train = get_cli_args()
    cfg_dict = CoreEngine.utils.read_jsonfile_into_dict(cfg_path)

    cfg_obj = CoreEngine.repo_extractor.conf.Cfg(
        cfg_dict, CoreEngine.repo_extractor.schema.cfg_schema
    )

    db = CoreEngine.DatabaseManager()
    repo = db.allocate_repo(cfg_dict["repo"])

    gh_ext = CoreEngine.repo_extractor.extractor.Extractor(cfg_obj, db)
    prs = gh_ext.get_repo_issues_data(db)

    api_labels = CoreEngine.utils.read_jsonfile_into_dict(
        cfg_obj.get_cfg_val("api_domain_label_listing")
    )
    sub_labels = CoreEngine.utils.read_jsonfile_into_dict(
        cfg_obj.get_cfg_val("api_subdomain_label_listing")
    )
    ai = CoreEngine.AICachedClassifier(api_labels, sub_labels, db)

    print("Classifying APIs in files")
    for pr in prs:
        print(f"\tClassifying files from PR {pr} for predictions training ")

        # Here is where ASTs and classification are done;
        # all the "heavy lifting" of the core engine
        CoreEngine.process_files(ai, db, pr, repo)

        # CoreEngine.process_files(ai, db)  <-- Run this to process PRs from any repo!

    db.save()

    if skip_train:
        print("\nSkipping Model Training. \nDone.")
        sys.exit()

    method = cfg_dict["clf_method"]

    print("\nPreparing data frame")

    # this gets data from a specific PR from a specific Repository
    df = get_prs_df(db, prs, repo)

    # Instead, you can use this below to get ALL data from all PRs and Repos stored
    df = get_all_data(db)
    df.to_csv("output/all_data.csv")

    print("Getting data from all extracted repositories:\n")
    repos_processed = db.get_all_repos()
    for repo_process in repos_processed:
        prs = len(db.get_prs_of_repo(repo_process))

        print(
            f"\tIncluding data for: {repo_process.owner}/{repo_process.name} PRs: {prs}"
        )
    print()

    # Here is where you can do processing with the dataframe to isolate/manipulate it.
    # Or, put it in the below if statements for gpt or random forest...

    print(f"Training... {method} model")

    if method == "gpt":
        json_open = cfg_obj.get_cfg_val("gpt_jsonl_path")

        if len(prs) < 10:
            print("Too Few PRs to train! Quitting")
            exit()

        domain_message, subdomain_message = (
            CoreEngine.classifier.generate_system_message(api_labels, sub_labels, df)
        )
        CoreEngine.classifier.generate_gpt_messages(
            domain_message, subdomain_message, df, json_open
        )

        llm_classifier = CoreEngine.classifier.fine_tune_gpt(json_open)

        if llm_classifier is None:
            print(
                "Error training! See https://platform.openai.com/finetune/ for details. Exiting.."
            )
            exit()

        # Save Model
        with open(cfg_dict["clf_model_out_path"], "wb") as f:
            dat = {
                "time_saved": datetime.now(),
                "model": llm_classifier,
                "type": "gpt",
                "save_version": __version__,
            }
            pickle.dump(dat, f)
        # classifier.save_model(llm_classifier)
        print(f"Your model has been saved {llm_classifier}")

    if method == "gpt-combined":
        json_open = cfg_obj.get_cfg_val("gpt_jsonl_path")

        # Training goes here ....

        # Save Model ... keep this part.
        with open(cfg_dict["clf_model_out_path"], "wb") as f:
            dat = {
                "time_saved": datetime.now(),
                "model": llm_classifier,
                "type": "gpt-combined",
                "save_version": __version__,
            }
            pickle.dump(dat, f)
        # classifier.save_model(llm_classifier)
        print(f"Your model has been saved {llm_classifier}")

    if method == "rf":
        df = df.drop(
            columns=[
                "Repo Name",
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
        x_text_features, vx = CoreEngine.classifier.extract_text_features(df)

        # Transform labels
        y_df, _ = CoreEngine.classifier.transform_labels(df)

        # Combine features
        x_combined = CoreEngine.classifier.create_combined_features(x_text_features)

        # Get class distribution before MLSMOTE
        print("\nClass distribution before MLSMOTE:")
        class_distribution_before = y_df.sum(axis=0)
        print(class_distribution_before)

        # Perform MLSMOTE to augment the data

        if len(prs) < 3:
            print("Too Few PRs to train! Quitting")
            return

        print("\nbalancing classes...")
        x_augmented, y_augmented = CoreEngine.classifier.perform_mlsmote(
            x_combined, y_df, n_sample=500
        )

        # Get class distribution after MLSMOTE
        print("\nClass distribution after MLSMOTE:")
        y_combined = pd.concat([y_df, y_augmented], axis=0)
        class_distribution_after = y_combined.sum(axis=0)
        print(class_distribution_after)

        print("\nTraining RF model...")
        x_combined = pd.concat([x_combined, x_augmented], axis=0)
        y_combined = pd.concat([y_df, y_augmented], axis=0)

        # Train
        clf = CoreEngine.classifier.train_random_forest(x_combined, y_combined)

        # Save Model
        with open(cfg_dict["clf_model_out_path"], "wb") as f:
            dat = {
                "time_saved": datetime.now(),
                "model": clf,
                "vectorizer": vx,
                "labels": y_df,
                "type": "rf",
                "save_version": __version__,
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
    CoreEngine.database_init.start()

    #  def setup_db():
    #      """TODO."""
    #      database_init.populate_db_with_mining_data()
    #      database_init.setup_caches()


def get_cli_args() -> tuple[str, bool]:
    """
    Get initializing arguments from CLI.

    Returns:
        str: path to file with arguments to program
        bool: skip training flag
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
    arg_parser.add_argument(
        "-s",
        action="store_true",
        help="Skip training of model",
    )

    args = arg_parser.parse_args()

    return args.extractor_cfg_file, args.s


def get_all_data(db: CoreEngine.DatabaseManager) -> pd.DataFrame:
    """Get all extracted data from all Repos/PRs

    Can be used for training

    Args:
        db (CoreEngine.DatabaseManager): _description_

    Returns:
        _type_: _description_
    """
    df = db.get_df_all()
    columns_to_convert = df.columns[16:]
    df[columns_to_convert] = df[columns_to_convert].map(lambda x: 1 if x > 0 else 0)
    df["issue text"] = df["issue text"].apply(CoreEngine.classifier.clean_text)
    df["issue description"] = df["issue description"].apply(
        CoreEngine.classifier.clean_text
    )
    # df = CoreEngine.classifier.filter_domains(df) # No filtering on get_all_data

    return df


def get_prs_df(
    db: CoreEngine.DatabaseManager,
    prs: list[int],
    repo: CoreEngine.database_manager.Repository,
):
    """Get extracted data for a specific series of PRs from a given repository

    Args:
        db (CoreEngine.DatabaseManager): Database connector
        prs (list[int]): List of PR numbers to pull from
        repo (Repository): Repository to pull from

    Returns:
        pd.Dataframe: Dataframe of the extracted data.
    """
    df = db.get_df(prs, repo)
    columns_to_convert = df.columns[16:]
    df[columns_to_convert] = df[columns_to_convert].map(lambda x: 1 if x > 0 else 0)
    df["issue text"] = df["issue text"].apply(CoreEngine.classifier.clean_text)
    df["issue description"] = df["issue description"].apply(
        CoreEngine.classifier.clean_text
    )
    df = CoreEngine.classifier.filter_domains(df)

    return df


if __name__ == "__main__":
    main()
