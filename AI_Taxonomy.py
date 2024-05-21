#Hunter Jenkins
#Taxonomy Tests Version 1
#AI function calls

#This is well documented with improvements that could be made earlier on for better taxonomy
#This should not require any changes to this file unless alteration for output
#We should be calling on this file with the "GetDomains" file 
#in this main file i included variable to show one text example if someone wanted to run the main


import datetime
import json
from openai import OpenAI
from dotenv import load_dotenv # do a pip install dotenv
import os
import random

from DatabaseManager import DatabaseManager

load_dotenv()

# The comments below the function signatures are called docstrings
# and can be autoformatted with a VS Code extension. I use "autoDocstring"
# from https://marketplace.visualstudio.com/items?itemName=njpwerner.autodocstring

class AIClassifier():
    def __init__(self, api_domain_label_listing : dict, subdomain_label_listing : dict):
        """Setup OpenAI API key. Import label listings. API Domains and subdomains.

        Args:
            api_domain_label_listing (dict): From labels.json
            subdomain_label_listing (dict): From Merged_API_Sub_Domains_Descriptions.json
        """

        # csv
        LOG_FILE = "./generatedFiles/ai_log.csv"

        OpenAI.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.api_label_listing = api_domain_label_listing
        self.subdomain_label_listing = subdomain_label_listing
        self.LOG_FILE = LOG_FILE

    def parse_domain_description(self, text : str):
        """Extracts the domain and description from an OpenAI Query Response

        Args:
            text (str): Response from OpenAI

        Returns:
            str: Domain
            str: Description 
        """
        # Define potential delimiters that separate the domain from the description
        delimiters = ["\n", " - ", "\nDescription: ", ": "]
        
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

    def classify_API(self, api : str):
        return random.choice(["cat","dog","bird","rabbit","hen","pig","cow"])
        """Classifies a classname "API" into a domain.

        Args:
            api (str): The classname "api"

        Returns:
            str: domain
            str: description
            str: complete AI response
        """

        # LOG
        with open(self.LOG_FILE, 'a') as file:
            file.write(f"{datetime.datetime.now()},API,{api}")

        #Storing and approving past classfications in a database. THis would take manual work at first but maybe we can add a functon to the program design where#
        # the user validates the AIs reponse such as upvoting it

        #Cassify the API into the orginal domains

        # Convert the JSON data into a text format suitable for asking questions
        text = json.dumps(self.api_label_listing, indent=2)  # You might still want to convert it to ensure it's readable

        # Directly include the full question in the OpenAI API call
        question = (
        f"Please analyze the provided descriptions and the details of the imported API, then determine the most fitting domain from a list of 31 labels. "
        f"Return like this domain - description, only the name of the selected domain and a brief description of this domain. "
        f"API details: {api}. Context: {text}. Do not include any additional information or reasoning in your response.")


        # Query the OpenAI API
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "user", "content": question}
            ]
        )
        # Accessing the chat response correctly
        response = completion.choices[0].message.content # Assuming this is the correct path based on your API response structure

        ##print(response)

        domain, description = self.parse_domain_description(response)
        
        with open(self.LOG_FILE, 'a') as file:
            file.write(f",{domain}\n")

        return domain, description, response

    def classify_function(self, api_name : str, function_name : str, api_domain : str):
        return random.choice(["grain","rice","seed","carrots","straw","grass","wheat"])
        """Classify a function into a subdomain, given classname and class domain.

        Args:
            api_name (str): _description_
            function_name (str): _description_
            api_domain (str): _description_

        Returns:
            str: subdomain
            str: description
            str: response
        """
        # LOG
        with open(self.LOG_FILE, 'a') as file:
            file.write(f"{datetime.datetime.now()},FUNC,{api_name},{function_name},{api_domain}")

        if not(api_domain in self.subdomain_label_listing):
            out = f"No sub-domain for function '{function_name}'."
            with open(self.LOG_FILE, 'a') as file:
                file.write(f",{out}\n")
            return out

        sub_domains_descriptions = []
        for item in self.subdomain_label_listing[api_domain]:
            for sub_domain, description in item.items():
                #print(f"  - {sub_domain}: {description}")
                sub_domains_descriptions.append(f"{sub_domain}: {description}")
        
        # Join all sub-domain descriptions into a single string for the query
        sub_domains_descriptions_str = "\n ".join(sub_domains_descriptions)

        
        prompt_text = (
            f"Analyze the following information about the API function '{function_name}' which is part of the '{api_name}' in the '{api_domain}' domain. "
            f"Choose the most relevant classification from these available sub-domain options: \n{sub_domains_descriptions_str}. "
            f"Please provide only the name of the most appropriate subdomain and the description of it, without any additional details or explanation."
        )
        # Query the OpenAI API
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "user", "content": prompt_text}
            ]
        )
        #print(completion.choices[0].message.content)
        response = completion.choices[0].message.content # Assuming this is the correct path based on your API response structure

        ##print(response)

        sub_domain, description = self.parse_domain_description(response)
        
        with open(self.LOG_FILE, 'a') as file:
               file.write(f",{sub_domain}\n")

        return sub_domain, description, response

    def classify_class_and_function(self, fullname : str):
        """Classify class and function from the full name at once.

        Args:
            fullname (str): Class and function full name, like this: java.swing.JFrame::open

        Returns:
            str: domain of class
            str: description of domain of class
            str: response of domain of class
            str: subdomain of function
            str: subdescription of function
            str: subresponse of function
        """
        api_name = fullname.split("::")[0]
        domain, description, response  = self.classify_API(api_name)
        function_name = fullname.split("::")[1]
        subdomain, subdescription, subresponse  = self.classify_function(api_name, function_name, domain)
        return domain, description, response, subdomain, subdescription, subresponse


