import csv
import sqlite3
import pandas as pd


# Convert to grab stuff from db
def find_values_by_filename(csv_file, filename):
    conn = sqlite3.connect(csv_file)
    cur = conn.cursor()

    query = '''
        SELECT domains, subdomains
        FROM storage
        WHERE filename = ?;
        '''
    cur.execute(query, (filename,))

    # Fetch the result
    result = cur.fetchone()

    # Check if a result was found and print the last_name
    if result:
        cur.close()
        conn.close()
        return result[0], result[1]
        # print(f"The last name for '{key_name}' is '{last_name}'.")
    else:
        cur.close()
        conn.close()
        return filename + "not found"
    # with open(csv_file, mode='r') as file:
    #     reader = csv.DictReader(file, delimiter=',')
    #
    #     # Check if 'filename' exists in the fieldnames
    #     if 'filename' not in reader.fieldnames:
    #         return "Column 'filename' not found in the CSV file"
    #
    #     # Iterate over each row
    #     for row in reader:
    #         # Check if the filename contains the given filename
    #         if filename in row['filename']:
    #             return row['domains'], row['subdomains']
    #
    #
    #     # If the filename is not found
    #     return filename + " not found"


def update_original_csv(csv_file, domains, subdomains, counts):
    header = [
        'domains', 'subdomains', 'Application', 'Application Performance Manager', 'Big Data',
        'Cloud', 'Computer Graphics', 'Data Structure', 'Databases',
        'Software Development and IT Operations', 'Error Handling', 'Event Handling',
        'Geographic Information System', 'Input-Output', 'Interpreter',
        'Internationalization', 'Logic', 'Language', 'Logging',
        'Machine Learning', 'Microservices/Services', 'Multimedia',
        'Multi-Thread', 'Natural Language Processing', 'Network',
        'Operating System', 'Parser', 'Search', 'Security', 'Setup',
        'User Interface', 'Utility', 'Test', 'Application-Integration',
        'Application-Plugin Management', 'Application-User Customization',
        'Application-App Configuration', 'Application-Version Control',
        'Application-Compatibility Checks', 'Application Performance Manager-Performance Monitoring',
        'Application Performance Manager-Resource Allocation',
        'Application Performance Manager-Error Detection', 'Application Performance Manager-Load Balancing',
        'Application Performance Manager-Traffic Management', 'Application Performance Manager-Diagnostic Tools',
        'Big Data-Data Processing', 'Big Data-Data Storage', 'Big Data-Data Analysis',
        'Big Data-Real-Time Processing', 'Big Data-Batch Processing', 'Big Data-Data Visualization',
        'Cloud-Resource Management', 'Cloud-Virtualization', 'Cloud-Scalability Solutions',
        'Cloud-Cloud Security', 'Cloud-Data Migration', 'Cloud-Service Configuration',
        'Computer Graphics-Image Rendering', 'Computer Graphics-Animation', 'Computer Graphics-Modeling',
        'Computer Graphics-Texture Mapping', 'Computer Graphics-Visual Effects',
        'Computer Graphics-Graphics Optimization', 'Data Structure-Linear Structures',
        'Data Structure-Tree Structures', 'Data Structure-Graph Structures', 'Data Structure-Data Sorting',
        'Data Structure-Search Algorithms', 'Data Structure-Data Manipulation', 'Databases-Query Execution',
        'Databases-Transaction Management', 'Databases-Schema Design', 'Databases-Database Security',
        'Databases-Backup and Recovery', 'Databases-Database Optimization',
        'Software Development and IT Operations-Continuous Integration',
        'Software Development and IT Operations-Continuous Deployment',
        'Software Development and IT Operations-Automated Testing',
        'Software Development and IT Operations-Configuration Management',
        'Software Development and IT Operations-Version Control',
        'Software Development and IT Operations-Monitoring and Logging', 'Error Handling-Exception Handling',
        'Error Handling-Error Logging', 'Error Handling-Fault Tolerance', 'Error Handling-Debugging Tools',
        'Error Handling-User Notification', 'Error Handling-Error Prevention', 'Event Handling-User Interactions',
        'Event Handling-System Events', 'Event Handling-Event Logging', 'Event Handling-Event Driven Processing',
        'Event Handling-Notifications', 'Event Handling-Asynchronous Processing',
        'Geographic Information System-Mapping',
        'Geographic Information System-Spatial Analysis', 'Geographic Information System-Data Collection',
        'Geographic Information System-Geographic Visualization', 'Geographic Information System-Location Services',
        'Geographic Information System-Environmental Modeling', 'Input-Output-Data Reading',
        'Input-Output-Data Writing',
        'Input-Output-Stream Management', 'Input-Output-Buffering Strategies', 'Input-Output-File Management',
        'Input-Output-Network IO',
        'Interpreter-Script Execution', 'Interpreter-Code Translation', 'Interpreter-Memory Management',
        'Interpreter-Syntax Analysis',
        'Interpreter-Optimization', 'Interpreter-Debugging', 'Internationalization-Localization',
        'Internationalization-Language Support',
        'Internationalization-Cultural Adaptation', 'Internationalization-Currency Conversion',
        'Internationalization-Date/Time Formatting',
        'Internationalization-Right-to-Left Layouts', 'Logic-Control Structures', 'Logic-Algorithm Implementation',
        'Logic-Logic Optimization', 'Logic-Validation Checks', 'Logic-Rule Processing', 'Logic-Decision Making',
        'Language-Syntax Features', 'Language-Compiler/Interpreter Enhancements', 'Language-Runtime Optimization',
        'Language-Standard Libraries', 'Language-Language Extensions', 'Language-Type Systems', 'Logging-Event Logging',
        'Logging-System Monitoring', 'Logging-Performance Tracking', 'Logging-Error Logs', 'Logging-User Activity Logs',
        'Logging-Audit Trails', 'Machine Learning-Training Models', 'Machine Learning-Prediction',
        'Machine Learning-Data Preprocessing',
        'Machine Learning-Feature Extraction', 'Machine Learning-Model Evaluation', 'Machine Learning-Deployment',
        'Microservices/Services-Service Discovery',
        'Microservices/Services-Load Balancing', 'Microservices/Services-API Gateway',
        'Microservices/Services-Service Communication', 'Microservices/Services-Fault Tolerance',
        'Microservices/Services-Service Deployment', 'Multimedia-Media Playback', 'Multimedia-Media Editing',
        'Multimedia-Encoding and Decoding', 'Multimedia-Streaming',
        'Multimedia-Content Delivery', 'Multimedia-Media Storage', 'Multi-Thread-Concurrency Control',
        'Multi-Thread-Synchronization', 'Multi-Thread-Thread Safety',
        'Multi-Thread-Parallel Processing', 'Multi-Thread-Resource Sharing', 'Multi-Thread-Deadlock Resolution',
        'Natural Language Processing-Text Analysis',
        'Natural Language Processing-Speech Recognition', 'Natural Language Processing-Language Generation',
        'Natural Language Processing-Sentiment Analysis',
        'Natural Language Processing-Machine Translation', 'Natural Language Processing-Chatbot Interfaces',
        'Network-Protocol Implementation', 'Network-Connection Management',
        'Network-Data Transmission', 'Network-Network Security', 'Network-Bandwidth Optimization',
        'Network-Network Monitoring', 'Operating System-Process Management',
        'Operating System-Memory Management', 'Operating System-Device Drivers', 'Operating System-File Systems',
        'Operating System-User Interface', 'Operating System-System Security',
        'Parser-Syntax Parsing', 'Parser-Error Recovery', 'Parser-Data Conversion', 'Parser-Optimization',
        'Parser-Code Generation', 'Parser-Validation', 'Search-Indexing',
        'Search-Query Processing', 'Search-Ranking', 'Search-Optimization', 'Search-Caching', 'Search-Personalization',
        'Security-Authentication', 'Security-Authorization',
        'Security-Encryption', 'Security-Intrusion Detection', 'Security-Compliance', 'Security-Data Integrity',
        'Setup-Installation', 'Setup-Configuration',
        'Setup-System Requirements', 'Setup-Update Management', 'Setup-Licensing', 'Setup-Environment Setup',
        'User Interface-Layout Design', 'User Interface-Interaction Design',
        'User Interface-Accessibility', 'User Interface-Animation', 'User Interface-Responsive Design',
        'User Interface-User Feedback', 'Utility-Data Conversion', 'Utility-System Tools',
        'Utility-Automation Scripts', 'Utility-Performance Tools', 'Utility-Diagnostic Utilities',
        'Utility-Backup Tools', 'Test-Unit Testing', 'Test-Integration Testing', 'Test-Performance Testing',
        'Test-Security Testing', 'Test-Usability Testing', 'Test-Regression Testing']

    # Load the existing CSV file
    df = pd.read_csv(csv_file)

    # Define new column names and data
    new_columns = {
        header[0]: domains,
        header[1]: subdomains
    }

    # Update new_columns with counts
    for i in range(len(counts)):
        new_columns[header[i + 2]] = counts[i]

    # Ensure all new columns exist in the DataFrame
    for col in new_columns:
        if col not in df.columns:
            df[col] = None

    # Find the first empty row for new data
    empty_row_index = df.index[df['domains'].isna() & df['subdomains'].isna()].min()

    # Fill in the new data for the first empty row
    df.at[empty_row_index, 'domains'] = domains
    df.at[empty_row_index, 'subdomains'] = subdomains
    for col, val in new_columns.items():
        df.at[empty_row_index, col] = val

    # Save the updated CSV
    df.to_csv(csv_file, index=False)

# Example usage
# csv_file = 'test.csv'
# filename_to_find = 'src/main/java/org/jabref/gui/entryeditor/fileannotationtab/FileAnnotationTab.java'
# result = find_values_by_filename(csv_file, filename_to_find)
#
# if isinstance(result, tuple):
#     domains, subdomains = result
#     print("{" + filename_to_find + ": [" + domains + "], [" + subdomains + "]}")
# else:
#     print(result)
