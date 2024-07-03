"""
main.py

By Benjamin Carter, Dylan Johnson, and Hunter Jenkins

This program constitutes the main of the CoreEngine
"""

from .symbol_table import SymbolTable
from . import tokens as tokenExtract

# TODO. Refactor this.


class JavaProgram:
    """Class represents a Java AST Tree."""

    def __init__(self, javaAST: dict):
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
        if not (self.plain_classes) is None:
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

        if not (self.classes is None):
            return self.classes

        ast = self.ast

        tokens = set(tokenExtract.pullToken(ast))
        imports = set(tokenExtract.pullImport(ast))

        result = {}
        importItems = {}
        for i in imports:
            params = i.split(".")
            name = params[-1]
            if name in importItems:
                importItems[name].append(i)
            else:
                importItems[name] = [i]

        for token in tokens:
            # check to see if it is in the imports.
            # if not, check lang
            # if not, fail
            if token in importItems:
                result[token] = importItems[token]
            else:
                result[token] = 0

        self.classes = result
        return result

    def populateSymbolTable(self):
        """Pre-generate symbols and methods"""
        pgrmTables = SymbolTable(self.ast)
        self.symbols = pgrmTables.findSymbols()  # gets all classes with variable names.
        self.methods = pgrmTables.getMethods()  # gets all methods from variable name.

    def getCompleteSymbolTable(self):
        """Match methods and symbols and class names into a combined data structure.

        Returns:
            dict: Data Structure of compiled symbols, methods, and classes.
        """

        if self.classes is None:
            self.getClassOptions()
        if self.symbols is None or self.methods is None:
            self.populateSymbolTable()

        if not (self.completeTable is None):
            return self.completeTable

        out = {}
        for className in self.classes:
            out[className] = {"full": self.classes[className], "varlist": []}

            for num, variable in enumerate(self.symbols):
                if variable["class"] != className:
                    continue
                variableName = variable["name"]
                lineNumber = variable["line"]

                nextLine = -1
                for vr in self.symbols[num + 1 :]:
                    # see if there are any more!
                    if vr["class"] != className:
                        continue
                    # if(variable["line"] > lineNumber):
                    nextLine = vr["line"] - 1
                    break  # CHECK! We may need to move this back.

                methodOut = []
                for method in self.methods:
                    # check to see if it is referencing the same variable
                    if method["name"] != variableName:
                        continue

                    # TODO: instead of comparing line numbers, compare depth in AST tree.
                    # print(className, method["name"], lineNumber, nextLine, method["line"])
                    # if(method["line"] < lineNumber):
                    #     continue
                    # if(nextLine != -1 and method["line"] > nextLine):
                    #     continue
                    # print("Append!")
                    methodOut.append(method)

                out[className]["varlist"].append(
                    {"variable": variable, "methods": methodOut}
                )

        self.completeTable = out
        return out

    def getFunctions(self):
        """Return all the functions used in the program

        Returns:
            dict[str : list]: function_name : [line numbers]
        """
        if not (self.functions is None):
            return self.functions

        if self.completeTable is None:
            self.getCompleteSymbolTable()

        functions = {}
        for className in self.completeTable:
            data = self.completeTable[className]

            methodsGeneral = []
            for varl in data["varlist"]:
                for m in varl["methods"]:
                    methodsGeneral.append(m)

            fullName = "Unknown"
            if data["full"] != 0:
                for fN in data["full"]:
                    for mN in methodsGeneral:
                        if f"{fN}::{mN['method']}" in functions:
                            functions[f"{fN}::{mN['method']}"].append(mN["line"])
                        else:
                            functions[f"{fN}::{mN['method']}"] = [mN["line"]]
            else:
                for mN in methodsGeneral:
                    if f"Unknown::{mN['method']}" in functions:
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
