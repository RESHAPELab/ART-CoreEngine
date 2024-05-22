#
# main.py
#
# By Benjamin Carter, Dylan Johnson, and Hunter Jenkins
#  
# This program constitutes the main of the CoreEngine

import glob
import json
import sys

import tqdm
from AI_Taxonomy import AICachedClassifier, load_data
from DatabaseManager import DatabaseManager
import github_pull
from generateAST import generateAST
import os
from symbolTable import SymbolTable
import tokens as tokenExtract
import csv_pull
import store_result
import csv_push
import database_init

RED_COLOR = "\033[1m\033[38;5;9m"
YELLOW_COLOR = "\033[1m\033[38;5;11m"
RESET_COLOR = "\033[0m"


class JavaProgram():
    """Class represents a Java AST Tree.
    """
    def __init__(self, javaAST : dict):
        """Set up the class. Requires AST.

        Args:
            javaAST (dict): AST
        """
        self.ast = javaAST

        # Cached Responses
        self.reset()
    
    def reset(self):
        """Reset internal caches"""
        self.classes = None
        self.plain_classes = None
        self.methods = None
        self.symbols = None
        self.completeTable = None
        self.functions = None

    def getClasses(self):
        """Get classes in program

        Returns:
            set[str]: Set of all classes in program
        """
        if(not(self.plain_classes) is None):
            return self.plain_classes

        self.plain_classes = set()
        class_options = self.getClassOptions()
        for class_name in class_options:
            node = class_options[class_name]
            if node == 0:
                continue
            for x in node:
                self.plain_classes.add(x)
        return self.plain_classes

    def getClassOptions(self):
        """Takes the classnames from the file, matches it to imports, and returns all the full-name class names.

        Returns:
            list: Data structure with the tokens
                  matched to the full class name based off of imports.
        """

        if(not(self.classes is None)):
            return self.classes

        ast = self.ast

        tokens = set(tokenExtract.pullToken(ast))
        imports =  set(tokenExtract.pullImport(ast))

        result = {}
        importItems = {}
        for i in imports:
            params = i.split(".")
            name = params[-1]
            if(name in importItems):
                importItems[name].append(i)
            else:
                importItems[name] = [i]

        for token in tokens:
            # check to see if it is in the imports.
            # if not, check lang
            # if not, fail
            if(token in importItems):
                result[token] = importItems[token]
            else:
                result[token] = 0
        
        self.classes = result
        return result

    def populateSymbolTable(self):
        """Pre-generate symbols and methods
        """
        pgrmTables = SymbolTable(self.ast)
        self.symbols = pgrmTables.findSymbols()  # gets all classes with variable names.
        self.methods = pgrmTables.getMethods()  # gets all methods from variable name.

    def getCompleteSymbolTable(self):
        """Match methods and symbols and class names into a combined data structure.

        Returns:
            dict: Data Structure of compiled symbols, methods, and classes.
        """

        if(self.classes is None):
            self.getClassOptions()
        if(self.symbols is None or self.methods is None):
            self.populateSymbolTable()
        
        if(not(self.completeTable is None)):
            return self.completeTable

        out = {}
        for className in self.classes:
            out[className] = {"full" : self.classes[className], "varlist" : []}

            for num, variable in enumerate(self.symbols):
                if(variable["class"] != className):
                    continue
                variableName = variable["name"]
                lineNumber = variable["line"]

                nextLine = -1
                for vr in self.symbols[num+1:]:
                    # see if there are any more!
                    if(vr["class"] != className):
                        continue
                # if(variable["line"] > lineNumber):
                    nextLine = vr["line"] - 1
                    break # CHECK! We may need to move this back.


                methodOut = []
                for method in self.methods:
                    # check to see if it is referencing the same variable
                    if(method["name"] != variableName):
                        continue

                    # TODO: instead of comparing line numbers, compare depth in AST tree.
                    # print(className, method["name"], lineNumber, nextLine, method["line"])
                    # if(method["line"] < lineNumber):
                    #     continue
                    # if(nextLine != -1 and method["line"] > nextLine):
                    #     continue
                    # print("Append!")
                    methodOut.append(method)

                out[className]["varlist"].append({"variable":variable, "methods": methodOut})
        
        self.completeTable = out
        return out

    def getFunctions(self):
        """Return all the functions used in the program

        Returns:
            dict[str : list]: function_name : [line numbers]
        """
        if(not(self.functions is None)):
            return self.functions
        
        if(self.completeTable is None):
            self.getCompleteSymbolTable()
        

        functions = {}
        for className in self.completeTable:
            data = self.completeTable[className]

            methodsGeneral = []
            for varl in data["varlist"]:
                for m in varl["methods"]:
                    methodsGeneral.append(m)
            
            fullName = "Unknown"
            if(data["full"] != 0):
                for fN in data["full"]:
                    for mN in methodsGeneral:
                        if(f"{fN}::{mN['method']}" in functions):
                            functions[f"{fN}::{mN['method']}"].append(mN["line"])
                        else:
                            functions[f"{fN}::{mN['method']}"] = [mN["line"]]
            else:
                for mN in methodsGeneral:
                    if(f"Unknown::{mN['method']}" in functions):
                        functions[f"Unknown::{mN['method']}"].append(mN["line"])
                    else:
                        functions[f"Unknown::{mN['method']}"] = [mN["line"]]
        
        self.functions = functions
        return functions

    # Function to extract and print class names and methods
    def extract_classes_and_methods(self) -> tuple[set[str], dict]:
        """Function to extract and print class names and methods

        Returns:
            set: classes
            dict: functions
        """
        return self.getClasses(), self.getFunctions()

    
