"""
main.py

By Benjamin Carter, Dylan Johnson, and Hunter Jenkins

This program constitutes the main of the CoreEngine
"""

import glob
import os
import sys

import tqdm

from src.AI_Taxonomy import AICachedClassifier, load_data
from src.DatabaseManager import DatabaseManager
from src import github_pull
from src.generateAST import generateAST
from src.symbolTable import SymbolTable
from src import tokens as tokenExtract
from src import store_result
from src import database_init


RED_COLOR = "\033[1m\033[38;5;9m"
YELLOW_COLOR = "\033[1m\033[38;5;11m"
RESET_COLOR = "\033[0m"


class JavaProgram:
    """Class represents a Java AST Tree."""

    def __init__(self, java_ast: dict):
        """Set up the class. Requires AST.

        Args:
            java_ast (dict): AST
        """
        self.ast = java_ast

        self.classes = None
        self.plain_classes = None
        self.methods = None
        self.symbols = None
        self.complete_table = None
        self.functions = None

    def get_classes(self):
        """Get classes in program

        Returns:
            set[str]: Set of all classes in program
        """
        if self.plain_classes is not None:
            return self.plain_classes

        self.plain_classes = set()

        class_options = self.get_class_options()
        for class_name in class_options.items():
            node = class_options[class_name]
            if node == 0:
                continue
            for x in node:
                self.plain_classes.add(x)
        return self.plain_classes

    def get_class_options(self):
        """
        Takes the classnames from the file, matches it to imports, and
        returns all the full-name class names.

        Returns:
            list: Data structure with the tokens matched to the full
            class name based off of imports.
        """

        if self.classes is not None:
            return self.classes

        ast = self.ast

        tokens = set(tokenExtract.pullToken(ast))
        imports = set(tokenExtract.pullImport(ast))

        result = {}
        import_items = {}
        for i in imports:
            params = i.split(".")
            name = params[-1]
            if name in import_items:
                import_items[name].append(i)
            else:
                import_items[name] = [i]

        for token in tokens:
            # check to see if it is in the imports.
            # if not, check lang
            # if not, fail
            if token in import_items:
                result[token] = import_items[token]
            else:
                result[token] = 0

        self.classes = result
        return result

    def populate_symbol_table(self):
        """Pre-generate symbols and methods"""

        pgrm_tables = SymbolTable(self.ast)

        self.symbols = (
            pgrm_tables.findSymbols()
        )  # gets all classes with variable names.

        self.methods = pgrm_tables.getMethods()  # gets all methods from variable name.

    def get_complete_symbol_table(self):
        """Match methods and symbols and class names into a combined data structure.

        Returns:
            dict: Data Structure of compiled symbols, methods, and classes.
        """

        if self.classes is None:
            self.get_class_options()

        if self.symbols is None or self.methods is None:
            self.populate_symbol_table()

        if self.complete_table is not None:
            return self.complete_table

        out = {}
        for class_name in self.classes:
            out[class_name] = {"full": self.classes[class_name], "varlist": []}

            for num, variable in enumerate(self.symbols):
                if variable["class"] != class_name:
                    continue
                variable_name = variable["name"]

                for vr in self.symbols[num + 1 :]:
                    # see if there are any more!
                    if vr["class"] != class_name:
                        continue
                    # if(variable["line"] > lineNumber):
                    break  # CHECK! We may need to move this back.

                method_out = []
                for method in self.methods:
                    # check to see if it is referencing the same variable
                    if method["name"] != variable_name:
                        continue

                    # TODO: instead of comparing line numbers, compare depth in AST tree.
                    # print(className, method["name"], lineNumber, nextLine, method["line"])
                    # if(method["line"] < lineNumber):
                    #     continue
                    # if(nextLine != -1 and method["line"] > nextLine):
                    #     continue
                    # print("Append!")
                    method_out.append(method)

                out[class_name]["varlist"].append(
                    {"variable": variable, "methods": method_out}
                )

        self.complete_table = out
        return out

    def get_functions(self):
        """Return all the functions used in the program

        Returns:
            dict[str : list]: function_name : [line numbers]
        """
        if self.functions is not None:
            return self.functions

        if self.complete_table is None:
            self.get_complete_symbol_table()

        functions = {}
        for class_name in self.complete_table:
            data = self.complete_table[class_name]

            methods_general = []
            for varl in data["varlist"]:
                for m in varl["methods"]:
                    methods_general.append(m)

            if data["full"] != 0:
                for f_n in data["full"]:
                    for m_n in methods_general:
                        if f"{f_n}::{m_n['method']}" in functions:
                            functions[f"{f_n}::{m_n['method']}"].append(m_n["line"])
                        else:
                            functions[f"{f_n}::{m_n['method']}"] = [m_n["line"]]
            else:
                for m_n in methods_general:
                    if f"Unknown::{m_n['method']}" in functions:
                        functions[f"Unknown::{m_n['method']}"].append(m_n["line"])
                    else:
                        functions[f"Unknown::{m_n['method']}"] = [m_n["line"]]

        self.functions = functions
        return functions

    # Function to extract and print class names and methods
    def extract_classes_and_methods(self) -> tuple[set[str], dict]:
        """Function to extract and print class names and methods

        Returns:
            set: classes
            dict: functions
        """
        return self.get_classes(), self.get_functions()


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
            result = generateAST(save_location)
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
    # -----------------------
    API_LISTING_FILE = "./data/domain_labels.json"
    SUB_DOMAIN_LISTING_FILE = "./data/subdomain_labels.json"
    # -----------------------

    api_domain_listing = load_data(API_LISTING_FILE)
    sub_domain_listing = load_data(SUB_DOMAIN_LISTING_FILE)

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