class AICachedClassifier(AIClassifier):
    def __init__(self, api_domain_label_listing : dict, subdomain_label_listing : dict, db : DatabaseManager):
        self.db = db
        super().__init__(api_domain_label_listing, subdomain_label_listing)
    
    def classify_API(self, api : str):
        cache_result = self.db.cache_classify_API(api)
        if(cache_result is None):
            domain, _a , _b = super().classify_API(api)
            self.db.store_class_classification(api, domain) 
            return domain     
        else:
            return cache_result
        
    def classify_function(self, api_name: str, function_name: str, api_domain: str):
        cache_result = self.db.cache_classify_function(api_name, function_name)
        if(cache_result is None):
            subdomain, _a , _b = super().classify_function(api_name, function_name, api_domain)
            self.db.store_function_classification(api_name, function_name, subdomain)      
            return subdomain
        else:
            return cache_result
    
    def classify_class_and_function(self, fullname: str):
        """Classify class and function from the full name at once.

        Args:
            fullname (str): Class and function full name, like this: java.swing.JFrame::open

        Returns:
            str: domain of class
            str: description of domain of class
            str: response of domain of class
            str: subdomain of function
            str: subdescription of function
            str: subresponse of function
        """
        api_name = fullname.split("::")[0]
        domain  = self.classify_API(api_name)
        function_name = fullname.split("::")[1]
        subdomain  = self.classify_function(api_name, function_name, domain)
        return domain, subdomain
    
        
#Load File
def load_data(filename : str):
    """Load JSON Dict from filename

    Args:
        filename (str): filename to load from. Assume working directory

    Returns:
        dict: json dictionary.
    """
    with open(filename) as file:
        return json.load(file)

#Ideas for improvement
#Pinecone Database - somehow having a database with GENERAL context on functions and APIs non dependent on the language this could improve
#the model and ai request without there being bottleneck to a specefic language


def main():
    """Main function to execute the script"""
    #-----------------------
    #Removed anything in () after the main name of the labels just incase openAI forgot to put it in the response
    API_listing_file = 'domain_labels.json' #Dont change, specefic file needed in folder
    sub_domain_listing_file = 'subdomain_labels.json' #Dont Change, Specefic File Needed in Folder
    #-----------------------

    api_domain_listing = load_data(API_listing_file)
    sub_domain_listing = load_data(sub_domain_listing_file)

    classifier = AIClassifier(api_domain_listing, sub_domain_listing)

    fullName = "java.sql.Connection::createStatement"

    # For testing purposes we can keep these until needed since we arent calling on the main as of right now
    api_name = fullName.split("::")[0]
    domain, description, response  = classifier.classify_API(api_name)
    print("DOMAIN: ", domain)
    print("DESCRIPTION: ",description)
    print("RESPONSE: ", response)
    print("\n")
    function_name = fullName.split("::")[1]
    #When calling the classify function we need the api_domain that the api is apart of. This is because we are getting a sub domain for the function.
    # For example... api_name java.sql.connection falls under the domain "Database (DB), if the function_name is createStatement the sub_domain 
    # will be one of the ones under the Database (DB) domain, so it would be Quert Execution according to AI
    # THe goal here is to give the AI as much context as possible because I realized when it understood the API and api domain it made better function classifications when testing
    function_sub_domain, description, response = classifier.classify_function(api_name, function_name, domain)
    print("FUNCTION SUBDOMAIN: ", function_sub_domain)
    print("DESCRIPTION: ",description)
    print("RESPONSE: ", response)


if __name__ == "__main__":
    main()