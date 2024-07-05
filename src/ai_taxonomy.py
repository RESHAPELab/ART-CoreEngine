# Anonymous Author
# Taxonomy Tests Version 1
# AI function calls

# This is well documented with improvements that could be made earlier on for better taxonomy
# This should not require any changes to this file unless alteration for output
# We should be calling on this file with the "GetDomains" file
# in this main file i included variable to show one text example if someone wanted to run the main


import datetime
import json
import lzma
from openai import OpenAI
from dotenv import load_dotenv  # do a pip install dotenv
import os
import random
import tiktoken  # pip install tiktoken
import lzma
import pickle

from .database_manager import DatabaseManager

# Do True to use fake domains (animals and animal-feed)
# Do False to use actual AI

# Please ask/double check before setting it to false. We really don't need
# the real data until the very end. (On final export to predictions team)
USE_DEBUG_VALUES = False

# Features logging,
# If you want to see the AI calls in real time, run
# `tail -n 100 -f output/ai_log.csv`

load_dotenv()

# The comments below the function signatures are called docstrings
# and can be autoformatted with a VS Code extension. I use "autoDocstring"
# from https://marketplace.visualstudio.com/items?itemName=njpwerner.autodocstring


class AIClassifier:
    def __init__(self, api_domain_label_listing: dict, subdomain_label_listing: dict):
        """Setup OpenAI API key. Import label listings. API Domains and subdomains.

        Args:
            api_domain_label_listing (dict): From labels.json
            subdomain_label_listing (dict): From Merged_API_Sub_Domains_Descriptions.json
        """

        # csv
        LOG_FILE = "./output/ai_log.csv"

        OpenAI.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.api_label_listing = api_domain_label_listing
        self.subdomain_label_listing = subdomain_label_listing
        self.LOG_FILE = LOG_FILE
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def parse_domain_description(self, text: str):
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

    def classify_API(self, api: str):
        """Classifies a classname "API" into a domain.

        Args:
            api (str): The classname "api"

        Returns:
            str: domain
            str: description
            str: complete AI response
        """

        # LOG
        with open(self.LOG_FILE, "a") as file:
            file.write(f"{datetime.datetime.now()},API,{api}")

        # Storing and approving past classfications in a database. THis would take manual work at first but maybe we can add a functon to the program design where#
        # the user validates the AIs reponse such as upvoting it

        # Cassify the API into the orginal domains

        # Convert the JSON data into a text format suitable for asking questions
        text = json.dumps(
            self.api_label_listing, indent=2
        )  # You might still want to convert it to ensure it's readable

        # Directly include the full question in the OpenAI API call
        question = (
            f"Please analyze the provided descriptions and the details of the imported API, then determine the most fitting domain from a list of 31 labels. "
            f"Return like this domain - description, only the name of the selected domain and a brief description of this domain. "
            f"API details: {api}. Context: {text}. Do not include any additional information or reasoning in your response."
        )

        response_tokens = []
        context_tokens = []
        response = None
        if not (USE_DEBUG_VALUES):
            # Query the OpenAI API

            context_tokens = self.tokenizer.encode(question)

            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                messages=[{"role": "user", "content": question}],
            )
            # Accessing the chat response correctly
            response = completion.choices[
                0
            ].message.content  # Assuming this is the correct path based on your API response structure
            response_tokens = self.tokenizer.encode(response)
        else:
            # use this for random testing so it does not cost anything!
            response = random.choice(
                ["cat", "dog", "bird", "rabbit", "hen", "pig", "cow"]
            )
            # Use "real" dummy data... instead of animals, use the actual label names
            response = random.choice(list(self.subdomain_label_listing.keys()))

        ##print(response)

        domain, description = self.parse_domain_description(response)

        with open(self.LOG_FILE, "a") as file:
            file.write(f",{domain},{len(context_tokens)},{len(response_tokens)}\n")

        context_pkl = pickle.dumps(context_tokens)
        response_pkl = pickle.dumps(response_tokens)

        context_raw = lzma.compress(context_pkl)
        response_raw = lzma.compress(response_pkl)

        return (
            domain,
            description,
            response,
            len(context_tokens),
            len(response_tokens),
            context_raw,
            response_raw,
        )

    def classify_function(self, api_name: str, function_name: str, api_domain: str):
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
        with open(self.LOG_FILE, "a") as file:
            file.write(
                f"{datetime.datetime.now()},FUNC,{api_name},{function_name},{api_domain}"
            )

        if api_domain in ["cat", "dog", "bird", "rabbit", "hen", "pig", "cow"]:
            api_domain = random.choice(list(self.subdomain_label_listing.keys()))

        if not (api_domain in self.subdomain_label_listing):
            out = f"No sub-domain for function '{function_name}'."
            with open(self.LOG_FILE, "a") as file:
                file.write(f",{out}\n")
            return out, None, None, -1, -1, None, None

        sub_domains_descriptions = []
        sub_domain_selection = []
        for item in self.subdomain_label_listing[api_domain]:
            for sub_domain, description in item.items():
                # print(f"  - {sub_domain}: {description}")
                sub_domains_descriptions.append(f"{sub_domain}: {description}")
                sub_domain_selection.append(sub_domain)

        # Join all sub-domain descriptions into a single string for the query
        sub_domains_descriptions_str = "\n ".join(sub_domains_descriptions)

        prompt_text = (
            f"Analyze the following information about the API function '{function_name}' which is part of the '{api_name}' in the '{api_domain}' domain. "
            f"Choose the most relevant classification from these available sub-domain options: \n{sub_domains_descriptions_str}. "
            f"Please provide only the name of the most appropriate subdomain and the description of it, without any additional details or explanation."
        )

        response_tokens = []
        context_tokens = []
        if not (USE_DEBUG_VALUES):
            # Query the OpenAI API
            context_tokens = self.tokenizer.encode(prompt_text)
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                messages=[{"role": "user", "content": prompt_text}],
            )
            # print(completion.choices[0].message.content)
            response = completion.choices[
                0
            ].message.content  # Assuming this is the correct path based on your API response structure
            response_tokens = self.tokenizer.encode(response)
        else:
            # use this for random testing so it does not cost anything!
            response = random.choice(
                ["grain", "rice", "seed", "carrots", "straw", "grass", "wheat"]
            )
            # Use "real" dummy data... instead of animal food, use the actual label names
            response = random.choice(sub_domain_selection)

        ##print(response)

        sub_domain, description = self.parse_domain_description(response)

        with open(self.LOG_FILE, "a") as file:
            file.write(f",{sub_domain},{len(context_tokens)},{len(response_tokens)}\n")

        context_pkl = pickle.dumps(context_tokens)
        response_pkl = pickle.dumps(response_tokens)

        context_raw = lzma.compress(context_pkl)
        response_raw = lzma.compress(response_pkl)

        return (
            sub_domain,
            description,
            response,
            len(context_tokens),
            len(response_tokens),
            context_raw,
            response_raw,
        )

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
        domain, description, response = self.classify_API(api_name)
        function_name = fullname.split("::")[1]
        subdomain, subdescription, subresponse = self.classify_function(
            api_name, function_name, domain
        )
        return domain, description, response, subdomain, subdescription, subresponse


