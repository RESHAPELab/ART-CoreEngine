import sqlite3


def start():
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
