
import glob
import itertools
import json
from multiprocessing import Pool
import time
from chatgpt import askGPT_ClassDescription, askGPT_FunctionDescription
from generateAST import generateAST, jsonIt
from main import JavaDocumentation, JavaProgram, DocumentationSearch, compileSymbolClasses, summarize
from symbolTable import SymbolTable
import hashlib
import os
import tqdm

def printDebug(s):
    if False:
        print(s)

def apiProcessClass(dataset, cache, className): # rate target: 4 per minute on average (4 procs, 60sec avg wait time for 1 query)
    description = dataset[className]

    if(className in cache):
        return cache[className]
    
    return None
    timeDelay = int(hashlib.md5(className.encode()).hexdigest(), 16) % 120 
    print(f"AI query for {className}. Delaying for {timeDelay} seconds")
    time.sleep(timeDelay)
    return {"className": className, "summary":summarize(description, sentences_count = 2), "llm" : askGPT_ClassDescription(description)}

def apiProcessFunction(dataset, cache, funcName):
    description = dataset[funcName]

    if(funcName in cache):
        return cache[funcName]
    
    return None
    timeDelay = int(hashlib.md5(funcName.encode()).hexdigest(), 16) % 180 # rate target: 2.67 per minute on average (4 procs, 90 sec avg wait time for 1 query)
    print(f"AI query for {funcName}. Delaying for {timeDelay} seconds")
    time.sleep(timeDelay)
    return {"functionName": funcName, "summary":summarize(description, sentences_count = 2), "llm" : askGPT_FunctionDescription(description,funcName.split(":")[0])}



#function to return all file names in directory and all sub directories
def storeFilenames():
    allFilenames = []     

    for dirpath, dirnames, filenames in os.walk(os.getcwd()):
        for filename in filenames:
            if filename.endswith('.java'):
                fullPath = os.path.join(dirpath, filename)
                allFilenames.append(fullPath)
    return allFilenames

cacheClassDescriptions = {}
cacheFunctionDescriptions = {}

