#
# main.py
#
# By Benjamin Carter, TJ Potter, and Brent McLennan.
#  
# This function parses an AST and displays all the type identifiers from the AST.
# The user can then select an identifier and view its documentation using the Java Docs.

# Read the java code from the JSON.
# Get list of tokens available to search for and their line numbers.
# Search on docs for the token.

import json
from generateAST import generateAST
import os
from symbolTable import SymbolTable
import tokens as tokenExtract

class JavaProgram():
    """Class represents a Java AST Tree.
    """
    def __init__(self, javaAST : dict):
        """Set up the class. Requires AST.

        Args:
            javaAST (dict): AST
        """
        self.ast = javaAST

        self.classes = None
        self.methods = None
        self.symbols = None
        self.completeTable = None
    
    def getClasses(self):
        """Takes the classnames from the file, matches it to imports, and returns all the full-name class names.

        Returns:
            list: Data structure with the tokens
                  matched to the full class name based off of imports.
        """
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
        pgrmTables = SymbolTable(self.ast)
        self.symbols = pgrmTables.findSymbols() # gets all classes with variable names.
        self.methods = pgrmTables.getMethods() # gets all methods from variable name.

    def getCompleteSymbolTable(self):
        """Match methods and symbols and class names into a combined data structure.

        Args:
            tokenList (dict): Token (class name) data structure.
            symbols (dict): Symbol (variable name) data structure.
            methods (dict): Method (method name) data structure.

        Returns:
            dict: Data Structure of compiled symbols, methods, and classes.
        """

        if(self.classes is None):
            self.getClasses()
        if(self.symbols is None or self.methods is None):
            self.populateSymbolTable()

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

        return functions
    
    

if __name__ == "__main__":


    # get AST from JSON.
    ast = generateAST("samples/PreviewViewer.java")
    # fp = open("generatedFiles/saved.ast.json")
    # ast = json.load(fp)
    # fp.close()

    pgrm = JavaProgram(ast)
    classNames = pgrm.getClasses() # converts all class names to full names.
    print(classNames)
    print("*"*20)
    symbols = pgrm.getCompleteSymbolTable()
    print(symbols)
    print("*"*20)
    funcs = pgrm.getFunctions()
    print(funcs)
    
