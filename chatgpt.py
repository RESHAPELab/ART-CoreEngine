from g4f.client import Client

####
#
#  This file is old! I think this will be completely replaced (and deleted) by Hunters Taxonomy algorithm. 
#
####

client = Client()
messages = [
    {"role": "system",
     "content": "You are attempting to classify the inputted description into one of the 31 labels based off of the similarity to it."},
    {"role": "system",
     "content": "Your response must be one word, which is the label of the description."}
]



# Labels and their descriptions
options = {
    "Application": "third party apps or plugins for specific use attached to the system",
    "Application Performance Manager": "monitors performance or benchmark",
    "Big Data": "API's that deal with storing large amounts of data. with variety of formats",
    "Cloud": "APUs for software and services that run on the Internet",
    "Computer Graphics": "Manipulating visual content",
    "Data Structure": "Data structures patterns (e.g., collections, lists, trees)",
    "Databases": "Databases or metadata",
    "Software Development and IT": "Libraries for version control, continuous integration and continuous delivery",
    "Error Handling": "response and recovery procedures from error conditions",
    "Event Handling": "answers to event like listeners",
    "Geographic Information System": "Geographically referenced information",
    "Input/Output": "read, write data",
    "Interpreter": "compiler or interpreter features",
    "Internationalization": "integrate and infuse international, intercultural, and global dimensions",
    "Logic": "frameworks, patterns like commands, controls, or architecture-oriented classes",
    "Language": "internal language features and conversions",
    "Logging": "log registry for the app",
    "Machine Learning": "ML support like build a model based on training data",
    "Microservices/Services": "Independently deployable smaller services. Interface between two different applications so that they can communicate with each other",
    "Multimedia": "Representation of information with text, audio, video",
    "Multithread": "Support for concurrent execution",
    "Natural Language Processing": "Process and analyze natural language data",
    "Network": "Web protocols, sockets RMI APIs",
    "Operating System": "APIs to access and manage a computer's resources",
    "Parser": "Breaks down data into recognized pieces for further analysis",
    "Search": "API for web searching",
    "Security": "Crypto and secure protocols",
    "Setup": "Internal app configurations",
    "User Interface": "Defines forms, screens, visual controls",
    "Utility": "third party libraries for general use",
    "Test": "test automation"
}

def askGPT_ClassDescription(classDescription, label_options=options):
    # Construct the prompt with the object description and option descriptions
    prompt = f"In a coding program there is a class with the following description: \n"
    prompt += f"{classDescription}\n"
    prompt += " more fit with which of these options: "
    prompt += f"Options: {label_options}\n"
    prompt += "Respond with what category this class best fits in.\n"
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        stream=True
    )

    answer = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            answer += (chunk.choices[0].delta.content.strip('*') or "")
    return answer

def askGPT_FunctionDescription(functionDescription, classFullName, label_options=options):
    # Construct the prompt with the object description and option descriptions
    prompt = f"In a coding program this function is used belonging to the {classFullName} class. Does this function description: \n{functionDescription}"
    prompt += "\n more fit with which of these options: "
    prompt += f"Options: {label_options}\n"
    prompt += "Respond with what category this function best fits in.\n"
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        stream=True
    )

    answer = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            answer += (chunk.choices[0].delta.content.strip('*') or "")
    return answer

def getClientProvider():
    return client.chat.completions.provider

