"""Provides driver functionality for running the GitHub extractor."""

import argparse
from datetime import datetime
import glob
import os
import pickle
import sys

import pandas as pd

import src as CoreEngine


def main():
    """Driver function for GitHub Repo Extractor."""
    print("Connecting to database...")
    init_db()

    cfg_dict: dict = get_user_cfg()
    cfg_obj = CoreEngine.repo_extractor.conf.Cfg(
        cfg_dict, CoreEngine.configuration_schema.cfg_schema
    )
    db = CoreEngine.DatabaseManager()

    gh_ext = CoreEngine.repo_extractor.extractor.Extractor(cfg_obj)
    prs = gh_ext.get_repo_issues_data(db)

    api_labels = CoreEngine.utils.read_jsonfile_into_dict(
        cfg_obj.get_cfg_val("api_domain_label_listing")
    )
    sub_labels = CoreEngine.utils.read_jsonfile_into_dict(
        cfg_obj.get_cfg_val("api_subdomain_label_listing")
    )
    ai = CoreEngine.AICachedClassifier(api_labels, sub_labels, db)

    for pr in prs:
        print(f"\nClassifying files from PR {pr} for predictions training ")

        # Here is where ASTs and classification are done;
        # all the "heavy lifting" of the core engine
        CoreEngine.process_files(ai, db, pr)

    db.save()

    method = cfg_dict["classification_method"]

    print("\nPreparing data frame")
    df = get_prs_df(db, prs)

    if method == "gpt":
        system_message, assistant_message = (
            CoreEngine.classifier.generate_system_message(sub_labels, df)
        )
        CoreEngine.classifier.generate_gpt_messages(
            system_message, assistant_message, df
        )

        llm_classifier = CoreEngine.classifier.fine_tune_gpt()

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
        x_text_features, vx = CoreEngine.classifier.extract_text_features(df)

        # Transform labels
        y_df, _ = CoreEngine.classifier.transform_labels(df)

        # Combine features
        x_combined = CoreEngine.classifier.create_combined_features(x_text_features)

        # Perform MLSMOTE to augment the data

        if len(prs) < 3:
            print("Too Few PRs to train! Quitting")
            return

        print("\nbalancing classes...")
        x_augmented, y_augmented = CoreEngine.classifier.perform_mlsmote(
            x_combined, y_df, n_sample=500
        )

        print("\nTraining RF model...")
        x_combined = pd.concat([x_combined, x_augmented], axis=0)
        y_combined = pd.concat([y_df, y_augmented], axis=0)

        # Train
        clf = CoreEngine.classifier.train_random_forest(x_combined, y_combined)

        # Save Model
        with open(cfg_dict["classification_model_save"], "wb") as f:
            dat = {
                "time_saved": datetime.now(),
                "model": clf,
                "vectorizer": vx,
                "labels": y_df,
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
    CoreEngine.database_init.start()

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

    return CoreEngine.utils.read_jsonfile_into_dict(cfg_path)


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


def get_prs_df(db: CoreEngine.DatabaseManager, prs):
    """Todo."""
    df = db.get_df(prs)
    columns_to_convert = df.columns[15:]
    df[columns_to_convert] = df[columns_to_convert].map(lambda x: 1 if x > 0 else 0)
    df["issue text"] = df["issue text"].apply(CoreEngine.classifier.clean_text)
    df["issue description"] = df["issue description"].apply(
        CoreEngine.classifier.clean_text
    )
    df = CoreEngine.classifier.filter_domains(df)

    return df


if __name__ == "__main__":
    main()
