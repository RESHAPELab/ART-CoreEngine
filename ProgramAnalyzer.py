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
from AI_Taxonomy import AIClassifier, load_data
from generateAST import generateAST
import os
from symbolTable import SymbolTable
import tokens as tokenExtract
import csv_pull
from g4f.client import Client
import store_result
import csv_push

client = Client()

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

    # Function to extract and print class names and methods
    def extract_classes_and_methods(self, data):
        result = {}
        for class_name, details in data.items():
            name = str(data[class_name].get('full', class_name)).strip("['']")
            for var_info in details['varlist']:
                variable_class = var_info['variable']['class']
                methods = var_info['methods']
                method_names = {method['method'] for method in methods}  # Use a set to avoid duplicates
                if variable_class in result:
                    if name != "0":
                        result[name].update(method_names)
                    else:
                        result[variable_class].update(method_names)
                else:
                    if name != "0":
                        result[name] = method_names
                    else:
                        result[variable_class] = method_names
        # Ensure all classes are included, even if they have no methods
        for class_name, details in data.items():
            if class_name not in result:
                name = str(data[class_name].get('full', class_name)).strip("['']")
                if name != "0":
                    result[name] = set()
                else:
                    result[class_name] = set()
        return result


def askGPT_ClassDescription(API_file, API):
    # Construct the prompt with the object description and option descriptions
    # Load JSON data from the specified path
    with open(API_file, 'r') as file:
        data = json.load(file)

    # Convert the JSON data into a text format suitable for asking questions
    text = json.dumps(data, indent=2)  # You might still want to convert it to ensure it's readable

    # Directly include the full question in the OpenAI API call
    question = (
    f"Please analyze the provided descriptions and the details of the imported API, then determine the most fitting domain from a list of 31 labels. "
    f"Return like this domain - description, only the name of the selected domain. "
    f"API details: {API}. Context: {text}. Do not include any additional information or reasoning in your response just the domain chosen.")
    messages = [{"role": "user", "content": question}]
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        stream=True
    )

    answer = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            answer += (chunk.choices[0].delta.content.strip('*') or "")
    return answer

def askGPT_FunctionDescription(api_name, function_name, api_domain, sub_domain_file):
    # Construct the prompt with the object description and option descriptions
    # Load JSON data from the specified path
    with open(sub_domain_file, 'r') as file:
        data = json.load(file)

    if api_domain in data:
        sub_domains_descriptions = []
        for item in data[api_domain]:
            for sub_domain, description in item.items():
                # print(f"  - {sub_domain}: {description}")
                sub_domains_descriptions.append(f"{sub_domain}: {description}")

        # Join all sub-domain descriptions into a single string for the query
        sub_domains_descriptions_str = ", ".join(sub_domains_descriptions)

        # Directly include the full question in the OpenAI API call
        question = (
            f"Analyze the following information about the API function '{function_name}' which is part of the '{api_name}' in the '{api_domain}' domain. "
            f"Choose the most relevant classification from these available sub-domain options: {sub_domains_descriptions_str}. "
            f"Please provide only the name of the most appropriate subdomain, without any additional details or explanation just the subdomain chosen."
        )
        messages = [{"role": "user", "content": question}]
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            stream=True
        )

        answer = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                answer += (chunk.choices[0].delta.content.strip('*') or "")
        return answer
    else:
        return f"No sub-domain for function '{function_name}'."



