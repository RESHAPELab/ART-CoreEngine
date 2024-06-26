import generate_ast
import tokens as tokenExtract
from symbol_table import SymbolTable
import builtins
import java_ast
import python_ast

#inputProgram = "../test/samples/AutosaveManager.java"
inputProgram = "../test/samples/GetDomains.py"

# result = generateAST.jsonIt(generateAST.generateAST(inputProgram))

# print(generateAST.generateAST(inputProgram))

file_end = inputProgram.strip().split('.')[-1]

if file_end == "java":
    result = java_ast.JavaProgram(generate_ast.generate_ast(inputProgram))
elif file_end == "py":
    result = python_ast.PythonProgram(generate_ast.generate_ast(inputProgram))


plain_classes = result.getClasses()  # converts all class names to full names.
functions = result.getFunctions().keys()


# print(result.symbols)
# print(result.methods)

print(plain_classes)
# print(result.completeTable)
print(functions)