class AICachedClassifier(AIClassifier):
    """The same thing as AIClassifier, but each call is wrapped by a cache request.

    This avoids overusing the AI

    Inherits:
        AIClassifier
    """

    def __init__(
        self,
        api_domain_label_listing: dict,
        subdomain_label_listing: dict,
        db: DatabaseManager,
    ):
        """Set up AI Classifier with Cache Support

        Args:
            api_domain_label_listing (dict): Dictionary Listing of all possible api (class) domains
            subdomain_label_listing (dict): Dictionary Listing of all possible subdomains
            db (DatabaseManager): Database Handler Object
        """
        self.db = db
        super().__init__(api_domain_label_listing, subdomain_label_listing)

    def classify_API(self, api: str) -> str:
        """Classify api/classname into a domain as defined by the domain label listing

        Args:
            api (str): API name

        Returns:
            str: domain of API
        """
        cache_result = self.db.cache_classify_API(api)
        if cache_result is None:
            domain, _a, _b, context_count, response_count, context, response = (
                super().classify_API(api)
            )
            self.db.store_class_classification(
                api, domain, context_count, response_count, context, response
            )
            return domain
        else:
            return cache_result

    def classify_function(
        self, api_name: str, function_name: str, api_domain: str
    ) -> str:
        """Classify function into a subdomain given class and class domain

        Args:
            api_name (str): API name / Class name
            function_name (str): Function name
            api_domain (str): Domain of the API as found by classify_API()

        Returns:
            str: subdomain of function
        """
        cache_result = self.db.cache_classify_function(api_name, function_name)
        if cache_result is None:
            subdomain, _a, _b, context_count, response_count, context, response = (
                super().classify_function(api_name, function_name, api_domain)
            )
            self.db.store_function_classification(
                api_name,
                function_name,
                subdomain,
                context_count,
                response_count,
                context,
                response,
            )
            return subdomain
        else:
            return cache_result

    def classify_class_and_function(self, fullname: str) -> tuple[str, str]:
        """Classify class and function from the full name at once.

        Args:
            fullname (str): Class and function full name, like this: java.swing.JFrame::open

        Returns:
            str: domain of class
            str: subdomain of function
        """
        api_name = fullname.split("::")[0]
        domain = self.classify_API(api_name)
        function_name = fullname.split("::")[1]
        subdomain = self.classify_function(api_name, function_name, domain)
        return domain, subdomain


