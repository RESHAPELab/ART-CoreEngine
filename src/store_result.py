import sqlite3
import json
from collections import Counter
import pandas as pd

#----------- SQL TO CSV --------------------------

def create_and_populate_db(db_path : str):
    """Create an example database file

    Args:
        db_path (str): database file
    """
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table
    cursor.execute('''CREATE TABLE IF NOT EXISTS example_table (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        age INTEGER
                    )''')

    # Insert data
    cursor.execute("INSERT INTO example_table (name, age) VALUES ('Alice', 30)")
    cursor.execute("INSERT INTO example_table (name, age) VALUES ('Bob', 25)")
    cursor.execute("INSERT INTO example_table (name, age) VALUES ('Charlie', 35)")

    # Commit changes and close connection
    conn.commit()
    conn.close()

def sqlite_to_csv(db_path : str, table_name : str, output_csv_path : str):
    """Export table at database path to csv file

    Args:
        db_path (str): _description_
        table_name (str): _description_
        output_csv_path (str): _description_
    """
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)

    # Load the table into a pandas DataFrame
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)

    # Export the DataFrame to a CSV file
    df.to_csv(output_csv_path, index=False)  # index=False to avoid writing row numbers

    # Close the connection
    conn.close()

    print(f"Table {table_name} has been exported to {output_csv_path}")

#--------------CSV/DB CODE------------------------

# CONVERT TO IN DATABASE
def in_csv(csv_file, key_name):
    conn = sqlite3.connect(csv_file)
    cur = conn.cursor()

    # Prepare and execute the query
    query = '''
    SELECT EXISTS (
        SELECT 1
        FROM storage
        WHERE key = ?
    ) AS found;
    '''
    cur.execute(query, (key_name,))

    # Fetch the result
    result = cur.fetchone()[0]

    # Print whether the key phrase was found or not
    if result == 1:
        cur.close()
        conn.close()
        # print(f"The key phrase '{key_name}' was found in the first column.")
        return True
    else:
        cur.close()
        conn.close()
        # print(f"The key phrase '{key_name}' was not found in the first column.")
        return False
    # if os.path.exists(csv_file):
    #     with open(csv_file, 'r', newline='') as file:
    #         reader = csv.reader(file)
    #         for row in reader:
    #             if row and row[0] == key_name:
    #                 return True


def in_file(csv_file, key_name):
    conn = sqlite3.connect(csv_file)
    cur = conn.cursor()

    # Prepare and execute the query
    query = '''
    SELECT EXISTS (
        SELECT 1
        FROM storage
        WHERE filename = ?
    ) AS found;
    '''
    cur.execute(query, (key_name,))

    # Fetch the result
    result = cur.fetchone()[0]

    # Print whether the key phrase was found or not
    if result == 1:
        cur.close()
        conn.close()
        # print(f"The key phrase '{key_name}' was found in the first column.")
        return True
    else:
        cur.close()
        conn.close()
        # print(f"The key phrase '{key_name}' was not found in the first column.")
        return False
    # if os.path.exists(csv_file):
    #     with open(csv_file, 'r', newline='') as file:
    #         reader = csv.reader(file)
    #         for row in reader:
    #             if row and row[0] == key_name:
    #                 return True


# GET FROM DATABASE
def get_from_csv(csv_file, key_name):
    conn = sqlite3.connect(csv_file)
    cur = conn.cursor()

    query = '''
    SELECT label
    FROM storage
    WHERE key = ?;
    '''
    cur.execute(query, (key_name,))

    # Fetch the result
    result = cur.fetchone()

    # Check if a result was found and print the last_name
    if result:
        cur.close()
        conn.close()
        return result[0]
        # print(f"The last name for '{key_name}' is '{last_name}'.")
    else:
        cur.close()
        conn.close()
        return None
        # print(f"No match found for the first name '{key_name}'.")
    # if os.path.exists(csv_file):
    #     with open(csv_file, 'r', newline='') as file:
    #         reader = csv.reader(file)
    #         for row in reader:
    #             if row and row[0] == key_name:
    #                 return row[1]
    # return None


