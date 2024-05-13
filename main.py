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
from bs4 import BeautifulSoup
import glob
import os
import sys
from symbolTable import SymbolTable
import tokens
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from chatgpt import askGPT_ClassDescription


def summarize(text, language="english", sentences_count=1):
    """Summarize a piece of text into a sentence.

    Args:
        text (str): The text input
        language (str, optional): Language selection. Defaults to "english".
        sentences_count (int, optional): Number of sentences to result. Defaults to 1.

    Returns:
        str: string of summarized text.
    """
    parser = PlaintextParser.from_string(text, Tokenizer(language))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentences_count)
    return ' '.join([str(sentence) for sentence in summary])


class JavaProgram():
    """Class represents a Java AST Tree.
    """
    def __init__(self, javaAST : dict):
        """Set up the class. Requires AST.

        Args:
            javaAST (dict): AST
        """
        self.ast = javaAST
    
    def getTokens(self):
        """Get the various class names and imports used in the AST.

        Returns:
            dict:
               tokens: Names of classes
               imports: Fully qualified class names via imports
        """
        ast = self.ast

        self.tokens = {
            "tokens" : set(tokens.pullToken(ast)),
            "imports" : set(tokens.pullImport(ast))

        }
        return self.tokens
    
    def matchImports(self):
        """Match imports to the tokens.

        Returns:
            list: Data structure with the tokens
                  matched to the full class name based off of imports.
        """
        result = {}
        importItems = {}
        for i in self.tokens["imports"]:
            params = i.split(".")
            name = params[-1]
            if(name in importItems):
                importItems[name].append(i)
            else:
                importItems[name] = [i]

        for token in self.tokens["tokens"]:
            # check to see if it is in the imports.
            # if not, check lang
            # if not, fail
            if(token in importItems):
                result[token] = importItems[token]
            else:
                result[token] = 0
        return result


class DocumentationSearch():
    """Class representing the documentation folder structure.
    """
    def __init__(self):
        self.docPath = "javaDocs/html/api/"
        self.numSlash = len(self.docPath.split("/"))
    
    def indexTokens(self):
        """Find all possible class names in a dictionary. Index the list.

        Returns:
            dict: Data structure of the index of class names.
        """
        #
        # get all the possible tokens here
        #
        # return a dictionary with the key being the full name, and the value being the filename relative to self.docPath
        #

        modules = os.walk(self.docPath)
        layerOne = next(modules)
        allModules = set()
        for module in layerOne[1]:
            if(module.split(".")[0] in set("java")):
                allModules.add(module)
        
        ignore = {"class-use","doc-files"}
        index = {}
        for layer in modules:
            path = layer[0].replace('\\','/')
            currentDirectoryEnd = os.path.basename(path)

            if(currentDirectoryEnd in allModules):
                continue # go down to layer two

            if(currentDirectoryEnd in ignore or currentDirectoryEnd.find('-') != -1):
                ignore.add(currentDirectoryEnd)
                continue
            
            files = layer[2]
            for file in files:
                filename, ext = os.path.splitext(file)
                if(ext != '.html'):
                    continue
                
                tokens = path.split('/')[self.numSlash:]
                absoluteID = ""
                for token in tokens:
                    absoluteID += token + "."
                absoluteID += filename
                index[absoluteID] = path + "/" + filename + ext

        self.indexedTokens = index
        return self.indexedTokens
    
    def getDocumentationFile(self, fullName):
        """Get the documentation file name from the full class name.

        Args:
            fullName (str): the fully qualified class name

        Returns:
            str: filename of class's documentation.
        """
        if(fullName in self.indexedTokens):
            return self.indexedTokens[fullName]
        else:
            return "Not Found"
    
    def findMissingImports(self, ins):
        """Find a class from index without knowing the qualified name.

        Args:
            ins (str): class name

        Returns:
            dict: Data Structure of updated index with the unknown classes.
        """
        importItems = {}
        for i in self.indexedTokens:
            params = i.split(".")
            name = params[-1]
            if(name in importItems):
                importItems[name].append(i)
            else:
                importItems[name] = [i]
        
        for item in ins:
            if(ins[item] != 0):
                continue
            if(item in importItems):
                ins[item] = importItems[item]
        return ins
            

