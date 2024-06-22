import csv
import sqlite3
import ast

from src import store_result


def read_specific_column(filepath, column_name):
    with open(filepath, 'r') as file:
        csv_reader = csv.DictReader(file)
        column_values = []
        for row in csv_reader:
            column_values.append(row[column_name])
        return [column.split(',') for column in column_values]


def read_full_column(filepath, column_name):
    with open(filepath, 'r') as file:
        csv_reader = csv.DictReader(file)
        column_values = []
        for row in csv_reader:
            column_values.append(row[column_name])
        return [column for column in column_values]
# File path
# file_path = './issues_data2.csv'
# column_name = 'PR Files'


def pull_csv(file_path, column_name):
    column_data = read_specific_column(file_path, column_name)
    change_files = set()

    for column in column_data:
        for item in column:
            item = item.replace('[', '').replace(']', '').replace("'", "")
            if item.endswith(".java"):
                change_files.add(item)
    return change_files


## NEEDS UPDATE
def update_csv_with_results(file_path, column_name, results):
    with open(file_path, 'r') as file:
        csv_reader = csv.DictReader(file)
        fieldnames = csv_reader.fieldnames + ['Result']  # Add 'Result' as a new field
        rows = []
        for row in csv_reader:
            row['Result'] = results.pop(0)  # Add result to the row
            rows.append(row)

    with open(file_path, 'w', newline='') as file:
        csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_writer.writerows(rows)


def grab_values_at_files(file_list):
    results = []
    for file in file_list:
        #print("LOOK JHERE: " + str(file))
        if store_result.in_file('./output/file_data.db', file):
            # Connect to SQLite database
            conn = sqlite3.connect('./output/file_data.db')
            cur = conn.cursor()

            # Execute query to retrieve data
            cur.execute('''
                SELECT domains, subdomains, "Application", "Application Performance Manager", "Big Data",
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
                    "Test-Performance Testing", "Test-Security Testing", "Test-Usability Testing", "Test-Regression Testing" FROM storage WHERE filename = ?;
            ''', (file,))

            # Fetch all rows
            rows = cur.fetchall()

            cur.close()
            conn.close()

            results.append(rows)

    total_domains = []
    total_subdomains = []
    counts = []

    # Assuming both tuples have the same length
    for i in range(len(results[0][0])):
        total_count = 0
        for x in range(len(file_list)):
            if i >= 2:
                total_count += results[x][0][i]
            elif i == 0:
                total_domains.append(results[x][0][i])
            else:
                total_subdomains.append(results[x][0][i])
        if i >= 2:
            counts.append(total_count)

    domains = []
    subdomains = []
    for i in range(len(total_domains)):
        # Parse the string representation of the inner array
        inner_array = ast.literal_eval(total_domains[i])
        for x in inner_array:
            domains.append(x)
    for i in range(len(total_subdomains)):
        # Parse the string representation of the inner array
        inner_array = ast.literal_eval(total_subdomains[i])
        for x in inner_array:
            subdomains.append(x)
    return domains, subdomains, counts



# column_data = read_full_column('issues_data2.csv', 'PR Files')
# results = []
#
# for file in column_data:
#     # Convert the string to an actual array
#     array = eval(file)
#     array_of_javas = []
#     for input in array:
#         if input.endswith(".java"):
#             array_of_javas.append(input)
#
#     array_of_results = []
#     for java_file in array_of_javas:
#         result = csv_push.find_values_by_filename('test.csv', java_file)
#         if isinstance(result, tuple):
#             domains, subdomains = result
#             array_of_results.append("{" + java_file + ": [" + domains + "], [" + subdomains + "]}")
#         else:
#             array_of_results.append(result)
#     results.append(array_of_results)
#
# update_csv_with_results('issues_data2 test.csv', 'PR Files', results)
    # print(array[0])
    #
    # # Print the array
    # print("Yippee: " + str(array))