# CONVERT TO ADD Functions and API TO DATABASE
def add_to_csv(csv_file, key_name, label):
    conn = sqlite3.connect(csv_file)
    cur = conn.cursor()
    found = in_csv(csv_file, key_name)

    if not found:
        cur.execute('''
            INSERT INTO storage (key, label) VALUES (?, ?)
        ''', (key_name, label))
        conn.commit()
    cur.close()
    conn.close()
        # with open(csv_file, 'a', newline='') as file:
        #     writer = csv.writer(file)
        #     file.seek(0, os.SEEK_END)  # Move pointer to the end of file
        #     if file.tell() == 0:  # Check if file is empty
        #         writer.writerow(['key', 'label'])  # Write header row if file is empty
        #     writer.writerow([key_name, label])


# STORE FILE DATA IN DATABASE
def store_file(csv_file, file_name, domains, subdomains):
    conn = sqlite3.connect(csv_file)
    cur = conn.cursor()
    found = in_file(csv_file, file_name)

    if not found:
        possible_domains = ['Application', 'Application Performance Manager', 'Big Data', 'Cloud', 'Computer Graphics', 'Data Structure', 'Databases', 'Software Development and IT Operations', 'Error Handling', 'Event Handling', 'Geographic Information System', 'Input-Output', 'Interpreter', 'Internationalization', 'Logic', 'Language', 'Logging', 'Machine Learning', 'Microservices/Services', 'Multimedia', 'Multi-Thread', 'Natural Language Processing', 'Network', 'Operating System', 'Parser', 'Search', 'Security', 'Setup', 'User Interface', 'Utility', 'Test']
        possible_subdomains = [
            'Application-Integration',
            'Application-Plugin Management',
            'Application-User Customization',
            'Application-App Configuration',
            'Application-Version Control',
            'Application-Compatibility Checks',
            'Application Performance Manager-Performance Monitoring',
            'Application Performance Manager-Resource Allocation',
            'Application Performance Manager-Error Detection',
            'Application Performance Manager-Load Balancing',
            'Application Performance Manager-Traffic Management',
            'Application Performance Manager-Diagnostic Tools',
            'Big Data-Data Processing',
            'Big Data-Data Storage',
            'Big Data-Data Analysis',
            'Big Data-Real-Time Processing',
            'Big Data-Batch Processing',
            'Big Data-Data Visualization',
            'Cloud-Resource Management',
            'Cloud-Virtualization',
            'Cloud-Scalability Solutions',
            'Cloud-Cloud Security',
            'Cloud-Data Migration',
            'Cloud-Service Configuration',
            'Computer Graphics-Image Rendering',
            'Computer Graphics-Animation',
            'Computer Graphics-Modeling',
            'Computer Graphics-Texture Mapping',
            'Computer Graphics-Visual Effects',
            'Computer Graphics-Graphics Optimization',
            'Data Structure-Linear Structures',
            'Data Structure-Tree Structures',
            'Data Structure-Graph Structures',
            'Data Structure-Data Sorting',
            'Data Structure-Search Algorithms',
            'Data Structure-Data Manipulation',
            'Databases-Query Execution',
            'Databases-Transaction Management',
            'Databases-Schema Design',
            'Databases-Database Security',
            'Databases-Backup and Recovery',
            'Databases-Database Optimization',
            'Software Development and IT Operations-Continuous Integration',
            'Software Development and IT Operations-Continuous Deployment',
            'Software Development and IT Operations-Automated Testing',
            'Software Development and IT Operations-Configuration Management',
            'Software Development and IT Operations-Version Control',
            'Software Development and IT Operations-Monitoring and Logging',
            'Error Handling-Exception Handling',
            'Error Handling-Error Logging',
            'Error Handling-Fault Tolerance',
            'Error Handling-Debugging Tools',
            'Error Handling-User Notification',
            'Error Handling-Error Prevention',
            'Event Handling-User Interactions',
            'Event Handling-System Events',
            'Event Handling-Event Logging',
            'Event Handling-Event Driven Processing',
            'Event Handling-Notifications',
            'Event Handling-Asynchronous Processing',
            'Geographic Information System-Mapping',
            'Geographic Information System-Spatial Analysis',
            'Geographic Information System-Data Collection',
            'Geographic Information System-Geographic Visualization',
            'Geographic Information System-Location Services',
            'Geographic Information System-Environmental Modeling',
            'Input-Output-Data Reading',
            'Input-Output-Data Writing',
            'Input-Output-Stream Management',
            'Input-Output-Buffering Strategies',
            'Input-Output-File Management',
            'Input-Output-Network IO',
            'Interpreter-Script Execution',
            'Interpreter-Code Translation',
            'Interpreter-Memory Management',
            'Interpreter-Syntax Analysis',
            'Interpreter-Optimization',
            'Interpreter-Debugging',
            'Internationalization-Localization',
            'Internationalization-Language Support',
            'Internationalization-Cultural Adaptation',
            'Internationalization-Currency Conversion',
            'Internationalization-Date/Time Formatting',
            'Internationalization-Right-to-Left Layouts',
            'Logic-Control Structures',
            'Logic-Algorithm Implementation',
            'Logic-Logic Optimization',
            'Logic-Validation Checks',
            'Logic-Rule Processing',
            'Logic-Decision Making',
            'Language-Syntax Features',
            'Language-Compiler/Interpreter Enhancements',
            'Language-Runtime Optimization',
            'Language-Standard Libraries',
            'Language-Language Extensions',
            'Language-Type Systems',
            'Logging-Event Logging',
            'Logging-System Monitoring',
            'Logging-Performance Tracking',
            'Logging-Error Logs',
            'Logging-User Activity Logs',
            'Logging-Audit Trails',
            'Machine Learning-Training Models',
            'Machine Learning-Prediction',
            'Machine Learning-Data Preprocessing',
            'Machine Learning-Feature Extraction',
            'Machine Learning-Model Evaluation',
            'Machine Learning-Deployment',
            'Microservices/Services-Service Discovery',
            'Microservices/Services-Load Balancing',
            'Microservices/Services-API Gateway',
            'Microservices/Services-Service Communication',
            'Microservices/Services-Fault Tolerance',
            'Microservices/Services-Service Deployment',
            'Multimedia-Media Playback',
            'Multimedia-Media Editing',
            'Multimedia-Encoding and Decoding',
            'Multimedia-Streaming',
            'Multimedia-Content Delivery',
            'Multimedia-Media Storage',
            'Multi-Thread-Concurrency Control',
            'Multi-Thread-Synchronization',
            'Multi-Thread-Thread Safety',
            'Multi-Thread-Parallel Processing',
            'Multi-Thread-Resource Sharing',
            'Multi-Thread-Deadlock Resolution',
            'Natural Language Processing-Text Analysis',
            'Natural Language Processing-Speech Recognition',
            'Natural Language Processing-Language Generation',
            'Natural Language Processing-Sentiment Analysis',
            'Natural Language Processing-Machine Translation',
            'Natural Language Processing-Chatbot Interfaces',
            'Network-Protocol Implementation',
            'Network-Connection Management',
            'Network-Data Transmission',
            'Network-Network Security',
            'Network-Bandwidth Optimization',
            'Network-Network Monitoring',
            'Operating System)-Process Management',
            'Operating System)-Memory Management',
            'Operating System)-Device Drivers',
            'Operating System)-File Systems',
            'Operating System)-User Interface',
            'Operating System)-System Security',
            'Parser-Syntax Parsing',
            'Parser-Error Recovery',
            'Parser-Data Conversion',
            'Parser-Optimization',
            'Parser-Code Generation',
            'Parser-Validation',
            'Search-Indexing',
            'Search-Query Processing',
            'Search-Ranking',
            'Search-Optimization',
            'Search-Caching',
            'Search-Personalization',
            'Security-Authentication',
            'Security-Authorization',
            'Security-Encryption',
            'Security-Intrusion Detection',
            'Security-Compliance',
            'Security-Data Integrity',
            'Setup-Installation',
            'Setup-Configuration',
            'Setup-System Requirements',
            'Setup-Update Management',
            'Setup-Licensing',
            'Setup-Environment Setup',
            'User Interface-Layout Design',
            'User Interface-Interaction Design',
            'User Interface-Accessibility',
            'User Interface-Animation',
            'User Interface-Responsive Design',
            'User Interface-User Feedback',
            'Utility-Data Conversion',
            'Utility-System Tools',
            'Utility-Automation Scripts',
            'Utility-Performance Tools',
            'Utility-Diagnostic Utilities',
            'Utility-Backup Tools',
            'Test-Unit Testing',
            'Test-Integration Testing',
            'Test-Performance Testing',
            'Test-Security Testing',
            'Test-Usability Testing',
            'Test-Regression Testing'
        ]
        # Initialize Counters with all possible values
        domain_counts = Counter({key: 0 for key in possible_domains})
        subdomain_counts = Counter({key:0 for key in possible_subdomains})
        # Update the Counter with counts from your list
        domain_counts.update(domains)
        subdomain_counts.update(subdomains)
        domains = json.dumps(domains)
        subdomains = json.dumps(subdomains)
        cur.execute('''
                   INSERT INTO storage (filename, domains, subdomains, "Application", "Application Performance Manager" , "Big Data" ,
        "Cloud", "Computer Graphics", "Data Structure", "Databases",
        "Software Development and IT Operations", "Error Handling", "Event Handling",
        "Geographic Information System", "Input-Output", "Interpreter",
        "Internationalization", "Logic", "Language", "Logging",
        "Machine Learning", "Microservices/Services", "Multimedia",
        "Multi-Thread", "Natural Language Processing", "Network",
        "Operating System", "Parser", "Search", "Security", "Setup",
        "User Interface", "Utility", "Test", "Application-Integration",
        "Application-Plugin Management", "Application-User Customization",
        "Application-App Configuration", "Application-Version Control",
        "Application-Compatibility Checks", "Application Performance Manager-Performance Monitoring",
        "Application Performance Manager-Resource Allocation",
        "Application Performance Manager-Error Detection", "Application Performance Manager-Load Balancing",
        "Application Performance Manager-Traffic Management", "Application Performance Manager-Diagnostic Tools",
        "Big Data-Data Processing", "Big Data-Data Storage", "Big Data-Data Analysis",
        "Big Data-Real-Time Processing", "Big Data-Batch Processing", "Big Data-Data Visualization",
        "Cloud-Resource Management", "Cloud-Virtualization", "Cloud-Scalability Solutions",
        "Cloud-Cloud Security", "Cloud-Data Migration", "Cloud-Service Configuration",
        "Computer Graphics-Image Rendering", "Computer Graphics-Animation", "Computer Graphics-Modeling",
        "Computer Graphics-Texture Mapping", "Computer Graphics-Visual Effects",
        "Computer Graphics-Graphics Optimization", "Data Structure-Linear Structures",
        "Data Structure-Tree Structures", "Data Structure-Graph Structures", "Data Structure-Data Sorting",
        "Data Structure-Search Algorithms", "Data Structure-Data Manipulation", "Databases-Query Execution",
        "Databases-Transaction Management", "Databases-Schema Design", "Databases-Database Security",
        "Databases-Backup and Recovery", "Databases-Database Optimization",
        "Software Development and IT Operations-Continuous Integration",
        "Software Development and IT Operations-Continuous Deployment",
        "Software Development and IT Operations-Automated Testing",
        "Software Development and IT Operations-Configuration Management",
        "Software Development and IT Operations-Version Control",
        "Software Development and IT Operations-Monitoring and Logging", "Error Handling-Exception Handling",
        "Error Handling-Error Logging", "Error Handling-Fault Tolerance", "Error Handling-Debugging Tools",
        "Error Handling-User Notification", "Error Handling-Error Prevention", "Event Handling-User Interactions",
        "Event Handling-System Events", "Event Handling-Event Logging", "Event Handling-Event Driven Processing",
        "Event Handling-Notifications", "Event Handling-Asynchronous Processing", "Geographic Information System-Mapping",
        "Geographic Information System-Spatial Analysis", "Geographic Information System-Data Collection",
        "Geographic Information System-Geographic Visualization", "Geographic Information System-Location Services",
        "Geographic Information System-Environmental Modeling", "Input-Output-Data Reading", "Input-Output-Data Writing",
        "Input-Output-Stream Management", "Input-Output-Buffering Strategies", "Input-Output-File Management", "Input-Output-Network IO",
        "Interpreter-Script Execution", "Interpreter-Code Translation", "Interpreter-Memory Management", "Interpreter-Syntax Analysis",
        "Interpreter-Optimization", "Interpreter-Debugging", "Internationalization-Localization", "Internationalization-Language Support",
        "Internationalization-Cultural Adaptation", "Internationalization-Currency Conversion", "Internationalization-Date/Time Formatting",
        "Internationalization-Right-to-Left Layouts", "Logic-Control Structures", "Logic-Algorithm Implementation",
        "Logic-Logic Optimization", "Logic-Validation Checks", "Logic-Rule Processing", "Logic-Decision Making",
        "Language-Syntax Features", "Language-Compiler/Interpreter Enhancements", "Language-Runtime Optimization",
        "Language-Standard Libraries", "Language-Language Extensions", "Language-Type Systems", "Logging-Event Logging",
        "Logging-System Monitoring", "Logging-Performance Tracking", "Logging-Error Logs", "Logging-User Activity Logs",
        "Logging-Audit Trails", "Machine Learning-Training Models", "Machine Learning-Prediction", "Machine Learning-Data Preprocessing",
        "Machine Learning-Feature Extraction", "Machine Learning-Model Evaluation", "Machine Learning-Deployment", "Microservices/Services-Service Discovery",
        "Microservices/Services-Load Balancing", "Microservices/Services-API Gateway", "Microservices/Services-Service Communication", "Microservices/Services-Fault Tolerance",
        "Microservices/Services-Service Deployment", "Multimedia-Media Playback", "Multimedia-Media Editing", "Multimedia-Encoding and Decoding", "Multimedia-Streaming",
        "Multimedia-Content Delivery", "Multimedia-Media Storage", "Multi-Thread-Concurrency Control", "Multi-Thread-Synchronization", "Multi-Thread-Thread Safety",
        "Multi-Thread-Parallel Processing", "Multi-Thread-Resource Sharing", "Multi-Thread-Deadlock Resolution", "Natural Language Processing-Text Analysis",
        "Natural Language Processing-Speech Recognition", "Natural Language Processing-Language Generation", "Natural Language Processing-Sentiment Analysis",
        "Natural Language Processing-Machine Translation", "Natural Language Processing-Chatbot Interfaces", "Network-Protocol Implementation", "Network-Connection Management",
        "Network-Data Transmission", "Network-Network Security", "Network-Bandwidth Optimization", "Network-Network Monitoring", "Operating System-Process Management",
        "Operating System-Memory Management", "Operating System-Device Drivers", "Operating System-File Systems", "Operating System-User Interface", "Operating System-System Security",
        "Parser-Syntax Parsing", "Parser-Error Recovery", "Parser-Data Conversion", "Parser-Optimization", "Parser-Code Generation", "Parser-Validation", "Search-Indexing",
        "Search-Query Processing", "Search-Ranking", "Search-Optimization", "Search-Caching", "Search-Personalization", "Security-Authentication", "Security-Authorization",
        "Security-Encryption", "Security-Intrusion Detection", "Security-Compliance", "Security-Data Integrity", "Setup-Installation", "Setup-Configuration",
        "Setup-System Requirements", "Setup-Update Management", "Setup-Licensing", "Setup-Environment Setup", "User Interface-Layout Design", "User Interface-Interaction Design",
        "User Interface-Accessibility", "User Interface-Animation", "User Interface-Responsive Design", "User Interface-User Feedback", "Utility-Data Conversion", "Utility-System Tools",
        "Utility-Automation Scripts", "Utility-Performance Tools", "Utility-Diagnostic Utilities", "Utility-Backup Tools", "Test-Unit Testing", "Test-Integration Testing",
        "Test-Performance Testing", "Test-Security Testing", "Test-Usability Testing", "Test-Regression Testing") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ''', (file_name, domains, subdomains, domain_counts['Application'], domain_counts['Application Performance Manager'], domain_counts['Big Data'], domain_counts['Cloud'], domain_counts['Computer Graphics'], domain_counts['Data Structure'], domain_counts['Databases'], domain_counts['Software Development and IT Operations'], domain_counts['Error Handling'], domain_counts['Event Handling'], domain_counts['Geographic Information System'], domain_counts['Input-Output'], domain_counts['Interpreter'], domain_counts['Internationalization'], domain_counts['Logic'], domain_counts['Language'], domain_counts['Logging'], domain_counts['Machine Learning'], domain_counts['Microservices/Services'], domain_counts['Multimedia'], domain_counts['Multi-Thread'], domain_counts['Natural Language Processing'], domain_counts['Network'], domain_counts['Operating System'], domain_counts['Parser'], domain_counts['Search'], domain_counts['Security'], domain_counts['Setup'], domain_counts['User Interface'], domain_counts['Utility'], domain_counts['Test'], subdomain_counts['Application-Integration'], subdomain_counts['Application-Plugin Management'], subdomain_counts['Application-User Customization'], subdomain_counts['Application-App Configuration'], subdomain_counts['Application-Version Control'], subdomain_counts['Application-Compatibility Checks'], subdomain_counts['Application Performance Manager-Performance Monitoring'], subdomain_counts['Application Performance Manager-Resource Allocation'], subdomain_counts['Application Performance Manager-Error Detection'], subdomain_counts['Application Performance Manager-Load Balancing'], subdomain_counts['Application Performance Manager-Traffic Management'], subdomain_counts['Application Performance Manager-Diagnostic Tools'], subdomain_counts['Big Data-Data Processing'], subdomain_counts['Big Data-Data Storage'], subdomain_counts['Big Data-Data Analysis'], subdomain_counts['Big Data-Real-Time Processing'], subdomain_counts['Big Data-Batch Processing'], subdomain_counts['Big Data-Data Visualization'], subdomain_counts['Cloud-Resource Management'], subdomain_counts['Cloud-Virtualization'], subdomain_counts['Cloud-Scalability Solutions'], subdomain_counts['Cloud-Cloud Security'], subdomain_counts['Cloud-Data Migration'], subdomain_counts['Cloud-Service Configuration'], subdomain_counts['Computer Graphics-Image Rendering'], subdomain_counts['Computer Graphics-Animation'], subdomain_counts['Computer Graphics-Modeling'], subdomain_counts['Computer Graphics-Texture Mapping'], subdomain_counts['Computer Graphics-Visual Effects'], subdomain_counts['Computer Graphics-Graphics Optimization'], subdomain_counts['Data Structure-Linear Structures'], subdomain_counts['Data Structure-Tree Structures'], subdomain_counts['Data Structure-Graph Structures'], subdomain_counts['Data Structure-Data Sorting'], subdomain_counts['Data Structure-Search Algorithms'], subdomain_counts['Data Structure-Data Manipulation'], subdomain_counts['Databases-Query Execution'], subdomain_counts['Databases-Transaction Management'], subdomain_counts['Databases-Schema Design'], subdomain_counts['Databases-Database Security'], subdomain_counts['Databases-Backup and Recovery'], subdomain_counts['Databases-Database Optimization'], subdomain_counts['Software Development and IT Operations-Continuous Integration'], subdomain_counts['Software Development and IT Operations-Continuous Deployment'], subdomain_counts['Software Development and IT Operations-Automated Testing'], subdomain_counts['Software Development and IT Operations-Configuration Management'], subdomain_counts['Software Development and IT Operations-Version Control'], subdomain_counts['Software Development and IT Operations-Monitoring and Logging'], subdomain_counts['Error Handling-Exception Handling'], subdomain_counts['Error Handling-Error Logging'], subdomain_counts['Error Handling-Fault Tolerance'], subdomain_counts['Error Handling-Debugging Tools'], subdomain_counts['Error Handling-User Notification'], subdomain_counts['Error Handling-Error Prevention'], subdomain_counts['Event Handling-User Interactions'], subdomain_counts['Event Handling-System Events'], subdomain_counts['Event Handling-Event Logging'], subdomain_counts['Event Handling-Event Driven Processing'], subdomain_counts['Event Handling-Notifications'], subdomain_counts['Event Handling-Asynchronous Processing'], subdomain_counts['Geographic Information System-Mapping'], subdomain_counts['Geographic Information System-Spatial Analysis'], subdomain_counts['Geographic Information System-Data Collection'], subdomain_counts['Geographic Information System-Geographic Visualization'], subdomain_counts['Geographic Information System-Location Services'], subdomain_counts['Geographic Information System-Environmental Modeling'], subdomain_counts['Input-Output-Data Reading'], subdomain_counts['Input-Output-Data Writing'], subdomain_counts['Input-Output-Stream Management'], subdomain_counts['Input-Output-Buffering Strategies'], subdomain_counts['Input-Output-File Management'], subdomain_counts['Input-Output-Network IO'], subdomain_counts['Interpreter-Script Execution'], subdomain_counts['Interpreter-Code Translation'], subdomain_counts['Interpreter-Memory Management'], subdomain_counts['Interpreter-Syntax Analysis'], subdomain_counts['Interpreter-Optimization'], subdomain_counts['Interpreter-Debugging'], subdomain_counts['Internationalization-Localization'], subdomain_counts['Internationalization-Language Support'], subdomain_counts['Internationalization-Cultural Adaptation'], subdomain_counts['Internationalization-Currency Conversion'], subdomain_counts['Internationalization-Date/Time Formatting'], subdomain_counts['Internationalization-Right-to-Left Layouts'], subdomain_counts['Logic-Control Structures'], subdomain_counts['Logic-Algorithm Implementation'], subdomain_counts['Logic-Logic Optimization'], subdomain_counts['Logic-Validation Checks'], subdomain_counts['Logic-Rule Processing'], subdomain_counts['Logic-Decision Making'], subdomain_counts['Language-Syntax Features'], subdomain_counts['Language-Compiler/Interpreter Enhancements'], subdomain_counts['Language-Runtime Optimization'], subdomain_counts['Language-Standard Libraries'], subdomain_counts['Language-Language Extensions'], subdomain_counts['Language-Type Systems'], subdomain_counts['Logging-Event Logging'], subdomain_counts['Logging-System Monitoring'], subdomain_counts['Logging-Performance Tracking'], subdomain_counts['Logging-Error Logs'], subdomain_counts['Logging-User Activity Logs'], subdomain_counts['Logging-Audit Trails'], subdomain_counts['Machine Learning-Training Models'], subdomain_counts['Machine Learning-Prediction'], subdomain_counts['Machine Learning-Data Preprocessing'], subdomain_counts['Machine Learning-Feature Extraction'], subdomain_counts['Machine Learning-Model Evaluation'], subdomain_counts['Machine Learning-Deployment'], subdomain_counts['Microservices/Services-Service Discovery'], subdomain_counts['Microservices/Services-Load Balancing'], subdomain_counts['Microservices/Services-API Gateway'], subdomain_counts['Microservices/Services-Service Communication'], subdomain_counts['Microservices/Services-Fault Tolerance'], subdomain_counts['Microservices/Services-Service Deployment'], subdomain_counts['Multimedia-Media Playback'], subdomain_counts['Multimedia-Media Editing'], subdomain_counts['Multimedia-Encoding and Decoding'], subdomain_counts['Multimedia-Streaming'], subdomain_counts['Multimedia-Content Delivery'], subdomain_counts['Multimedia-Media Storage'], subdomain_counts['Multi-Thread-Concurrency Control'], subdomain_counts['Multi-Thread-Synchronization'], subdomain_counts['Multi-Thread-Thread Safety'], subdomain_counts['Multi-Thread-Parallel Processing'], subdomain_counts['Multi-Thread-Resource Sharing'], subdomain_counts['Multi-Thread-Deadlock Resolution'], subdomain_counts['Natural Language Processing-Text Analysis'], subdomain_counts['Natural Language Processing-Speech Recognition'], subdomain_counts['Natural Language Processing-Language Generation'], subdomain_counts['Natural Language Processing-Sentiment Analysis'], subdomain_counts['Natural Language Processing-Machine Translation'], subdomain_counts['Natural Language Processing-Chatbot Interfaces'], subdomain_counts['Network-Protocol Implementation'], subdomain_counts['Network-Connection Management'], subdomain_counts['Network-Data Transmission'], subdomain_counts['Network-Network Security'], subdomain_counts['Network-Bandwidth Optimization'], subdomain_counts['Network-Network Monitoring'], subdomain_counts['Operating System)-Process Management'], subdomain_counts['Operating System)-Memory Management'], subdomain_counts['Operating System)-Device Drivers'], subdomain_counts['Operating System)-File Systems'], subdomain_counts['Operating System)-User Interface'], subdomain_counts['Operating System)-System Security'], subdomain_counts['Parser-Syntax Parsing'], subdomain_counts['Parser-Error Recovery'], subdomain_counts['Parser-Data Conversion'], subdomain_counts['Parser-Optimization'], subdomain_counts['Parser-Code Generation'], subdomain_counts['Parser-Validation'], subdomain_counts['Search-Indexing'], subdomain_counts['Search-Query Processing'], subdomain_counts['Search-Ranking'], subdomain_counts['Search-Optimization'], subdomain_counts['Search-Caching'], subdomain_counts['Search-Personalization'], subdomain_counts['Security-Authentication'], subdomain_counts['Security-Authorization'], subdomain_counts['Security-Encryption'], subdomain_counts['Security-Intrusion Detection'], subdomain_counts['Security-Compliance'], subdomain_counts['Security-Data Integrity'], subdomain_counts['Setup-Installation'], subdomain_counts['Setup-Configuration'], subdomain_counts['Setup-System Requirements'], subdomain_counts['Setup-Update Management'], subdomain_counts['Setup-Licensing'], subdomain_counts['Setup-Environment Setup'], subdomain_counts['User Interface-Layout Design'], subdomain_counts['User Interface-Interaction Design'], subdomain_counts['User Interface-Accessibility'], subdomain_counts['User Interface-Animation'], subdomain_counts['User Interface-Responsive Design'], subdomain_counts['User Interface-User Feedback'], subdomain_counts['Utility-Data Conversion'], subdomain_counts['Utility-System Tools'], subdomain_counts['Utility-Automation Scripts'], subdomain_counts['Utility-Performance Tools'], subdomain_counts['Utility-Diagnostic Utilities'], subdomain_counts['Utility-Backup Tools'], subdomain_counts['Test-Unit Testing'], subdomain_counts['Test-Integration Testing'], subdomain_counts['Test-Performance Testing'], subdomain_counts['Test-Security Testing'], subdomain_counts['Test-Usability Testing'], subdomain_counts['Test-Regression Testing']))
        conn.commit()
    cur.close()
    conn.close()
        # with open(csv_file, 'a', newline='') as file:
        #     file.seek(0, os.SEEK_END)  # Move pointer to the end of file
        #     writer = csv.writer(file)
        #     if file.tell() == 0:  # Check if file is empty
        #         writer.writerow(['filename', 'domains', 'subdomains'])  # Write header row if file is empty
        #     domains_str = ', '.join(domains)
        #     subdomains_str = ', '.join(subdomains)
        #     if subdomains_str == "":
        #         subdomains_str = "None Used"
        #     writer.writerow([file_name, domains_str, subdomains_str])


# Example usage:
# csv_file = 'data.csv'
# key_name = input("Enter key name to check and possibly add: ")
# description = input("Enter description: ")
#
# add_to_csv(csv_file, key_name, description)
# print(get_from_csv('function_storage.csv', 'java.util.List'))

# csv_file = 'test.csv'
# file_name = 'java.util.test'
# domains = ['UI', 'DB', 'etc.']
# subdomains = ['UI-event', 'DB-connection', 'etc']
#
# store_file(csv_file, file_name, domains, subdomains)


# Example usage of SQL to CSV

# # Path to your SQLite database
# db_path = 'example.db'

# # Create and populate the database
# create_and_populate_db(db_path)

# # Export the table to a CSV
# sqlite_to_csv(db_path, 'example_table', 'output.csv')

# # Load and print the CSV to verify
# df = pd.read_csv('output.csv')
# print(df)
