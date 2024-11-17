#
# processing.py
#
# By Anonymous
#
# This program constitutes the main of the CoreEngine

import os
import sys
from typing import Optional
import tqdm
from . import github_pull
from .ai_taxonomy import AICachedClassifier, load_data
from .database_manager import DatabaseManager, Repository
from .generate_ast import generate_ast
from .java_ast import JavaProgram


RED_COLOR = "\033[1m\033[38;5;9m"
YELLOW_COLOR = "\033[1m\033[38;5;11m"
RESET_COLOR = "\033[0m"


def process_files(
    ai: AICachedClassifier,
    db: DatabaseManager,
    pr=None,
    repo: Optional[Repository] = None,
):
    """Process files that have not been processed yet

    Args:
        ai (AICachedClassifier): AI Classifier Engine
        db (DatabaseManager): Database Engine
        pr (Optional[int], default=None): Set to pr # for processing files from a specific PR # (None for all.)
        repo (Optional[Repository], default=None): Set to repo # for processing files from a specific repo.
    """
    if repo is None and pr is not None:
        raise NotImplementedError(
            "If specifying PR #, please indicate Repository # too"
        )

    files = db.get_unprocessed_files(pr, repo)
    # later change to process files from one PR! db.get_unprocessed_files(pr)
    files_done = set()

    # Go file by file
    for fileElement in tqdm.tqdm(files, smoothing=0.05, leave=False):
        # extract file path and commit_hash
        file = fileElement[0]
        commit_hash = fileElement[1]
        spc_repo = fileElement[2]

        # verify if there are no repeat files!
        if (file, commit_hash) in files_done:
            print(file, commit_hash)
            raise ValueError("Repeat! Fails assert! Log Bug Report!")
        files_done.add((file, commit_hash))

        # download from GitHub
        saveLocation = db.manageDownload(file, commit_hash, spc_repo)

        # quick hack to skip all files except java files to save time!
        name, ending = os.path.splitext(file)
        if ending != ".java":
            db.mark_file_as_processed(
                file,
                commit_hash,
                repo=spc_repo,
                status="Time Save Not Java",
            )
            continue
        try:
            github_pull.get_github_single_file(
                spc_repo.owner, spc_repo.name, commit_hash, file, saveLocation
            )
        except Exception as e:
            print(
                f"\t{YELLOW_COLOR}Error downloading file {commit_hash, file}. Likely requires a different commit. Please check. \n Error: {e}{RESET_COLOR}",
                file=sys.stderr,
            )
            db.mark_file_as_processed(
                file, commit_hash, status="Error downloading", repo=spc_repo
            )
            continue
        # print("\tDownloaded: ", commit_hash, file)

        # generated AST.
        try:
            result = generate_ast(saveLocation)
        except:
            db.mark_file_as_processed(
                file, commit_hash, status="unsupported lang", repo=spc_repo
            )
            continue

        # parse AST
        pgrm = JavaProgram(result)
        try:
            plain_classes = pgrm.getClasses()  # converts all class names to full names.
            functions = pgrm.getFunctions().keys()
        except:
            print(
                f"\t{YELLOW_COLOR}Can't parse Java Program {saveLocation}. {RESET_COLOR}",
                file=sys.stderr,
            )
            db.mark_file_as_processed(
                file, commit_hash, status="ERROR in Java Parsing", repo=spc_repo
            )
            continue

        # classify api's
        local_domain_cache = {}
        for class_name in plain_classes:
            domain = ai.classify_API(class_name)  # automatically saves it to cache.
            local_domain_cache[class_name] = domain
            db.mark_file_api_use(file, commit_hash, class_name, spc_repo)
        db.save()

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
            db.mark_file_function_use(
                file, commit_hash, class_name, function_name, spc_repo
            )

        # mark as processed and continue
        db.mark_file_as_processed(file, commit_hash, spc_repo)
        os.unlink(saveLocation)
        db.save()

    db.save()
