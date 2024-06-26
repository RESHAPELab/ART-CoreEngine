"""
main.py

By Benjamin Carter, Dylan Johnson, and Hunter Jenkins

This program constitutes the main of the CoreEngine
"""

from src.symbol_table import SymbolTable
from src import tokens as tokenExtract
import builtins

# TODO. Refactor this.

class PythonProgram():
    """Class represents a Java AST Tree.
    """

    def __init__(self, pythonAST: dict):
        """Set up the class. Requires AST.

        Args:
            javaAST (dict): AST
        """
        self.ast = pythonAST

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
        if (not (self.plain_classes) is None):
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

        if (not (self.classes is None)):
            return self.classes

        ast = self.ast

        tokens = set(tokenExtract.pullTokenPython(ast))
        imports = set(tokenExtract.pullImportPython(ast))
        #print("HERE: " + str(tokens))


        result = {}
        importItems = {}
        for i in imports:
            params = i.split(":")
            name = params[-1]
            if (name in importItems):
                importItems[name].append(i)
            else:
                importItems[name] = [i]


        for token in tokens:
            # check to see if it is in the imports.
            # if not, check lang
            # if not, fail
            if (token in importItems):
                name = importItems[token][0].split(":")
                if len(name) >= 2:
                    result[name[0]] = importItems[token]
                else:
                    result[name[0]] = importItems[token]
            else:
                result[token] = 0

        self.classes = result
        return result

    def populateSymbolTable(self):
        """Pre-generate symbols and methods
        """
        pgrmTables = SymbolTable(self.ast)
        self.symbols = pgrmTables.findSymbolsPy()  # gets all classes with variable names.
        self.methods = pgrmTables.getMethodsPy()  # gets all methods from variable name.

    def getCompleteSymbolTable(self):
        """Match methods and symbols and class names into a combined data structure.

        Returns:
            dict: Data Structure of compiled symbols, methods, and classes.
        """

        # def find_method_in_builtin_types(builtin_module, method_name):
        #     found_methods = []
        #     for attr_name in dir(builtin_module):
        #         attr = getattr(builtin_module, attr_name)
        #         if hasattr(attr, method_name) and callable(getattr(attr, method_name)):
        #             found_methods.append((attr_name, method_name))
        #     return found_methods
        def find_method_in_builtin_types(builtin_module, method_name):
            found_methods = []
            for attr_name in dir(builtin_module):
                if attr_name.startswith('__') and attr_name.endswith('__'):
                    continue  # Skip special attributes like __doc__, __name__, etc.

                attr = getattr(builtin_module, attr_name)
                if hasattr(attr, method_name) and callable(getattr(attr, method_name)):
                    found_methods.append((attr_name, method_name))
            return found_methods

        if (self.classes is None):
            self.getClassOptions()
        if (self.symbols is None or self.methods is None):
            self.populateSymbolTable()

        if (not (self.completeTable is None)):
            return self.completeTable

        out = {}
        out["built-in"] = {"full": "python built-in types", "varlist": []}
        for className in self.classes:
            # out[className] = {"full": self.classes[className], "varlist": []}
            for num, variable in enumerate(self.symbols):
                if(variable["name"] == className):
                    out[variable["name"]] = {"full": self.classes[className], "varlist": []}
                #print(variable["name"])
                # if (variable["name"] != className):
                #     continue
                    variableName = variable["name"]
                    lineNumber = variable["line"]
                # nextLine = -1
                # for vr in self.symbols[num + 1:]:
                #     # see if there are any more!
                #     if (vr["class"] != className):
                #         continue
                #     # if(variable["line"] > lineNumber):
                #     nextLine = vr["line"] - 1
                #     break  # CHECK! We may need to move this back.

                    methodOut = []
                    builtInMethods = []
                    i = 0
                    for method in self.methods:
                        i += 1
                        #print(str(i) + str(method))
                        # check to see if it is referencing the same variable
                        alias = False
                        if self.classes[className] != 0:
                            inner_class = (self.classes[className][0].split(":"))
                            if len(inner_class) >= 2:
                                if method["name"] == inner_class[1]:
                                    alias = True
                                    out[inner_class[0]] = {"full": self.classes[className], "varlist": []}
                                    method['name'] = inner_class[0]
                                    methodOut.append(method)
                                    #variable['class'] = inner_class[0]
                        if (method["name"] != variableName and not alias):
                            continue

                        # TODO: instead of comparing line numbers, compare depth in AST tree.
                        # print(className, method["name"], lineNumber, nextLine, method["line"])
                        # if(method["line"] < lineNumber):
                        #     continue
                        # if(nextLine != -1 and method["line"] > nextLine):
                        #     continue
                        # print("Append!")
                        #print(method)

                        if not alias:
                            if self.plain_classes.__contains__(className):
                                methodOut.append(method)
                            else:
                                if variable["class"] == "unknown" or variable["class"] == "UNKNOWN":
                                    found_modules = find_method_in_builtin_types(builtins, method["method"])
                                    result = ""
                                    if len(found_modules) > 1:
                                        for module in found_modules:
                                            result += str(module[0]) + "/"
                                        result = result[:-1]
                                    else:
                                        result = found_modules[0][0]
                                    method["name"] = result
                                    builtInMethods.append(method)
                                else:
                                    method["name"] = variable["class"]
                                    builtInMethods.append(method)
                        # methodOut.append(method)
                    out[variable["name"]]["varlist"].append({"variable": variable, "methods": methodOut})
                    out["built-in"]["varlist"].append({"variable": variable, "methods": builtInMethods})
        self.completeTable = out
        #print(self.completeTable)
        return out

    def getFunctions(self):
        """Return all the functions used in the program

        Returns:
            dict[str : list]: function_name : [line numbers]
        """
        if (not (self.functions is None)):
            return self.functions

        if (self.completeTable is None):
            self.getCompleteSymbolTable()

        functions = {}
        for className in self.completeTable:
            data = self.completeTable[className]
            # print(className)

            methodsGeneral = []
            for varl in data["varlist"]:
                for m in varl["methods"]:
                    methodsGeneral.append(m)

            fullName = "Unknown"
            # if (data["full"] != 0):
            #print("WHAT: " + str(data["varlist"]))

            for vN in data["varlist"]:
                print("HERE: " + str(vN))
                for fN in vN["methods"]:
                    if vN['variable']['class'] != "unknown":
                        if (f"{vN['variable']['class']}::{fN['method']}" in functions):
                            functions[f"{vN['variable']['class']}::{fN['method']}"].append(fN["line"])
                            break
                        else:
                            functions[f"{vN['variable']['class']}::{fN['method']}"] = [fN["line"]]
                            break
                    else:
                        for mN in methodsGeneral:
                            if (f"{fN['name']}::{fN['method']}" in functions):
                                functions[f"{fN['name']}::{fN['method']}"].append(fN["line"])
                                break
                            else:
                                functions[f"{fN['name']}::{fN['method']}"] = [fN["line"]]
                                break
            # else:
            #     for mN in methodsGeneral:
            #         if (f"Unknown::{mN['method']}" in functions):
            #             functions[f"Unknown::{mN['method']}"].append(mN["line"])
            #         else:
            #             functions[f"Unknown::{mN['method']}"] = [mN["line"]]

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



# TODO:
#
# Currently it has a bit of an issue sometimes due to pythons builtin classes (such as list, dict, etc) 
# with builtin functions (such as append, split, etc).
#
# It will attempt to cast each function under a class but it sometimes doesn't find one (if its based off of another variable, x = y[3]) 
# or the function has multiple possible classes it belongs to (such as split, belonging to BaseExceptionGroup/ExceptionGroup/bytearray/bytes/str).