class JavaDocumentation():
    """Class representing a single documentation file.
    """
    def __init__(self, docName):
        """Set up the documentation and parse.

        Args:
            docName (str): The documentation filename.
        """
        self.filename = docName
        self.description = None
        self.parse()

    def parse(self):
        """Parse the documentation and extract the description.
        """
        #
        #  Parse the HTML here.
        #

        with open(self.filename) as fp:
            soup = BeautifulSoup(fp, 'html.parser')

        self.description = soup.find('div', attrs={'class': 'block'}).text
    
    def getClassCategory(self):
        """Use a LLM to categorize the class based off of the description.
        """
        gptResponse = askGPT_ClassDescription(self.description)
        counter = 0
        answer = ""
        for chunk in gptResponse:
            if chunk.choices[0].delta.content:
                answer += (chunk.choices[0].delta.content.strip('*') or "")
        return answer

    def getDescription(self):
        """Return Description of class.

        Returns:
            str: description
        """
        return self.description
    
    def getMethodDescription(self, methodName):
        """Get the method description from the class.

        Args:
            methodName (str): The method name

        Returns:
            str: The description of the method name.
        """

        with open(self.filename) as fp:
            soup = BeautifulSoup(fp, 'html.parser')

        elements = soup.select_one(f'section[id*="{methodName}("]')
        if(elements is None):
            return None

        methodText = elements.find('p')

        if(methodText is None):
            return None    
        
        methodText = methodText.text
        return methodText
    
def displayPrint(ds, token):
    """Return description and category of a class.

    Args:
        ds (DocumentationSearch): The documentation search manager class.
        token (str): The full qualified class name.

    Returns:
        str: The description of the class
        str: The category of the class using AI.
    """
    file = ds.getDocumentationFile(token)
    description = file
    category = None
    if(file == "Not Found"):
        description = "No documentation available!"
    else:
        doc = JavaDocumentation(file)
        description = doc.getDescription()
        category = doc.getClassCategory()
    return description, category

def compileSymbolClasses(tokenList, symbols, methods):
    """Match methods and symbols and class names into a combined data structure.

    Args:
        tokenList (dict): Token (class name) data structure.
        symbols (dict): Symbol (variable name) data structure.
        methods (dict): Method (method name) data structure.

    Returns:
        dict: Data Structure of compiled symbols, methods, and classes.
    """
    out = {}
    for className in tokenList:
        out[className] = {"full" : tokenList[className], "varlist" : []}

        for num, variable in enumerate(symbols):
            if(variable["class"] != className):
                continue
            variableName = variable["name"]
            lineNumber = variable["line"]

            nextLine = -1
            for vr in symbols[num+1:]:
                # see if there are any more!
                if(vr["class"] != className):
                    continue
               # if(variable["line"] > lineNumber):
                nextLine = vr["line"] - 1
                break # CHECK! We may need to move this back.


            methodOut = []
            for method in methods:
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

