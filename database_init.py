import datetime
import json
import os
import pickle
import sqlite3
from typing import Callable
import tqdm # pip install tqdm
from DatabaseManager import DatabaseManager 


def start(new_setup_func : Callable):
    """Set up Databases with tables. Define database structure
    """
    conn = sqlite3.connect("./generatedFiles/function_storage.db")
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS storage (key TEXT, label TEXT)
    ''')
    conn.commit()
    cur.close()
    conn.close()

    conn = sqlite3.connect("./generatedFiles/api_storage.db")
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS storage (key TEXT, label TEXT)
    ''')
    conn.commit()
    cur.close()
    conn.close()

    conn = sqlite3.connect("./generatedFiles/main.db")
    cur = conn.cursor()
    cur.execute("""
                      CREATE TABLE IF NOT EXISTS "files_changed" (
                        "rowID"	INTEGER PRIMARY KEY AUTOINCREMENT,
                        "filename"	TEXT,
                        "processed" TEXT,
                        "commit_hash" TEXT
                    )
                      """)
    cur.execute("""
                    CREATE TABLE IF NOT EXISTS "api_file_register" (
                        "rowID"	INTEGER PRIMARY KEY AUTOINCREMENT
                    )
                """)
    cur.execute("""
                      CREATE TABLE IF NOT EXISTS "pull_request_commits" (
                        "rowID"	INTEGER PRIMARY KEY AUTOINCREMENT,
                        "commit_hash" TEXT
                    )
                      """)
    cur.execute("""
                      CREATE TABLE IF NOT EXISTS "pull_request_comments" (
                            "rowID"	INTEGER PRIMARY KEY AUTOINCREMENT,
                            "comment"	TEXT NOT NULL,
                            "user"	TEXT
                        )
                      """)
    cur.execute("""
                      CREATE TABLE IF NOT EXISTS "settings" (
                        "rowID"	INTEGER PRIMARY KEY AUTOINCREMENT,
                        "key"	TEXT UNIQUE NOT NULL,
                        "value"	TEXT NOT NULL
                    )
                      """)
    cur.execute("""
                      CREATE TABLE IF NOT EXISTS "pull_requests" (
                        "rowID"	INTEGER PRIMARY KEY AUTOINCREMENT,
                        "pullNumber"	INTEGER NOT NULL,
                        "title"	TEXT NOT NULL,
                        "descriptionText"	TEXT,
                        "created"	TEXT NOT NULL,
                        "closed"	TEXT,
                        "userlogin"	TEXT,
                        "author"	TEXT,
                        "most_recent_commit" TEXT
                    )
                      """)
    cur.execute("""
                    CREATE TABLE IF NOT EXISTS "api_cache" (
                    "classname"	TEXT,
                    "domain"	TEXT,
                    "descriptionText" TEXT,
                    "response" TEXT,
                    PRIMARY KEY("classname")
                    )               
                """) 
    cur.execute("""
                    CREATE TABLE IF NOT EXISTS "function_cache" (
                    "function_name"	TEXT,
                    "subdomain"	TEXT,
                    "descriptionText" TEXT,
                    "response" TEXT
                )
                """)
    cur.execute("""
                CREATE TABLE IF NOT EXISTS "files_downloaded" (
                    "rowID"	INTEGER PRIMARY KEY AUTOINCREMENT,
                    "filepath"	TEXT,
                    "hash"	TEXT,
                    "ending" TEXT
                )
                """ 
                )
    
    # Data structure for export... this defines the output table. It is an SQL view to use 
    # all the power SQL has. query_generator generates the 1/0 columns.
    cur.execute(f"""
                CREATE VIEW IF NOT EXISTS outputTable AS
                    SELECT 
                        a.pullNumber as "PR #",
                        'True' as "Pull Request",
                        a.title as "issue text",
                        a.descriptionText as "issue description",
                        a.created as "created_at",
                        a.closed as "closed_at",
                        a.userlogin as "userlogin",
                        a.author as "author_name",
                        a.most_recent_commit as "most_recent_commit",
                        b.filename as "filename",
                        b.commit_hash as "file_commit",
                        
                        --- core engine fields
                
                        c.classname as "api",
                        c.function_name as "function_name",
                        d.domain as "api_domain",
                        f.subdomain as "subdomain",
                        
                        {query_generator()}
                        
                    FROM 
                        pull_requests as a,
                        files_changed as b,
                        api_file_register as c,
                        api_cache as d,
                        function_cache as f
                    WHERE
                        a.pullNumber = b.pullNumber AND
                        b.filename = c.filename AND
                        b.commit_hash = c.commit_hash AND
                        c.function_name = f.function_name AND
                        c.classname = f.classname AND
                        c.classname = d.classname  
                ;
                """)

    conn.commit()
    cur.execute("SELECT value FROM settings WHERE key = 'create'")
    row = cur.fetchone()
    if(row is None):
        print("New main.db generated")
        cur.execute("ALTER TABLE pull_request_comments ADD COLUMN pullNumber INTEGER REFERENCES pull_requests(pullNumber)")
        cur.execute("ALTER TABLE pull_request_commits ADD COLUMN pullNumber INTEGER REFERENCES pull_requests(pullNumber)")
        cur.execute("ALTER TABLE files_changed ADD COLUMN pullNumber INTEGER REFERENCES pull_requests(pullNumber)")
        cur.execute("ALTER TABLE function_cache ADD COLUMN classname TEXT REFERENCES api_cache(classname)")
        cur.execute("ALTER TABLE api_file_register ADD COLUMN filename TEXT REFERENCES files_changed(filename)")
        cur.execute("ALTER TABLE api_file_register ADD COLUMN commit_hash TEXT REFERENCES files_changed(commit_hash)")
        cur.execute("ALTER TABLE api_file_register ADD COLUMN classname TEXT REFERENCES api_cache(class_name)")
        cur.execute("ALTER TABLE api_file_register ADD COLUMN function_name TEXT REFERENCES function_cache(function_name)")
        cur.execute("INSERT INTO settings (key, value) VALUES ('create', ?)",(datetime.datetime.now(),))
        conn.commit()
        cur.close()
        conn.close()
        new_setup_func()
    else:
        print(f"Using main.db generated from {row[0]}")
        conn.commit()
    
        cur.execute("SELECT value FROM settings WHERE key = 'setup'")
        row = cur.fetchone()
        cur.close()
        conn.close()
        if(row is None):
            print("main.db is corrupted, regenerating")
            db = DatabaseManager()
            db.save_caches()
            db.close()
            os.unlink("./generatedFiles/main.db")
            return start(new_setup_func)


    conn = sqlite3.connect("./generatedFiles/file_data.db")
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS storage (filename TEXT, domains TEXT, subdomains TEXT, 
        "Application" INTEGER, "Application Performance Manager"  INTEGER, "Big Data"  INTEGER, 
        "Cloud" INTEGER, "Computer Graphics" INTEGER, "Data Structure" INTEGER, "Databases" INTEGER, 
        "Software Development and IT Operations" INTEGER, "Error Handling" INTEGER, "Event Handling" INTEGER, 
        "Geographic Information System" INTEGER, "Input-Output" INTEGER, "Interpreter" INTEGER, 
        "Internationalization" INTEGER, "Logic" INTEGER, "Language" INTEGER, "Logging" INTEGER, 
        "Machine Learning" INTEGER, "Microservices/Services" INTEGER, "Multimedia" INTEGER, 
        "Multi-Thread" INTEGER, "Natural Language Processing" INTEGER, "Network" INTEGER, 
        "Operating System" INTEGER, "Parser" INTEGER, "Search" INTEGER, "Security" INTEGER, "Setup" INTEGER, 
        "User Interface" INTEGER, "Utility" INTEGER, "Test" INTEGER, "Application-Integration" INTEGER, 
        "Application-Plugin Management" INTEGER, "Application-User Customization" INTEGER, 
        "Application-App Configuration" INTEGER, "Application-Version Control" INTEGER, 
        "Application-Compatibility Checks" INTEGER, "Application Performance Manager-Performance Monitoring" INTEGER, 
        "Application Performance Manager-Resource Allocation" INTEGER, 
        "Application Performance Manager-Error Detection" INTEGER, "Application Performance Manager-Load Balancing" INTEGER, 
        "Application Performance Manager-Traffic Management" INTEGER, "Application Performance Manager-Diagnostic Tools" INTEGER, 
        "Big Data-Data Processing" INTEGER, "Big Data-Data Storage" INTEGER, "Big Data-Data Analysis" INTEGER, 
        "Big Data-Real-Time Processing" INTEGER, "Big Data-Batch Processing" INTEGER, "Big Data-Data Visualization" INTEGER, 
        "Cloud-Resource Management" INTEGER, "Cloud-Virtualization" INTEGER, "Cloud-Scalability Solutions" INTEGER, 
        "Cloud-Cloud Security" INTEGER, "Cloud-Data Migration" INTEGER, "Cloud-Service Configuration" INTEGER, 
        "Computer Graphics-Image Rendering" INTEGER, "Computer Graphics-Animation" INTEGER, "Computer Graphics-Modeling" INTEGER, 
        "Computer Graphics-Texture Mapping" INTEGER, "Computer Graphics-Visual Effects" INTEGER, 
        "Computer Graphics-Graphics Optimization" INTEGER, "Data Structure-Linear Structures" INTEGER, 
        "Data Structure-Tree Structures" INTEGER, "Data Structure-Graph Structures" INTEGER, "Data Structure-Data Sorting" INTEGER, 
        "Data Structure-Search Algorithms" INTEGER, "Data Structure-Data Manipulation" INTEGER, "Databases-Query Execution" INTEGER, 
        "Databases-Transaction Management" INTEGER, "Databases-Schema Design" INTEGER, "Databases-Database Security" INTEGER, 
        "Databases-Backup and Recovery" INTEGER, "Databases-Database Optimization" INTEGER, 
        "Software Development and IT Operations-Continuous Integration" INTEGER, 
        "Software Development and IT Operations-Continuous Deployment" INTEGER, 
        "Software Development and IT Operations-Automated Testing" INTEGER, 
        "Software Development and IT Operations-Configuration Management" INTEGER, 
        "Software Development and IT Operations-Version Control" INTEGER, 
        "Software Development and IT Operations-Monitoring and Logging" INTEGER, "Error Handling-Exception Handling" INTEGER, 
        "Error Handling-Error Logging" INTEGER, "Error Handling-Fault Tolerance" INTEGER, "Error Handling-Debugging Tools" INTEGER, 
        "Error Handling-User Notification" INTEGER, "Error Handling-Error Prevention" INTEGER, "Event Handling-User Interactions" INTEGER, 
        "Event Handling-System Events" INTEGER, "Event Handling-Event Logging" INTEGER, "Event Handling-Event Driven Processing" INTEGER, 
        "Event Handling-Notifications" INTEGER, "Event Handling-Asynchronous Processing" INTEGER, "Geographic Information System-Mapping" INTEGER, 
        "Geographic Information System-Spatial Analysis" INTEGER, "Geographic Information System-Data Collection" INTEGER, 
        "Geographic Information System-Geographic Visualization" INTEGER, "Geographic Information System-Location Services" INTEGER, 
        "Geographic Information System-Environmental Modeling" INTEGER, "Input-Output-Data Reading" INTEGER, "Input-Output-Data Writing" INTEGER, 
        "Input-Output-Stream Management" INTEGER, "Input-Output-Buffering Strategies" INTEGER, "Input-Output-File Management" INTEGER, "Input-Output-Network IO" INTEGER, 
        "Interpreter-Script Execution" INTEGER, "Interpreter-Code Translation" INTEGER, "Interpreter-Memory Management" INTEGER, "Interpreter-Syntax Analysis" INTEGER, 
        "Interpreter-Optimization" INTEGER, "Interpreter-Debugging" INTEGER, "Internationalization-Localization" INTEGER, "Internationalization-Language Support" INTEGER, 
        "Internationalization-Cultural Adaptation" INTEGER, "Internationalization-Currency Conversion" INTEGER, "Internationalization-Date/Time Formatting" INTEGER, 
        "Internationalization-Right-to-Left Layouts" INTEGER, "Logic-Control Structures" INTEGER, "Logic-Algorithm Implementation" INTEGER, 
        "Logic-Logic Optimization" INTEGER, "Logic-Validation Checks" INTEGER, "Logic-Rule Processing" INTEGER, "Logic-Decision Making" INTEGER, 
        "Language-Syntax Features" INTEGER, "Language-Compiler/Interpreter Enhancements" INTEGER, "Language-Runtime Optimization" INTEGER, 
        "Language-Standard Libraries" INTEGER, "Language-Language Extensions" INTEGER, "Language-Type Systems" INTEGER, "Logging-Event Logging" INTEGER, 
        "Logging-System Monitoring" INTEGER, "Logging-Performance Tracking" INTEGER, "Logging-Error Logs" INTEGER, "Logging-User Activity Logs" INTEGER, 
        "Logging-Audit Trails" INTEGER, "Machine Learning-Training Models" INTEGER, "Machine Learning-Prediction" INTEGER, "Machine Learning-Data Preprocessing" INTEGER, 
        "Machine Learning-Feature Extraction" INTEGER, "Machine Learning-Model Evaluation" INTEGER, "Machine Learning-Deployment" INTEGER, "Microservices/Services-Service Discovery" INTEGER, 
        "Microservices/Services-Load Balancing" INTEGER, "Microservices/Services-API Gateway" INTEGER, "Microservices/Services-Service Communication" INTEGER, "Microservices/Services-Fault Tolerance" INTEGER, 
        "Microservices/Services-Service Deployment" INTEGER, "Multimedia-Media Playback" INTEGER, "Multimedia-Media Editing" INTEGER, "Multimedia-Encoding and Decoding" INTEGER, "Multimedia-Streaming" INTEGER, 
        "Multimedia-Content Delivery" INTEGER, "Multimedia-Media Storage" INTEGER, "Multi-Thread-Concurrency Control" INTEGER, "Multi-Thread-Synchronization" INTEGER, "Multi-Thread-Thread Safety" INTEGER, 
        "Multi-Thread-Parallel Processing" INTEGER, "Multi-Thread-Resource Sharing" INTEGER, "Multi-Thread-Deadlock Resolution" INTEGER, "Natural Language Processing-Text Analysis" INTEGER, 
        "Natural Language Processing-Speech Recognition" INTEGER, "Natural Language Processing-Language Generation" INTEGER, "Natural Language Processing-Sentiment Analysis" INTEGER, 
        "Natural Language Processing-Machine Translation" INTEGER, "Natural Language Processing-Chatbot Interfaces" INTEGER, "Network-Protocol Implementation" INTEGER, "Network-Connection Management" INTEGER, 
        "Network-Data Transmission" INTEGER, "Network-Network Security" INTEGER, "Network-Bandwidth Optimization" INTEGER, "Network-Network Monitoring" INTEGER, "Operating System-Process Management" INTEGER, 
        "Operating System-Memory Management" INTEGER, "Operating System-Device Drivers" INTEGER, "Operating System-File Systems" INTEGER, "Operating System-User Interface" INTEGER, "Operating System-System Security" INTEGER, 
        "Parser-Syntax Parsing" INTEGER, "Parser-Error Recovery" INTEGER, "Parser-Data Conversion" INTEGER, "Parser-Optimization" INTEGER, "Parser-Code Generation" INTEGER, "Parser-Validation" INTEGER, "Search-Indexing" INTEGER, 
        "Search-Query Processing" INTEGER, "Search-Ranking" INTEGER, "Search-Optimization" INTEGER, "Search-Caching" INTEGER, "Search-Personalization" INTEGER, "Security-Authentication" INTEGER, "Security-Authorization" INTEGER, 
        "Security-Encryption" INTEGER, "Security-Intrusion Detection" INTEGER, "Security-Compliance" INTEGER, "Security-Data Integrity" INTEGER, "Setup-Installation" INTEGER, "Setup-Configuration" INTEGER, 
        "Setup-System Requirements" INTEGER, "Setup-Update Management" INTEGER, "Setup-Licensing" INTEGER, "Setup-Environment Setup" INTEGER, "User Interface-Layout Design" INTEGER, "User Interface-Interaction Design" INTEGER, 
        "User Interface-Accessibility" INTEGER, "User Interface-Animation" INTEGER, "User Interface-Responsive Design" INTEGER, "User Interface-User Feedback" INTEGER, "Utility-Data Conversion" INTEGER, "Utility-System Tools" INTEGER, 
        "Utility-Automation Scripts" INTEGER, "Utility-Performance Tools" INTEGER, "Utility-Diagnostic Utilities" INTEGER, "Utility-Backup Tools" INTEGER, "Test-Unit Testing" INTEGER, "Test-Integration Testing" INTEGER, 
        "Test-Performance Testing" INTEGER, "Test-Security Testing" INTEGER, "Test-Usability Testing" INTEGER, "Test-Regression Testing" INTEGER)
    ''')
    conn.commit()
    cur.close()
    conn.close()

def setup_caches():
    """Import caches from backup.
    """
    db = DatabaseManager()
    db.load_caches()
    db.close()

def populate_db_with_mining_data():
    """Go through the mining data "datamining.pkl" and add it to the database. Data import.
    """
    conn = sqlite3.connect("./generatedFiles/main.db")
    cur = conn.cursor()

    file = open("./generatedFiles/datamining.pkl",'rb')
    data = pickle.load(file)
    file.close()

    filesAdded = set()

    for row in tqdm.tqdm(data):
        # Get elements from the rows
        issueNumber = row[1]
        pullR_check = row[2]
        if(pullR_check is not True):
            continue
        issueText = row[3]
        issueDescription = row[4]
        created = row[7]
        closed = row[8]
        userlog = row[9]
        author = row[10]
        comments = row[11]
        filesChanged = row[12]
        commit_hashes = row[13]
        commit_hash = row[14]
        
        # Insert into tables.
        vals = (issueNumber, issueText, issueDescription, created, closed, userlog, author,commit_hash)
        cur.execute("INSERT INTO pull_requests (pullNumber, title, descriptionText, created, closed, userlogin, author, most_recent_commit) VALUES (?,?,?,?,?,?,?,?)", vals)
        for comment in comments:
            if(comment == ''):
                continue
            cur.execute("INSERT INTO pull_request_comments (pullNumber, comment) VALUES (?,?)",(issueNumber, comment))
        for fileChange in set(filesChanged):
            if(fileChange == ''):
                continue
            search = f"{commit_hash}:{fileChange}"
            if(search not in filesAdded): # no duplicates!
                cur.execute("INSERT INTO files_changed (pullNumber, filename, commit_hash) VALUES (?, ?, ?)", (issueNumber, fileChange, commit_hash))
                filesAdded.add(search)
            else:
                cur.execute("UPDATE files_changed SET pullNumber=? WHERE filename = ? AND commit_hash = ?", (issueNumber, fileChange, commit_hash))
        if(commit_hash != ''):
            for commit in commit_hashes:
                cur.execute("INSERT INTO pull_request_commits (pullNumber, commit_hash) VALUES (?,?)",(issueNumber,commit))
        

    cur.execute("INSERT INTO settings (key, value) VALUES ('setup', ?)",(datetime.datetime.now(),))
    conn.commit()
    cur.close()
    conn.close()
    

def query_generator():
    """Generate the 1/0 columns for each label.

    Returns:
        str: SQL query to be injected into the CREATE VIEW statement.
    """

    subdomain_label_file = "subdomain_labels.json"

    with open(subdomain_label_file) as f:
        labels = json.load(f)
    out = ""
    for label in labels:
        sub_labels = labels[label]
        
        out += f"(CASE WHEN d.domain = '{label}' THEN 1 ELSE 0 END) as '{label}'"
        for sub_label in sub_labels:
            out += ",\n"
            out += f"(CASE WHEN d.domain = '{label}' AND f.subdomain = '{list(sub_label.keys())[0]}' THEN 1 ELSE 0 END) as '{label}-{list(sub_label.keys())[0]}'"
        out += ",\n" 
    return out[:-2]