def processFiles(ai : AICachedClassifier, db : DatabaseManager):
    """Process files that have not been processed yet

    Args:
        ai (AICachedClassifier): AI Classifier Engine
        db (DatabaseManager): Database Engine
    """
    MAX_COUNT = 20 # adjust for how many files to process when function called!!!

    files = db.get_unprocessed_files()
    count = 0
    files_done = set()

    # Go file by file
    for fileElement in tqdm.tqdm(files):
        # extract file path and commit_hash
        file = fileElement[0]
        commit_hash = fileElement[1]

        # verify if there are no repeat files!
        if((file, commit_hash) in files_done):
            print(file, commit_hash)
            raise ValueError("Repeat! Fails assert! Log Bug Report!")
        files_done.add((file,commit_hash))

        # download from GitHub
        saveLocation = db.manageDownload(file, commit_hash)

        try:
            github_pull.get_github_single_file("JabRef","jabref",commit_hash, file,saveLocation)
        except ValueError as e:
            print(f"{YELLOW_COLOR}Error downloading file {commit_hash, file}. Likely requires a different commit. Please check. \n Error: {e}{RESET_COLOR}",file=sys.stderr)
            db.mark_file_as_processed(file,commit_hash,status="Error downloading")
            continue
        print("Downloaded: ", commit_hash, file)
        
        # generated AST.
        try:
            result = generateAST(saveLocation)
        except:
            db.mark_file_as_processed(file,commit_hash,status="unsupported lang")
            continue
        
        # parse AST
        pgrm = JavaProgram(result)
        try:
            plain_classes = pgrm.getClasses()  # converts all class names to full names.
            functions = pgrm.getFunctions().keys()
        except:
            print(f"{RED_COLOR}ERROR PARSING JAVA PROGRAM {saveLocation}. Please submit bug ticket! Send the file '{saveLocation}' in the bug ticket{RESET_COLOR}",file=sys.stderr)
            db.mark_file_as_processed(file,commit_hash,status="ERROR in Java Parsing")
            continue

        # classify api's
        local_domain_cache = {}
        for class_name in plain_classes:
            domain = ai.classify_API(class_name)
            local_domain_cache[class_name] = domain
            db.store_class_classification(class_name, domain)
        db.save()

        # classify functions
        for function in functions:
            tokens = function.split("::")
            class_name = tokens[0]
            if(class_name == "Unknown"):
                continue
            function_name = tokens[1]

            class_domain = local_domain_cache[class_name]
            subdomain = ai.classify_function(class_name, function_name, class_domain)
            db.store_function_classification(class_name, function_name, subdomain)
        
        # mark as processed and continue
        db.mark_file_as_processed(file, commit_hash)
        db.save()
        count += 1
        if(count > MAX_COUNT):
            break
        
        

if __name__ == "__main__":

    # Setup!
    if (not (os.path.isdir("generatedFiles"))):
        os.makedirs("generatedFiles")

    os.chdir("generatedFiles")
    if (not (os.path.isdir("downloadedFiles"))):
        os.makedirs("downloadedFiles")
    os.chdir("../")

    def setupDB():
        """Put instructions here that you want run on first initialization (after folders are made)
        """
        # Clear download directory
        for file in glob.glob("generatedFiles/downloadedFiles/*"):
            os.remove(file)

        database_init.populate_db_with_mining_data()
        database_init.setup_caches()

    database_init.start(setupDB)

    # Create Database Connection
    db = DatabaseManager()
    #-----------------------
    API_listing_file = 'domain_labels.json' 
    sub_domain_listing_file = 'subdomain_labels.json'
    #-----------------------

    api_domain_listing = load_data(API_listing_file)
    sub_domain_listing = load_data(sub_domain_listing_file)

    classifier = AICachedClassifier(api_domain_listing, sub_domain_listing, db)

    print("Processing files")
    processFiles(classifier, db)
    
    db.save()
    db.close()