def printClassVariables(datastore, ds):
    """User Interface function printing all information

    Args:
        datastore (dict): Combined Data Structure with variable names, class names, and method names.
        ds (DocumentationSearch): Documentation Folder Manager
    """
    
    c = datastore['full']
    docs = None
    if(isinstance(c, int)):
        docs = None
        classname = "Unknown"
    else:
        classname = datastore['full'][0]
        file = ds.getDocumentationFile(c[0])
        if(file != "Not Found"):
            docs = JavaDocumentation(file)

    print(f"Your class: {classname} is used by {len(datastore['varlist'])} variables.")
    if(len(datastore['varlist']) == 0):
        return
    print(f"\nVariable List: ")
    counter = 1
    for var in datastore["varlist"]:
        print(f"\t {counter}) {var['variable']['name']} - defined on line: {var['variable']['line']}")
        counter += 1
    vars = datastore["varlist"]
    
    print("What variable would you like to look in depth? ")
    vInput = input("\? ")
    try:
        vInput = int(vInput) - 1
        v = vars[vInput]
    except:
        vInput = 0
    
    print("="*10)
    print(f"Variable Selected: {vars[vInput]['variable']['name']} at line {vars[vInput]['variable']['line']}")
    
    if(len(vars[vInput]["methods"]) == 0):
        print("\tNo methods used!")
        return 
    methodSearch = []

    for method in vars[vInput]["methods"]:
        print(f"\t{method['method']} at line {method['line']}")
        mname = method['method']
        if(not(mname in methodSearch)):
            methodSearch.append(mname)
    
    print("About the methods:")
    for m in methodSearch:
        if docs is None:
            print(f"\t{m} - Unknown class")
            continue
        
        desc = docs.getMethodDescription(m)
        if(desc is None):
            desc = "No Description Available"
        print(f"\t{m} - {summarize(desc)}")


    

if __name__ == "__main__":


    # get AST from JSON.
    fp = open("generatedFiles/saved.ast.json")
    ast = json.load(fp)
    fp.close()

    pgrm = JavaProgram(ast)
    rawTokens = pgrm.getTokens() # returns all class names
    matched = pgrm.matchImports() # converts all class names to full names.

    ds = DocumentationSearch()
    ds.indexTokens()
    tokenList = ds.findMissingImports(matched)  # maps it to the fully qualified names

    pgrmTables = SymbolTable(ast)
    symbols = pgrmTables.findSymbols() # gets all classes with variable names.
    methods = pgrmTables.getMethods() # gets all methods from variable name.

    compiledData = compileSymbolClasses(tokenList, symbols, methods)

            # matching variable name to item.

    while True:
        print("=="*20)
        print("What class would you like to find the documentation for?")
        counter = 0
        inputMap = {}
        for token in tokenList:
            name = token
            longNames = tokenList[token]
            display = ""
            if(longNames == 0):
                display = "unknown"
            elif(len(longNames) == 1):
                display = longNames[0]
            else:
                display = "Possible matches: "
                for x in longNames:
                    display += x + " "
            counter += 1
            inputMap[counter] = name
            print(f"  {counter}) {name} ({display})")
        print("  e) exit")
        value = input("/? ")
        
        try:
            v = int(value)
        except:
            print("You pressed a letter. Quitting program.")
            exit()
        
        if(not(v in inputMap)):
            print("Invalid option! Quitting program.")
            exit()
        
        print("="*20)
        print("Querying the AI class categorizer... please stand by....")

        description = ""
        chosenToken = tokenList[inputMap[v]]
        if(chosenToken == 0):
            description = "Unknown!"
            print(f"\n{chosenToken}\n{description}\n")

            print("="*20)
            printClassVariables(compiledData[inputMap[v]], ds)

            
            continue
            
        elif(len(chosenToken) == 1):
            
            description, category = displayPrint(ds, chosenToken[0]) 
            description = "\t" + description.replace("\n","\n\t")
            print(f"\n{chosenToken[0]} - \n AI Generated Category: \n {category} \n")

            print(f"--- end of AI Categorizer ---- \n {description}\n")
                              
            print("="*20)
            printClassVariables(compiledData[inputMap[v]], ds)
            
            
            continue
        
        print("Multiple options!")

        for token in chosenToken:
            print("===")
            description, category = displayPrint(ds, token)
            description = description.replace("\n","\t\n")
            print(f"\n{token} - \n AI Generated Category: \n {category} \n")

            print(f"--- end of AI Categorizer ---- \n {description}\n")
            print("="*20)
            printClassVariables(compiledData[inputMap[v]], ds)

        