def processFile(fname="filename.java", cacheName="cache.json"):
    # get ast.
    # return all classes used - classList and simpleDataReferenceTree
    # return all non-primitive variables used with class names - symbols and simpleDataReferenceTree
    # return all the functions used - methods and simpleDataReferenceTree
    # return the LLM domain of the class - classDomains
    # return class description - in classDescriptions
    # return class summary - in classSummaries
    #
    # return all the descriptions of the functions - in functionDescriptions.
    # return all the summaries of the descriptions of the functions - functionSummaries
    # return the LLM domain of the functions - in functionDomains

    printDebug("Generate AST")

    ast = generateAST(fname)

    printDebug("Parse AST")

    pgrm = JavaProgram(ast)
    pgrm.getTokens()

    # find the full qualified name
    docSearch = DocumentationSearch()
    docSearch.indexTokens()
    classList = docSearch.findMissingImports(pgrm.matchImports())

    symbolTableManager = SymbolTable(ast)
    symbols = symbolTableManager.findSymbols()
    methods = symbolTableManager.getMethods()

    compiledData = compileSymbolClasses(classList, symbols, methods)
    
    printDebug("Fetch Class Documentations")

    # documentations.
    # class doc.
    out = {}
    for className in classList:
        if(classList[className] == 0):
            continue # unknown! Not in JavaSDK
        
        for fullName in classList[className]:
            if(fullName in cacheClassDescriptions):
                out[fullName] = cacheClassDescriptions[fullName]
                continue

            docName = docSearch.getDocumentationFile(fullName)
            if(docName == "Not Found"):
                continue # unknown! Not in JavaSDK!

            jDoc = JavaDocumentation(docName)
            jDoc.parse()
            out[fullName] = jDoc.getDescription()
            cacheClassDescriptions[fullName] = out[fullName]
    
    classDescriptions = out
    
    printDebug("Fetch Function Descriptions")
    
    # get function descriptions.
    # KEY: class and function. Add to compiled data.
    functionDescriptions = {}
    for className in compiledData:
        data = compiledData[className]
        if(data["full"] == 0):
            continue # unknown. Not in JavaSDK.

        methodsGeneral = []
        for varl in data["varlist"]:
            for m in varl["methods"]:
                methodsGeneral.append(m)
        
        for fullName in data["full"]:

            docName = docSearch.getDocumentationFile(fullName)
            if(docName == "Not Found"):
                continue # unknown! Not in JavaSDK!

            jDoc = None

            for m in methodsGeneral:
                mName = m["method"]
                if(f"{fullName}::{mName}" in functionDescriptions):
                    continue
                # is None if not found!

                if(f"{fullName}::{mName}" in cacheFunctionDescriptions):
                    functionDescriptions[f"{fullName}::{mName}"]  = cacheFunctionDescriptions[f"{fullName}::{mName}"]
                    continue
                
                if(jDoc == None):
                    jDoc = JavaDocumentation(docName)
                    jDoc.parse()

                functionDescriptions[f"{fullName}::{mName}"] = jDoc.getMethodDescription(mName)
                cacheFunctionDescriptions[f"{fullName}::{mName}"] = jDoc.getMethodDescription(mName)

    
    # printDebug(jsonIt(compiledData))
    # # printDebug("\n=============")
    # printDebug("HELLO!")
    # printDebug(jsonIt(list(functionDescriptions.keys())))
    # printDebug("\n=============")
    # printDebug(jsonIt(compiledData))
    # printDebug("\n==========")
    # printDebug(jsonIt(classDescriptions))
    # printDebug("\n==========")
    # printDebug(jsonIt(functionDescriptions))
    # printDebug("\n==========")
    

    # AI section!
    printDebug("AI Section 1/2 - fetch Class Summaries and Domains")
    
    classDomains = {} # matches classDescriptions.
    classSummaries = {}

    try:
        cacheF = open(cacheName)
        cache = json.load(cacheF)
        cacheF.close()
    except:
        cache = {"classes":{}, "functions":{}}

    printDebug(list(classDescriptions.keys()))

    rawOut = []
    with Pool(processes=4) as p: # use parallel processing to make multiple queries at once! 
        rawOut = p.starmap(apiProcessClass,zip(itertools.repeat(classDescriptions),itertools.repeat(cache["classes"]),classDescriptions.keys()))
    
    for x in rawOut:
        if(x is None):
            continue

        cache["classes"][x["className"]] = x
        classDomains[x["className"]] = x["llm"]
        classSummaries[x["className"]] = x["summary"]

    ch = jsonIt(cache)
    
    f = open(cacheName,'w')
    f.write(ch)
    f.close()
    printDebug("AI Section 2/2 - fetch Function Summaries and Domains")

    printDebug(list(functionDescriptions.keys()))

    rawOut = []
    with Pool(processes=4) as p: # use parallel processing to make multiple queries at once! 
        rawOut = p.starmap(apiProcessFunction,zip(itertools.repeat(functionDescriptions),itertools.repeat(cache["functions"]),functionDescriptions.keys()))
    
    functionDomains = {}
    functionSummaries = {}
    for x in rawOut:
        if(x is None):
            continue

        cache["functions"][x["functionName"]] = x
        functionDomains[x["functionName"]] = x["llm"]
        functionSummaries[x["functionName"]] = x["summary"]
    
    # OUTPUT DATA!

    output = {
        "simpleDataReferenceTree":compiledData,
        "symbols":symbols,
        "methods":methods,
        "classList":classList,
        "classDescriptions":classDescriptions,
        "functionDescriptions":functionDescriptions,
        "classDomains":classDomains,
        "classSummaries":classSummaries,
        "functionDomains":functionDomains,
        "functionSummaries":functionSummaries     
        }
    
    ch = jsonIt(cache)
    
    f = open(cacheName,'w')
    f.write(ch)
    f.close()
    
    printDebug("Done!")

    return output

    
if __name__ == "__main__":
    fnames = storeFilenames()
    outs = []

    for fName in tqdm.tqdm(fnames):
        out = processFile(fName, "generatedFiles/LLMcache.json")

        finalResult = {"fileName" : fName, "data" : out}
        outs.append(finalResult)

        saveFile = open("generatedFiles/savedReport.json",'w')
        saveFile.write(jsonIt(outs))
        saveFile.close()

