import json
import AI_Taxonomy
#Hunter Jenkins
#May 13
#Parsing AST to pass into taxonomy, UNCOMPLETED
#Overview about issues and improvements below
# Method and Function are the same comments and code

def load_data(filename):
    with open(filename, 'r') as file:
        return json.load(file)

#Get the list of every API
def extract_imports(ast):
    imports = []
    for node in ast.get('children', []):
        if node.get('type') == 'import_declaration':
            full_import_name = node.get('text', '').replace('import ', '').strip(';')
            imports.append(full_import_name)
    return imports

#Compare APIs and the connected functions
#It is important we know what API a function/variable is from
def find_method_calls_and_identifiers(node, apis):
    api_methods = {api: [] for api in apis}  # Initialize dictionary to hold methods for each API

    def traverse(node):
        if isinstance(node, dict):
            # Check for method invocations and match them against known APIs
            #Here is where I was confused
            if node.get('type') == 'method_invocation':
                identifier = node.get('text', '')
                for api in apis:
                    # If the identifier contains the API, add it to the dictionary under that API
                    if api.split('.')[-1] in identifier:
                        #print(f"Found Method Call: {identifier} for API: {api}")
                        api_methods[api].append(identifier)
            
            # Recursively search through dictionary
            for value in node.values():
                traverse(value)
        
        elif isinstance(node, list):
            # Iterate over list elements
            for item in node:
                traverse(item)

    traverse(node)
    return api_methods

#This is the main thing part, passing in these APIS, and functions into the AI_Taxonomy file. Here we can also add printing to the specefic CSV as well
#More is stated below but basically if we get the top part working 100% everything should fall into place

def classify_apis_and_methods(data, apis):
    api_domain_info = {}
    for api in apis:
        domain, description = AI_Taxonomy.classify_API('labels.json', api)
        api_domain_info[api] = {'domain': domain, 'description': description}
        print("---------------------------------------------") #fill with csv in future for all prints here
        print(f"API : '{api}' \nDomain : {description}\n")
        methods = api_methods[api]
        for method in methods:
            sub_domain = AI_Taxonomy.classify_function(api, method, domain, 'Merged_API_Sub_Domains_Descriptions.json')
            print(f"\tMethod: '{method}' \n\t\tSub-Domain: '{sub_domain}'\n") #this prints the methods found for each API


# Usage example
AST_filename = 'test.json'
AST_data = load_data(AST_filename)
function_filename = 'Merged_API_Sub_Domains_Descriptions.json' #Dont Change, Specefic File Needed in Folder
function_data = load_data(function_filename) #Load this File 

apis = extract_imports(AST_data)
api_methods = find_method_calls_and_identifiers(AST_data, apis)
classify_apis_and_methods(AST_data, apis)


#Overview.. so what is the problem two things. One it seems that the APIs are not all imported at least when taking a look at the orginal java file I used
# for test. Second, I was still kind of confused on how Ben stored the functions because it was pretty complex, some of these functions look good
# other make no sense at all which is concerning. Ben you may have to alter this so it aligns with it better
# some things to take not, i included really no ui because htat is something we habe to add after the facts
# the main thing is that we are going to be testing this on thounsands of files so it needs to somehow run simutously we dont want them to have
# to select one file at a time, that is where dylan comes in with creating the ASTs for the changed files
# Heres what I think we can do, improve this and then basically write another python file that passes in all the ASTs into this and it should work well


# Status Update: (5/14/2024)
# Cleaned up the big algorithm and created a JavaProgram class where one can extract the functions and classnames from a java file. 
# This is in the ProgramAnalyzer.py file (currently on the dev branch.... the taxonomy branch will be merged into the dev branch).