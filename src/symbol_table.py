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
