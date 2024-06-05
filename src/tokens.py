import json

# Load JSON data from file
# filename = './output/saved.ast.json'
# with open(filename, 'r') as file:
#     data = json.load(file)

# Function to recursively search for identifiers starting by searching for "local_variable_declaration" then going to its child "identifiers"
def pullToken(jsonDirect, key="type_identifier"):
    """Finds the class names in a java file. "Tokens"

    Args:
        jsonDirect (dict): AST Tree JSON fragment
        key (str, optional): Search key. Defaults to "type_identifier".

    Returns:
        list: List of tokens matching the key.
    """
    tokens = []

    if isinstance(jsonDirect, dict):
        if jsonDirect.get("type") == key or jsonDirect.get("type") == "boolean_type": # If node is a type_identifier, get its text value
            text_value = jsonDirect.get("text")
            if text_value:  #check text value isnt empty
                # print(f"Found Token: {text_value}") #outputs the identifier when found for debugging
                tokens.append(text_value)

        # else recursively search through dictionary
        else:
            for value in jsonDirect.values():
                tokens.extend(pullToken(value, key))

    #iterates over list
    elif isinstance(jsonDirect, list):
        for item in jsonDirect:
            tokens.extend(pullToken(item, key))

    return tokens


def pullTokenPython(jsonDirect, key="assignment", keyChild="identifier"):
    tokens = []

    if isinstance(jsonDirect, dict):
        if jsonDirect.get("type") == key:  # If node is a type_identifier, get its text value
            for child in jsonDirect.get("children", []):
                if child.get("name") == keyChild:
                    text_value = child.get("text")
                    if text_value:  # check text value isnt empty
                        # print(f"Found Token: {text_value}") #outputs the identifier when found for debugging
                        tokens.append(text_value)

        # else recursively search through dictionary
        else:
            for value in jsonDirect.values():
                tokens.extend(pullTokenPython(value, key, keyChild))

    # iterates over list
    elif isinstance(jsonDirect, list):
        for item in jsonDirect:
            tokens.extend(pullTokenPython(item, key, keyChild))

    return tokens

def pullImport(jsonDirect, key="scoped_identifier"):

    imports = []

    if isinstance(jsonDirect, dict):
        if jsonDirect.get("type") == key or jsonDirect.get("grammar_id") == key: # If node is a type_identifier, get its text value
            text_value = jsonDirect.get("text")
            if text_value:  #check text value isnt empty
                # print(f"Found Identifier: {text_value}") #outputs the identifier when found for debugging
                imports.append(text_value)

        # else recursively search through dictionary
        else:
            for value in jsonDirect.values():
                imports.extend(pullImport(value, key))

    #iterates over list
    elif isinstance(jsonDirect, list):
        for item in jsonDirect:
            imports.extend(pullImport(item, key))

    return imports


def pullImportPython(jsonDirect, key="dotted_name"):
    imports = []

    if isinstance(jsonDirect, dict):
        if jsonDirect.get("type") == key or jsonDirect.get(
                "grammar_id") == key:  # If node is a type_identifier, get its text value
            text_value = jsonDirect.get("text")
            if text_value:  # check text value isnt empty
                # print(f"Found Identifier: {text_value}") #outputs the identifier when found for debugging
                imports.append(text_value)

        # else recursively search through dictionary
        else:
            for value in jsonDirect.values():
                imports.extend(pullImportPython(value, key))

    # iterates over list
    elif isinstance(jsonDirect, list):
        for item in jsonDirect:
            imports.extend(pullImportPython(item, key))

    return imports



# found_tokens = pullToken(data)
# print(found_tokens)
