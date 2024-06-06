"""
main.py

By Benjamin Carter, Dylan Johnson, and Hunter Jenkins

This program constitutes the main of the CoreEngine
"""

from src.symbolTable import SymbolTable
from src import tokens as tokenExtract


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