# Load File
def load_data(filename: str) -> dict:
    """Load JSON Dict from filename

    Args:
        filename (str): filename to load from. Assume working directory

    Returns:
        dict: json dictionary.
    """
    with open(filename) as file:
        return json.load(file)


# Ideas for improvement
# Pinecone Database - somehow having a database with GENERAL context on functions and APIs non dependent on the language this could improve
# the model and ai request without there being bottleneck to a specefic language


def main() -> None:
    """Testing Script"""

    # -----------------------
    # Removed anything in () after the main name of the labels just incase openAI forgot to put it in the response
    API_listing_file = (
        "./data/domain_labels.json"  # Dont change, specefic file needed in folder
    )
    sub_domain_listing_file = (
        "./data/subdomain_labels.json"  # Dont Change, Specefic File Needed in Folder
    )
    # -----------------------

    api_domain_listing = load_data(API_listing_file)
    sub_domain_listing = load_data(sub_domain_listing_file)

    classifier = AIClassifier(api_domain_listing, sub_domain_listing)

    fullName = "java.sql.Connection::createStatement"

    # For testing purposes we can keep these until needed since we arent calling on the main as of right now
    api_name = fullName.split("::")[0]
    domain, description, response = classifier.classify_API(api_name)
    print("DOMAIN: ", domain)
    print("DESCRIPTION: ", description)
    print("RESPONSE: ", response)
    print("\n")
    function_name = fullName.split("::")[1]
    # When calling the classify function we need the api_domain that the api is apart of. This is because we are getting a sub domain for the function.
    # For example... api_name java.sql.connection falls under the domain "Database (DB), if the function_name is createStatement the sub_domain
    # will be one of the ones under the Database (DB) domain, so it would be Quert Execution according to AI
    # THe goal here is to give the AI as much context as possible because I realized when it understood the API and api domain it made better function classifications when testing
    function_sub_domain, description, response = classifier.classify_function(
        api_name, function_name, domain
    )
    print("FUNCTION SUBDOMAIN: ", function_sub_domain)
    print("DESCRIPTION: ", description)
    print("RESPONSE: ", response)


if __name__ == "__main__":
    main()
