class SymbolTable():
    def __init__(self, ast : dict):
        """Create Symbol Table Object

        Args:
            ast (dict): AST of Java Program.
        """
        self.ast = ast
        self.symbols = []
        self.methodTable = []
    # in class def.
    # formal identifier. func(string A)
    # object_creation_expression

    # used by method invocation.

    # type_identifier -- variable_declarator (brother)

    def findSymbols(self):
        """Find all symbols (variables) used in the program

        Returns:
            list[dict]: Symbol Dictionary. [{class, name, line}, ...]
        """
        # LRP
        self.__findSymbol(self.ast)
        return self.symbols

    def __findSymbol(self, node):
        if(node["name"] == "formal_parameter"):

            typeID = ""
            name = ""
            startPoint = 0

            for x in reversed(node["children"]):
                if(x["type"] == "type_identifier"):
                    typeID = x["text"]
                elif(x["type"] == "identifier"):
                    name = x["text"]
                    startPoint = x["start_point"][0]

            if(typeID != ''):
                self.symbols.append({"class":typeID, "name":name, "line":startPoint})
                # ignore primitives.

            return
        elif(node["name"] == "field_declaration"):

            typeID = ""
            name = ""
            startPoint = 0

            for x in reversed(node["children"]):
                if(x["type"] == "type_identifier"):
                    typeID = x["text"]
                elif(x["type"] == "variable_declarator"):
                    children = x["children"]
                    firstID = children[0]
                    count = 0
                    while children[count]["name"] != "identifier":
                        count += 1
                    name = children[count]["text"] # get first identifier.
                    startPoint = children[count]["start_point"][0]

            if(typeID != ''):
                self.symbols.append({"class":typeID, "name":name, "line":startPoint})
                # ignore primitives.

            return
        elif(node["name"] == "local_variable_declaration"):

            typeID = ""
            name = ""
            startPoint = 0

            for x in reversed(node["children"]):
                if(x["type"] == "type_identifier"):
                    typeID = x["text"]
                elif(x["type"] == "variable_declarator"):
                    children = x["children"]
                    firstID = children[0]
                    count = 0
                    while children[count]["name"] != "identifier":
                        count += 1
                    name = children[count]["text"] # get first identifier.
                    startPoint = children[count]["start_point"][0]

            if(typeID != ''):
                self.symbols.append({"class":typeID, "name":name, "line":startPoint})
                # ignore primitives.
            return

        # see children.
        if(len(node["children"]) == 0):
            return # nothing here!

        for n in node["children"]:
            # check
            self.__findSymbol(n)

        # that's it! Nothing here.

    def getMethods(self):
        """Find all methods and invocations used in the program

        Returns:
            list[dict]: Method Dictionary. [{name (variable name), method, line}, ...]
        """
        self.__getMethod(self.ast)
        return self.methodTable

    def __getMethod(self, node):
        if(node["name"] == "method_invocation"):

            tokens = []
            # tokens, first is X
            # second, is .
            # third, is func

            for x in node["children"]:
                if(x["type"] == "method_invocation"):
                    # go in nest!
                    return self.__getMethod(x)

                if(x["type"] == "identifier"):
                    tokens.append(x["text"])
                    startPoint = x["start_point"][0]

                if(x["type"] == "argument_list"):
                    # it is possible for more!
                    self.__getMethod(x)

            if(len(tokens) >= 2):
                self.methodTable.append({"name":tokens[0], "method":tokens[1], "line":startPoint})
                # ignore primitives.

            return


        # see children.
        if(len(node["children"]) == 0):
            return # nothing here!

        for n in node["children"]:
            # check
            self.__getMethod(n)

        # that's it! Nothing here.

    def findSymbolsPy(self):
        """Find all symbols (variables) used in the program

        Returns:
            list[dict]: Symbol Dictionary. [{class, name, line}, ...]
        """
        # LRP
        self.__findSymbolPy(self.ast)
        return self.symbols

    def __findSymbolPy(self, node):
        def determine_type(node_text):
            try:
                # Check for common literals and basic types
                if node_text.isdigit():
                    return "int"
                elif node_text.replace('.', '', 1).isdigit():
                    return "float"
                elif node_text.startswith("'") and node_text.endswith("'"):
                    return "str"
                elif node_text.startswith('"') and node_text.endswith('"'):
                    return "str"
                elif node_text == "True" or node_text == "False":
                    return "bool"
                elif node_text == "None":
                    return "none"
                # Check for other types
                elif node_text.startswith("[") and node_text.endswith("]"):
                    return "list"  # Check for list literal
                elif node_text.startswith("{") and node_text.endswith("}"):
                    return "dict"  # Check for dictionary literal
                elif node_text.startswith("(") and node_text.endswith(")"):
                    return "tuple"  # Check for tuple literal
                elif node_text.startswith("{") and node_text.endswith("}") and ":" in node_text:
                    return "set"  # Check for set literal
                elif node_text.startswith("b'") and node_text.endswith("'"):
                    return "bytes"  # Check for bytes literal
                elif node_text.startswith("b\"") and node_text.endswith("\""):
                    return "bytes"  # Check for bytes literal
                elif node_text.startswith("bytearray(") and node_text.endswith(")"):
                    return "bytearray"  # Check for bytearray
                elif node_text.startswith("complex(") and node_text.endswith(")"):
                    return "complex"  # Check for complex number
                elif node_text == "...":
                    return "ellipsis"  # Check for ellipsis
                elif node_text.startswith("(") and node_text.endswith(")") and "for" in node_text and "in" in node_text:
                    return "generator"  # Check for generator expression
                elif node_text.startswith("[") and node_text.endswith("]") and "for" in node_text and "in" in node_text:
                    return "list comprehension"  # Check for list comprehension
                elif node_text.startswith("{") and node_text.endswith(
                        "}") and ":" in node_text and "for" in node_text and "in" in node_text:
                    return "dictionary comprehension"  # Check for dictionary comprehension
                elif node_text.startswith("{") and node_text.endswith("}") and "for" in node_text and "in" in node_text:
                    return "set comprehension"  # Check for set comprehension
                elif node_text in {"NotImplemented", "Ellipsis"}:
                    return "constant"  # Check for constants
                elif node_text.startswith("f'") and node_text.endswith("'"):
                    return "f-string"  # Check for f-string
                elif node_text.startswith("f\"") and node_text.endswith("\""):
                    return "f-string"  # Check for f-string
                elif node_text.startswith("u'") and node_text.endswith("'"):
                    return "unicode string literal"  # Check for unicode string literal
                elif node_text.startswith("u\"") and node_text.endswith("\""):
                    return "unicode string literal"  # Check for unicode string literal
                elif node_text.startswith("r'") and node_text.endswith("'"):
                    return "raw string literal"  # Check for raw string literal
                elif node_text.startswith("r\"") and node_text.endswith("\""):
                    return "raw string literal"  # Check for raw string literal
                elif node_text.startswith("@"):
                    return "decorator"  # Check for decorator
                else:
                    try:
                        node_text = node["text"]
                        eval_type = type(eval(node_text, {}, {}))
                        if eval_type == int:
                            return "int"
                        elif eval_type == float:
                            return "float"
                        elif eval_type == str:
                            return "str"
                        elif eval_type == list:
                            return "list"
                        elif eval_type == dict:
                            return "dict"
                        return "UNKNOWN"
                    except:
                        # print(node_text)
                        return "UNKNOWN"
            except:
                # print(node_text)
                return "UNKNOWN"

        if node["name"] == "assignment" or node["name"] == "attribute" or node["name"] == "dotted_name":

            typeID = ""
            name = ""
            startPoint = 0

            # pattern_list, subscript, identifier-text
            for x in reversed(node["children"]):
                if (x["type"] == "identifier"):
                    name = x["text"]
                    typeID = "unknown"
                    startPoint = x["start_point"][0]
                elif (x["type"] == "pattern_list"):
                    for y in reversed(x["children"]):
                        if (y["type"] == "identifier"):
                            name = y["text"]
                            typeID = "unknown"
                            startPoint = x["start_point"][0]
                elif (x["type"] == "subscript"):
                    for y in reversed(x["children"]):
                        if (y["type"] == "identifier"):
                            name = y["text"]
                            typeID = "unknown"
                            startPoint = x["start_point"][0]

            # Determine the type of the right-hand side of the assignment
            if node["name"] == "assignment" and node["children"]:
                value_node = node["children"][-1]  # Assuming the last child is the value
                # print("HERE: " + str(value_node))
                typeID = determine_type(value_node["text"])

            if (typeID != ''):
                self.symbols.append({"class": typeID, "name": name, "line": startPoint})
                # ignore primitives.

            return
        # elif (node["name"] == "call"):
        #
        #     typeID = ""
        #     name = ""
        #     startPoint = 0
        #
        #     for x in reversed(node["children"]):
        #         if (x["type"] == "type_identifier"):
        #             typeID = x["text"]
        #         elif (x["type"] == "variable_declarator"):
        #             children = x["children"]
        #             firstID = children[0]
        #             count = 0
        #             while children[count]["name"] != "identifier":
        #                 count += 1
        #             name = children[count]["text"]  # get first identifier.
        #             startPoint = children[count]["start_point"][0]
        #
        #     if (typeID != ''):
        #         self.symbols.append({"class": typeID, "name": name, "line": startPoint})
        #         # ignore primitives.
        #
        #     return
        # elif (node["name"] == "local_variable_declaration"):
        #
        #     typeID = ""
        #     name = ""
        #     startPoint = 0
        #
        #     for x in reversed(node["children"]):
        #         if (x["type"] == "type_identifier"):
        #             typeID = x["text"]
        #         elif (x["type"] == "variable_declarator"):
        #             children = x["children"]
        #             firstID = children[0]
        #             count = 0
        #             while children[count]["name"] != "identifier":
        #                 count += 1
        #             name = children[count]["text"]  # get first identifier.
        #             startPoint = children[count]["start_point"][0]
        #
        #     if (typeID != ''):
        #         self.symbols.append({"class": typeID, "name": name, "line": startPoint})
        #         # ignore primitives.
        #     return

        # see children.

        if len(node["children"]) == 0:
            return  # nothing here!

        for n in node["children"]:
            # check
            self.__findSymbolPy(n)

    def getMethodsPy(self):
        """Find all methods and invocations used in the program

        Returns:
            list[dict]: Method Dictionary. [{name (variable name), method, line}, ...]
        """
        self.__getMethodPy(self.ast)
        return self.methodTable

    def __getMethodPy(self, node):
        if node["name"] == "call":

            tokens = []
            # tokens, first is X
            # second, is .
            # third, is func

            for x in node["children"]:

                if x["type"] == "attribute":
                    for y in x["children"]:
                        if y["type"] == "call":
                            return self.__getMethodPy(x)
                        if y["type"] == "identifier":
                            tokens.append(y["text"])
                            startPoint = y["start_point"][0]

                # if (x["type"] == "identifier"):
                #     tokens.append(x["text"])
                #     startPoint = x["start_point"][0]

                # if (x["type"] == "argument_list"):
                #     for y in x["children"]:
                #         if (y["type"] == "identifier"):
                #             tokens.append(y["text"])
                #             startPoint = y["start_point"][0]

            if len(tokens) >= 2:
                self.methodTable.append({"name": tokens[0], "method": tokens[1], "line": startPoint})
                # ignore primitives.

            return

        # see children.
        if len(node["children"]) == 0:
            return  # nothing here!

        for n in node["children"]:
            # check
            self.__getMethodPy(n)
