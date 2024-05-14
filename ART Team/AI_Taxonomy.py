#Hunter Jenkins
#Taxonomy Tests Version 1
#AI function calls

#This is well documented with improvements that could be made earlier on for better taxnomy
#This should not require any changes to this file unless alteration for output
#We should be calling on this file with the "GetDomains" file 
#in this main file i included variable to show one text example if someone wanted to run the main


import json
from openai import OpenAI
#QUESTIONS
#How can I help or alter what I am doing for the classifications as well as change things to help the predictions team

# Initialize the OpenAI client
OpenAI.api_key = 'YOUR_API_KEY'  # Replace with your actual API key
client = OpenAI()

#Load File
def load_data(filename):
    with open(filename) as file:
        return json.load(file)

#Ideas for improvement
#Pinecone Database - somehow having a database with GENERAL context on functions and APIs non dependent on the language this could improve
#the model and ai request without there being bottleneck to a specefic language

#Storing and approving past classfications in a database. THis would take manual work at first but maybe we can add a functon to the program design where#
# the user validates the AIs reponse such as upvoting it

#Cassify the API into the orginal domains
def classify_API(API_file, API):
    # Load JSON data from the specified path
    with open(API_file, 'r') as file:
        data = json.load(file)

    # Convert the JSON data into a text format suitable for asking questions
    text = json.dumps(data, indent=2)  # You might still want to convert it to ensure it's readable

    # Directly include the full question in the OpenAI API call
    question = (
    f"Please analyze the provided descriptions and the details of the imported API, then determine the most fitting domain from a list of 31 labels. "
    f"Return like this domain - description, only the name of the selected domain and a brief description of this domain. "
    f"API details: {API}. Context: {text}. Do not include any additional information or reasoning in your response.")


    # Query the OpenAI API
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "user", "content": question}
        ]
    )
    # Accessing the chat response correctly
    response = completion.choices[0].message.content # Assuming this is the correct path based on your API response structure

    ##print(response)

    domain, description = parse_domain_description(response)
    
    return domain, response

def parse_domain_description(text):
    # Define potential delimiters that separate the domain from the description
    delimiters = ["\n", " - ", "\nDescription: "]
    
    # Initial split to isolate the domain from the rest of the text
    for delimiter in delimiters:
        parts = text.split(delimiter, 1)
        if len(parts) > 1:
            # Assume the first part is the domain, and the rest is the description
            domain = parts[0].strip()
            description = parts[1].strip()
            return domain, description
    
    # If no delimiter effectively splits the text, return the entire text as domain
    return text.strip(), "No description found"

# Classify function based on domain
def classify_function(api_name, function_name, api_domain, sub_domain_file):
     # Load JSON data from the specified path
    with open(sub_domain_file, 'r') as file:
        data = json.load(file)

    if api_domain in data:
        sub_domains_descriptions = []
        for item in data[api_domain]:
            for sub_domain, description in item.items():
                #print(f"  - {sub_domain}: {description}")
                sub_domains_descriptions.append(f"{sub_domain}: {description}")
        
        # Join all sub-domain descriptions into a single string for the query
        sub_domains_descriptions_str = ", ".join(sub_domains_descriptions)

        
        prompt_text = (
            f"Analyze the following information about the API function '{function_name}' which is part of the '{api_name}' in the '{api_domain}' domain. "
            f"Choose the most relevant classification from these available sub-domain options: {sub_domains_descriptions_str}. "
            f"Please provide only the name of the most appropriate subdomain and the description of it, without any additional details or explanation."
        )
        # Query the OpenAI API
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "user", "content": prompt_text}
            ]
        )
        #print(completion.choices[0].message.content)
        return completion.choices[0].message.content
    else:
        return f"No sub-domain for function '{function_name}'."

# Main function to execute the script
def main():
    #-----------------------
    #Removed anything in () after the main name of the labels just incase openAI forgot to put it in the response
    API_file = 'labels.json' #Dont change, specefic file needed in folder
    sub_domain_file = 'Merged_API_Sub_Domains_Descriptions.json' #Dont Change, Specefic File Needed in Folder
    #-----------------------

    # For testing purposes we can keep these until needed since we arent calling on the main as of right now
    api_name = "java.sql.Connection;"
    domain , domainAndDescription  = classify_API(API_file, api_name)
    print(domain)
    function_name = "createStatement()"
    print(domainAndDescription)

    #When calling the classify function we need the api_domain that the api is apart of. This is because we are getting a sub domain for the function.
    # For example... api_name java.sql.connection falls under the domain "Database (DB), if the function_name is createStatement the sub_domain 
    # will be one of the ones under the Database (DB) domain, so it would be Quert Execution according to AI
    # THe goal here is to give the AI as much context as possible because I realized when it understood the API and api domain it made better function classifications when testing
    function_sub_domain = classify_function(api_name, function_name, domain, sub_domain_file)
    print(function_sub_domain)

if __name__ == "__main__":
    main()