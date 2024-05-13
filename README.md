# Language Analyzer

By Benjamin Carter, TJ Potter, and Brent McLennan

***
# Part 4:

The database backup can be found here: https://codingcando.com/fileShare/file?code=2NYNWW4131

The modifications are under the `functions` table and the `api_function_spcific` table.

By Benjamin Carter, TJ Potter, and Brent McLennan

***


# Part 3:

Video Link - including the method descriptions and AI generation: [click me](https://codingcando.com/fileShare/file?code=2NMLDJIEEM)

Old Video link: [click me](https://codingcando.com/fileShare/file?code=LZHMW70KS1)

[Updated video link with java docs](https://codingcando.com/fileShare/file?code=JGZHDI5IEO)

# To Use:

Run `python3 generateAST.py (java_file.java)`
Example: `python3 generateAST.py simpleClass.java`
It will output the JSON result onto the terminal, and also save 
the JSON output to the `saved.ast.json` file.

# To parse AST and display documentation.

Run `python3 main.py`. This will load the AST from the saved JSON file and display an interactive prompt to see the documentation for each class used.

# PreReq's
1. Beautiful Soup `pip install bs4`
2. Python Treesitter `pip install tree-sitter`


> See [the tutorial on installing tree_sitter](https://github.com/tree-sitter/py-tree-sitter/tree/master)
> Then, you may need to then go into the `tree-sitter-java` folder and run `make`
