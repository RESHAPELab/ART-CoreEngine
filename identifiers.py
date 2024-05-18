import json

# Load JSON data from file
# filename = './generatedFiles/saved.ast.json'
# with open(filename, 'r') as file:
#     data = json.load(file)


########
# Is this to find variables? 
# I think this file is now old and can be safely deleted,
# As this is now included in the symbolTable.py program.
########

# Function to recursively search for identifiers starting by searching for "local_variable_declaration" then going to its child "identifiers"
def pullIdentifierJava(jsonDirect, key="local_variable_declaration", keyChild="identifier"):

    found_identifiers = [] #list to store our identifiers

    if isinstance(jsonDirect, dict):
        if jsonDirect.get("name") == key: # If node is a local_variable_declaration check its children
            for child in jsonDirect.get("children", []):
                if child.get("name") == keyChild:
                    text_value = child.get("text")
                    if text_value:  #check text value isnt empty
                        print(f"Found Identifier: {text_value}") #outputs the identifier when found for debugging
                        found_identifiers.append(text_value)
        
        # else recursively search through dictionary
        else:
            for value in jsonDirect.values():
                found_identifiers.extend(pullIdentifierJava(value, key, keyChild))
    
    #iterates over list
    elif isinstance(jsonDirect, list):
        for item in jsonDirect:
            found_identifiers.extend(pullIdentifierJava(item, key, keyChild))
    
    return found_identifiers


def pullIdentifierPython(jsonDirect, key="assignment", keyChild="identifier"):
    found_identifiers = []  # list to store our identifiers

    if isinstance(jsonDirect, dict):
        if jsonDirect.get("name") == key:  # If node is a local_variable_declaration check its children
            for child in jsonDirect.get("children", []):
                if child.get("name") == keyChild:
                    text_value = child.get("text")
                    if text_value:  # check text value isnt empty
                        print(f"Found Identifier: {text_value}")  # outputs the identifier when found for debugging
                        found_identifiers.append(text_value)

        # else recursively search through dictionary
        else:
            for value in jsonDirect.values():
                found_identifiers.extend(pullIdentifierPython(value, key, keyChild))

    # iterates over list
    elif isinstance(jsonDirect, list):
        for item in jsonDirect:
            found_identifiers.extend(pullIdentifierPython(item, key, keyChild))

    return found_identifiers

# found_identifiers = pullIdentifierPython(data)
# print(found_identifiers)