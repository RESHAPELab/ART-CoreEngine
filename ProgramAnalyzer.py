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

        self.classNames = None
        self.methods = None
        self.symbols = None
    
    def getClassnames(self):
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
        
        self.classNames = result
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

        if(self.classNames is None):
            self.getClassnames()
        if(self.symbols is None or self.methods is None):
            self.populateSymbolTable()

        out = {}
        for className in self.classNames:
            out[className] = {"full" : self.classNames[className], "varlist" : []}

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
        return out

    

if __name__ == "__main__":


    # get AST from JSON.
    generateAST("samples/PreviewViewer.java")
    fp = open("generatedFiles/saved.ast.json")
    ast = json.load(fp)
    fp.close()

    pgrm = JavaProgram(ast)
    classNames = pgrm.getClassnames() # converts all class names to full names.
    print(classNames)

    print("*"*20)

    symbols = pgrm.getCompleteSymbolTable()
    print(symbols)
    

