"""
GenerateAST.py

This file generates a AST from a java source file.
To do this, it uses the tree_sitter library which in turn
calls a java parser. This approach means that it is configured to
accept any and all java programs and syntaxes.

Anonymous
2/13/2024
"""

import json
import os
import sys

import tree_sitter_java
from tree_sitter import Language, Parser


# Determine the shared library extension based on the platform
if os.name == "posix" and sys.platform.startswith("darwin"):
    shared_library_extension = ".dylib"
else:
    shared_library_extension = ".so"

# # Build the Java language library
# Language.build_library(
#     # Store the library in the `build` directory
#     f"tree-sitter-java/libtree-sitter-java{shared_library_extension}",
#     # Include one or more languages
#     ["tree-sitter-java"],
# )

# Build the Python language library
# Language.build_library(
#     # Store the library in the `build` directory
#     f"tree-sitter-python/libtree-sitter-python{shared_library_extension}",
#     # Include one or more languages
#     ["tree-sitter-python"]
# )
#
# # Build the C++ language library
# Language.build_library(
#     # Store the library in the `build` directory
#     f"tree-sitter-cpp/libtree-sitter-cpp{shared_library_extension}",
#     # Include one or more languages
#     ["tree-sitter-cpp"]
# )
#
# # Build the C language library
# Language.build_library(
#     # Store the library in the `build` directory
#     f"tree-sitter-c/libtree-sitter-c{shared_library_extension}",
#     # Include one or more languages
#     ["tree-sitter-c"]
# )
#
# # Build the C# language library
# Language.build_library(
#     # Store the library in the `build` directory
#     f"tree-sitter-c-sharp/libtree-sitter-c_sharp{shared_library_extension}",
#     # Include one or more languages
#     ["tree-sitter-c-sharp"]
# )


def dict_to_json(input_dict: dict):
    """Convert a dictionary to JSON

    Args:
        input_dict (dict): the dictionary

    Returns:
        str: the JSON output
    """

    default = lambda o: str(o)
    return json.dumps(input_dict, indent=1, default=default, skipkeys=True)


def tree_to_dict(walk_pointer):
    """
    Convert an abstract syntax tree into a dictionary.
    This uses a post-order traversal technique. Goto children, then go to child's sibling.

    Args:
        walkPointer (): The parse tree context.

    Returns:
        dictionary of it and it's children
    """
    # get all field names.
    # for each field name, get it's value.
    # If value is a node, recursive!

    local_data: dict = {"name": walk_pointer.node.grammar_name}

    local_data["children"] = []

    if walk_pointer.goto_first_child():
        local_data["children"].append(tree_to_dict(walk_pointer))

        while walk_pointer.goto_next_sibling():
            local_data["children"].append(tree_to_dict(walk_pointer))

        walk_pointer.goto_parent()

    # value!
    extra = {
        "kind_id": walk_pointer.node.kind_id,
        "grammar_id": walk_pointer.node.grammar_name,
        "type": walk_pointer.node.type,
        "is_named": walk_pointer.node.is_named,
        "is_extra": walk_pointer.node.is_extra,
        "has_changes": walk_pointer.node.has_changes,
        "has_error": walk_pointer.node.has_error,
        "is_error": walk_pointer.node.is_error,
        "start_byte": walk_pointer.node.start_byte,
        "end_byte": walk_pointer.node.end_byte,
        "start_point": [
            walk_pointer.node.start_point[0],
            walk_pointer.node.start_point[1],
        ],
        "end_point": [walk_pointer.node.end_point[0], walk_pointer.node.end_point[1]],
        "child_count": walk_pointer.node.child_count,
        "named_child_count": walk_pointer.node.named_child_count,
        "text": walk_pointer.node.text.decode(),
    }
    local_data = {**local_data, **extra}

    # done.
    return local_data


def generate_ast(filename):
    """
    TODO.
    """

    file_end = filename.strip().split(".")[-1]
    language_library = ""
    # return dictionary AST.
    if file_end == "java":
        language_library = tree_sitter_java.language()
    # elif file_end == "py":
    #     language_library = tree_sitter_python.language()
    #     file_end = "python"
    # elif file_end == "c":
    #     language_library = tree_sitter_c.language()
    # elif file_end == "cpp":
    #     language_library = tree_sitter_cpp.language()
    # elif file_end == "cs":
    #     language_library = tree_sitter_cs.language()
    #     file_end = "c_sharp"
    # elif file_end == "html":
    #     language_library = tree_sitter_html.language()
    # elif file_end == "css":
    #     language_library = tree_sitter_css.language()
    # elif file_end == "js":
    #     language_library = tree_sitter_js.language()
    #     file_end = "javascript"
    else:
        raise ValueError(
            "Unsupported language. "
            "Supported options: java, python, C, C#, C++, HTML, Javascript, CSS. "
            "Given: " + file_end
        )
    # return dictionary AST.
    # JAVA_LANGUAGE = Language("tree-sitter-java/libtree-sitter-java.{shared_library_extension}","java")

    file_language = Language(language_library)

    parser = Parser()
    parser.set_language(file_language)

    # file_path, file_name = filename.rsplit('/', 1)

    with open(filename, "rb") as file:
        tree = parser.parse(file.read())

    tree_walk = tree.walk()

    # run recursive loop
    return tree_to_dict(tree_walk)


# maybe create a separate function that pulls the files from github?

# print("File Path: " + file_path)
# print("File Name: " + file_name)
# code_pull = github_pull.get_github_file_content('JabRef', 'jabref', file_path, file_name)

# if code_pull is not None or code_pull:
#     print("YIPPEE")
#     saveFile = open("output/code_pulled.java", 'w')
#     saveFile.write(code_pull)
#     saveFile.close()

#     file = open('output/code_pulled.java','rb')
#     tree = parser.parse(file.read())
#     file.close()

#     treeWalk = tree.walk()

#     # run recursive loop
#     return populateDictionary(treeWalk)

# else:
#     try:
#         file = open("./jabref-5.0-alpha/" + filename.strip(' '), 'rb')
#         tree = parser.parse(file.read())
#         file.close()

#     except Exception as e:
#         return

#     treeWalk = tree.walk()
#     # run recursive loop
#     return populateDictionary(treeWalk)


# maybe create a separate function that does this?

# input_files = csv_pull.pull_csv('./issues_data2.csv', 'PR Files')
# for file in input_files:
#     file_name = file.strip().split('/')[-1]
#     file_path = "./output/" + str(file_name) + "_ast.json"
#     if not os.path.exists(file_path):
#         result = jsonIt(generateAST(file))
#         if result != 'null':
#             with open(file_path, 'w') as f:
#                 f.write(str(result))
#         else:
#             print(file + " not found")
#     else:
#         print(file + " already converted")


# if __name__ == "__main__":
#     # fname = ""
#     # fname = "./samples/TimerUI.cs"
#     # fname = "./samples/Scheduler.cpp"
#     # fname = "./samples/Scheduling.c"
#     # fname = "./samples/Functionality.js"
#     # fname = "./samples/Design.css"
#     # fname = "./samples/Page.html"
#     fname = "./samples/FieldFactory.java"
#     # fname = "./Unused?/batchProcessing.py"
#     # if(len(sys.argv) > 1):
#     #     fname = sys.argv[1]
#     # else:
#     #     print("Please pass in the file to analyze as a option. Like this: python3 generateAST.py simpleClass.java")
#     #     exit()
#     result = jsonIt(generateAST(fname))
#
#     # save to file.
#     saveFile = open("output/saved.ast.json",'w')
#     saveFile.write(result)
#     saveFile.close()
#     print("AST Generated")
