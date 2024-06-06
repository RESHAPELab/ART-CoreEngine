"""TODO."""

import glob
import os
import sys

import tqdm

from src.AI_Taxonomy import AICachedClassifier, load_data
from src.DatabaseManager import DatabaseManager
from src import github_pull
from src.generate_ast import generate_ast
from src.java_ast import JavaProgram

from src import store_result
from src import database_init


RED_COLOR = "\033[1m\033[38;5;9m"
YELLOW_COLOR = "\033[1m\033[38;5;11m"
RESET_COLOR = "\033[0m"


def main():
    """TODO."""

    api_listing_file = "./data/domain_labels.json"
    sub_domain_listing_file = "./data/subdomain_labels.json"

    # Setup!
    if not os.path.isdir("output"):
        os.makedirs("output")

    os.chdir("output")
    if not os.path.isdir("downloadedFiles"):
        os.makedirs("downloadedFiles")
    os.chdir("../")

    def setup_db():
        """
        Put instructions here that you want run on first initialization
        (after folders are made)
        """

        # Clear download directory
        for file in glob.glob("output/downloadedFiles/*"):
            os.remove(file)

        database_init.populate_db_with_mining_data()
        database_init.setup_caches()

    database_init.start(setup_db)

    # Create database connection
    db = DatabaseManager()

    api_domain_listing = load_data(api_listing_file)
    sub_domain_listing = load_data(sub_domain_listing_file)

    classifier = AICachedClassifier(api_domain_listing, sub_domain_listing, db)

    print("\nProcessing files...")
    process_files(classifier, db)

    db.save()
    db.close()

    # EXPORT! Requires DB to be closed.
    print("\nExporting....")
    store_result.sqlite_to_csv(
        "./output/main.db", "outputTable", "./output/core_engine_output.csv"
    )


def process_files(ai: AICachedClassifier, database: DatabaseManager):
    """Process files that have not been processed yet

    Args:
        ai (AICachedClassifier): AI Classifier Engine
        db (DatabaseManager): Database Engine
    """
    max_count = 10  # adjust for how many successful *java* files to process when function called!!!

    files = database.get_unprocessed_files()
    count = 0
    files_done = set()

    # Go file by file
    for file_element in tqdm.tqdm(files):
        # extract file path and commit_hash
        file = file_element[0]
        commit_hash = file_element[1]

        # verify if there are no repeat files!
        if (file, commit_hash) in files_done:
            print(file, commit_hash)
            raise ValueError("Repeat! Fails assert! Log Bug Report!")
        files_done.add((file, commit_hash))

        # download from GitHub
        save_location = database.manageDownload(file, commit_hash)

        try:
            github_pull.get_github_single_file(
                "JabRef", "jabref", commit_hash, file, save_location
            )
        except ValueError as e:
            print(
                (
                    f"{YELLOW_COLOR}Error downloading file {commit_hash, file}. "
                    f"A different commit may be required. \n"
                    f"Error: {e}{RESET_COLOR}"
                ),
                file=sys.stderr,
            )
            database.mark_file_as_processed(
                file, commit_hash, status="Error downloading"
            )
            continue
        print("Downloaded: ", commit_hash, file)

        # generated AST.
        try:
            result = generate_ast(save_location)
        except:
            database.mark_file_as_processed(
                file, commit_hash, status="unsupported lang"
            )
            continue

        # parse AST
        pgrm = JavaProgram(result)
        try:
            plain_classes = (
                pgrm.get_classes()
            )  # converts all class names to full names.
            functions = pgrm.get_functions().keys()
        except:
            print(
                (
                    f"{RED_COLOR}ERROR PARSING JAVA PROGRAM {save_location}. "
                    f"Please submit a bug ticket! Send the file '{save_location}' in the bug ticket"
                    f"{RESET_COLOR}"
                ),
                file=sys.stderr,
            )
            database.mark_file_as_processed(
                file, commit_hash, status="ERROR in Java Parsing"
            )
            continue

        # classify api's
        local_domain_cache = {}
        for class_name in plain_classes:
            domain = ai.classify_API(class_name)  # automatically saves it to cache.
            local_domain_cache[class_name] = domain
            database.mark_file_api_use(file, commit_hash, class_name)
        database.save()

        # classify functions
        for function in functions:
            tokens = function.split("::")
            class_name = tokens[0]
            if class_name == "Unknown":
                continue
            function_name = tokens[1]

            class_domain = local_domain_cache[class_name]
            ai.classify_function(
                class_name, function_name, class_domain
            )  # automatically saves it to cache. Save for later.
            database.mark_file_function_use(
                file, commit_hash, class_name, function_name
            )

        # mark as processed and continue
        database.mark_file_as_processed(file, commit_hash)
        database.save()
        count += 1
        if count > max_count:
            break


if __name__ == "__main__":
    main()
