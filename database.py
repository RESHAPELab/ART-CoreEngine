import json
import psycopg2
import tqdm # pip install psycopg2-binary
    

############## DATABASE INFO ###################
name = ""
usr = ""
pswd = ""
################################################

# create function table
def createFunction():
    # connect to database
    conn = psycopg2.connect(
        dbname=name, 
        user=usr, 
        password=pswd, 
        host='localhost',
        port = 5432
    )
    cur = conn.cursor()

    # execute query to create table with pk
    cur.execute("""
                CREATE TABLE public.function
                (
                    function_name character varying,
                    api_name character varying
                );
                """)

    # clean up
    conn.commit()
    cur.close()
    conn.close()

# format data for fucntion table
def formatFunctionData(output):
    f_names, c_names = [], []

    # get classes
    for c, c_data in output['simpleDataReferenceTree'].items():
        if c_data['full'] == 0: continue
        c_name = str(c_data['full'])[2:-2] # api_name

        # get variable list
        for var in c_data['varlist']:
            methods = var['methods']

            # get methods, if any
            if len(methods) != 0:
                for method in methods:
                    f_name = str(method['method']) # function_name

                    # add to respective lists
                    f_names.append(f_name)
                    c_names.append(c_name)
    
    # group data and return
    result = {
        "function_name": f_names,
        "api_name": c_names
    }
    return result


# insert data into function table
def insertFunction(data):
    # connect to database
    conn = psycopg2.connect(
        dbname=name, 
        user=usr, 
        password=pswd, 
        host='localhost',
        port = 5432
    )
    cur = conn.cursor()

    # execute queries to check for distinct data and insert if distinct
    for i in range(len(data['function_name'])):
        f_name, c_name = data['function_name'][i], data['api_name'][i]
        cur.execute(f"SELECT COUNT(*) FROM function WHERE function_name = %s AND api_name = %s", (f_name, c_name))
        count = cur.fetchone()[0]
        if count == 0:
            cur.execute(f"INSERT INTO function(function_name, api_name) VALUES (%s, %s)", (f_name, c_name))
            conn.commit()
    # clean up
    
    cur.close()
    conn.close()


# create API_function_specific table
def createAPI_function_specific():
    # connect to database
    conn = psycopg2.connect(
        dbname=name, 
        user=usr, 
        password=pswd, 
        host='localhost',
        port = 5432
    )
    cur = conn.cursor()

    # execute query to create table with pk
    cur.execute("""
                CREATE TABLE public."api_function_specific"
                (
                    api_name_fk character varying,
                    function_name_fk character varying,
                    api_context character varying,
                    function_context character varying,
                    api_topic character varying,
                    function_topic character varying,
                    llm_expert_api character varying,
                    llm_expert_function character varying
                );
                """)

    # clean up
    conn.commit()
    cur.close()
    conn.close()


# format data for API_function_specific table
def formatAPI_function_specificData(output):
    c_names, f_names = [], []
    c_contexts, f_contexts = [], []
    c_topics, f_topics = [], []
    c_llms, f_llms = [], []

    # get classes
    for c, c_data in output['simpleDataReferenceTree'].items():
        # initialze values
        c_context, f_context = None, None
        c_topic, f_topic = None, None
        c_llm, f_llm = None, None

        if c_data['full'] == 0: continue
        for c_name in c_data['full']: # api_name_fk
            
            # get class descriptions
            for key, value in output['classDescriptions'].items():
                if c_name == key:
                    c_context = value # api_content
            
            # get class summaries
            for key, value in output['classSummaries'].items():
                if c_name == key:
                    c_topic = value # api_topic
            
            # get class domains
            for key, value in output['classDomains'].items():
                if c_name == key:
                    c_llm = value # llm_expert_api

            # get variable list
            for var in c_data['varlist']:
                methods = var['methods']

                # get methods, if any
                if len(methods) != 0:
                    for method in methods:
                        f_name = str(method['method']) # function_name_fk
                        f_name_full = c_name + "::" + f_name

                        # get class descriptions
                        for key, value in output['functionDescriptions'].items():
                            if f_name_full == key:
                                f_context = value # function_content
                        
                        # get class summaries
                        for key, value in output['functionSummaries'].items():
                            if f_name_full == key:
                                f_topic = value # function_topic
                        
                        # get class domains
                        for key, value in output['functionDomains'].items():
                            if f_name_full == key:
                                f_llm = value # llm_expert_funciton

                        # add to respective lists
                        f_names.append(f_name)
                        c_names.append(c_name)
                        f_contexts.append(f_context)
                        c_contexts.append(c_context)
                        f_topics.append(f_topic)
                        c_topics.append(c_topic)
                        f_llms.append(f_llm)
                        c_llms.append(c_llm)

    # group data and return 
    result = {
        "api_name_fk": c_names,          
        "function_name_fk": f_names,
        "api_context": c_contexts,       # full documentation
        "function_context": f_contexts,
        "api_topic": c_topics,           # summarized documentation
        "function_topic": f_topics,
        "llm_expert_api": c_llms,        # domain from G4F
        "llm_expert_function": f_llms
    }
    return result


# insert data into API_function_specific table
def insertAPI_function_specific(data):
    conn = psycopg2.connect(
        dbname=name, 
        user=usr, 
        password=pswd, 
        host='localhost',
        port = 5432
    )
    cur = conn.cursor()

    for i in range(len(data['api_name_fk'])):
        c_name, f_name = data['api_name_fk'][i], data['function_name_fk'][i]
        cur.execute(f"SELECT COUNT(*) FROM API_function_specific WHERE api_name_fk = %s AND function_name_fk = %s", (c_name, f_name))
        count = cur.fetchone()[0]
        if count == 0:
            cur.execute("INSERT INTO API_function_specific (api_name_fk, function_name_fk, api_context, function_context, api_topic, function_topic, llm_expert_API, llm_expert_function) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (data['api_name_fk'][i], data['function_name_fk'][i], data['api_context'][i], data['function_context'][i], data['api_topic'][i], data['function_topic'][i], data['llm_expert_api'][i], data['llm_expert_function'][i]))
            conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    # get data from savedReport.json
    
    with open("generatedFiles/savedReport.json", 'r') as f:
        json_data = json.load(f)
    f.close()

    createFunction()
    createAPI_function_specific()

    # iterate through data for each file
    for file in tqdm.tqdm(json_data):
        file_data = file['data']
        
        functionData = formatFunctionData(file_data)
        # print(functionData)
        insertFunction(functionData)

        API_function_specificData = formatAPI_function_specificData(file_data)
        # print(API_function_specificData)
        insertAPI_function_specific(API_function_specificData)