if __name__ == "__main__":

    if(not(os.path.isdir("generatedFiles"))):
        os.makedirs("generatedFiles")
    
    # get AST from JSON.
    ast = generateAST("samples/PreviewViewer.java")
    # fp = open("generatedFiles/saved.ast.json")
    # ast = json.load(fp)
    # fp.close()

    jp = JavaProgram(ast)
    cl = jp.getClasses()
    fn = jp.getFunctions()

    print(cl)
    functions = list(fn.keys())

    #-----------------------
    API_listing_file = 'domain_labels.json' 
    sub_domain_listing_file = 'subdomain_labels.json'
    #-----------------------

    api_domain_listing = load_data(API_listing_file)
    sub_domain_listing = load_data(sub_domain_listing_file)

    classifier = AIClassifier(api_domain_listing, sub_domain_listing)
    
    print(functions[0])
    print(classifier.classify_class_and_function(functions[0]))


    exit()

    input_files = csv_pull.pull_csv('generatedFiles/issues_data2 test.csv', 'PR Files')
    # input_files = ['samples/AutosaveManager.java']
    for file in input_files:
        file = "./jabref-5.0-alpha/" + file.strip(" ")
        # if not os.path.exists(file_path):
        result = (generateAST(file))
        domains = []
        subdomains = []
        if result != 'null' and result is not None:
            pgrm = JavaProgram(result)
            classNames = pgrm.getClasses()  # converts all class names to full names.
            print("##" * 20)
            print("START: " + file)
            #print("\t" + str(classNames))
            #print("*" * 20)
            symbols = pgrm.getCompleteSymbolTable()
            #print("\t" + str(symbols))
            connections = pgrm.extract_classes_and_methods(symbols)
            for class_name, methods in connections.items():
                print(f"\tClass: {class_name} - Methods: {methods}")
                if not store_result.in_csv('generatedFiles/function_storage.csv', class_name):
                    label = askGPT_ClassDescription('labels.json', class_name)
                    store_result.add_to_csv('generatedFiles/function_storage.csv', class_name, label)
                    print(label)
                else:
                    label = store_result.get_from_csv('generatedFiles/function_storage.csv', class_name)
                if label not in domains:
                    domains.append(label)
                if methods:
                    method_list = list(methods)
                    for method in method_list:
                        if not store_result.in_csv('generatedFiles/api_storage.csv', class_name + "-" + method):
                            sub_label = askGPT_FunctionDescription(class_name, method, label, 'Merged_API_Sub_Domains_Descriptions.json')
                            store_result.add_to_csv('generatedFiles/api_storage.csv', class_name + "-" + str(method), label + "-" + sub_label)
                            print(sub_label)
                            sub_label = label + "-" + sub_label
                        else:
                            sub_label = store_result.get_from_csv('generatedFiles/api_storage.csv', class_name + "-" + method)
                        if sub_label not in subdomains:
                            subdomains.append(sub_label)
            print("*" * 20)
            funcs = pgrm.getFunctions()
            #print("\t" + str(funcs))
            print("##" * 20)
            store_result.store_file('generatedFiles/file_data.csv', file.strip('./jabref-5.0-alpha/') + "a", domains, subdomains)
            # result = csv_push.find_values_by_filename('file_data.csv', file.strip('./jabref-5.0-alpha/') + "a")
            # if isinstance(result, tuple):
            #     domains, subdomains = result
            #     print("{" + file.strip('./jabref-5.0-alpha/') + "a" + ": [" + domains + "], [" + subdomains + "]}")
            # else:
            #     print(result)
        else:
            print(file + " not found")
        # else:
        #     print(file + " already converted")

    column_data = csv_pull.read_full_column('generatedFiles/issues_data2 test.csv', 'PR Files')
    results = []

    for file in column_data:
        # Convert the string to an actual array
        array = eval(file)
        array_of_javas = []
        for input in array:
            if input.endswith(".java"):
                array_of_javas.append(input)

        array_of_results = []
        for java_file in array_of_javas:
            result = csv_push.find_values_by_filename('generatedFiles/file_data.csv', java_file)
            if isinstance(result, tuple):
                domains, subdomains = result
                array_of_results.append("{" + java_file + ": [" + domains + "], [" + subdomains + "]}")
            else:
                array_of_results.append(result)
        results.append(array_of_results)

    csv_pull.update_csv_with_results('generatedFiles/issues_data2 test.csv', 'PR Files', results)

    # pgrm = JavaProgram(ast)
    # classNames = pgrm.getClasses() # converts all class names to full names.
    # print(classNames)
    # print("*"*20)
    # symbols = pgrm.getCompleteSymbolTable()
    # print(symbols)
    # print("*"*20)
    # funcs = pgrm.getFunctions()
    # print(funcs)
    

