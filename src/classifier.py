import argparse
import concurrent.futures
import json
import os
import random
import re
import string
import sys
import emoji
import numpy as np
import pandas as pd
import requests

from openai import OpenAI
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MultiLabelBinarizer
from dotenv import load_dotenv

from .ai_taxonomy import clean_domains, clean_subdomains
from .issue_class import Issue

load_dotenv()


# Function to reformat domain labels json
def format_domain_labels(domain_labels, subdomain_labels):
    formatted_domains = {}
    # reformat domains to increase clarity for gpt model and create dictionary with only domains/subdomains (to serve as expected gpt output)
    for key, value in subdomain_labels.items():
        temp_dictionary = {}
        # iterate through each subdomain in list and add to dictionary
        for i in range(len(value)):
            subdomain, description = list(value[i].items())[0]
            subdomain = key + '-' + subdomain
            temp_dictionary[subdomain] = description
        formatted_domains[key] = temp_dictionary
    return formatted_domains



# Function to drop rare domains (those below ten)
def drop_rare_domains(df, formatted_domains):
    domains = list(formatted_domains.keys())
    positive_count = df[domains].sum()

    # Filter domains with counts less than 10 instances and append to drop list
    filtered_positive_count = positive_count[positive_count < 10]
    domains_to_drop = filtered_positive_count.index.tolist()
    subdomains_to_drop = []

    # Get rare domains
    for domain in domains_to_drop:
        subdomains = formatted_domains[domain]

        # Get domain's corresponding subdomains
        for subdomain, description in subdomains.items():
            subdomains_to_drop.append(subdomain)

    # Remove from dictionary
    for domain in domains_to_drop:
        del formatted_domains[domain]

    df.drop(columns=domains_to_drop + subdomains_to_drop, inplace=True)

    return formatted_domains, df


# Function to drop rare subdomains
def drop_rare_subdomains(df, formatted_domains):
    subdomains_df = []
    subdomains_json = []

    for domain, subdomains in formatted_domains.items():

        for subdomain, description, in subdomains.items():
            subdomains_df.append(subdomain)
            subdomains_json.append(subdomain)

    positive_count = df[subdomains_df].sum()

    # Filter domains with counts less than 100
    filtered_positive_count = positive_count[positive_count < 10]

    subdomains_to_drop = filtered_positive_count.index.tolist()

    for subdomain in subdomains_to_drop:
        for domain, subdomains in formatted_domains.items():
            if subdomain in subdomains:
                del subdomains[subdomain]

    df = df.drop(columns=subdomains_to_drop)

    return formatted_domains, df


# Function to generate synthetic data for an issue
def create_synthetic_data(issue_title, issue_description, client):
    # Define the prompt for description
    prompt_description = (
        f"Rephrase the following issue description, keeping the general idea the same but changing the wording so that it is noticeably different. "
        f"Issue description: {issue_description}. Ensure that you give ONLY the rephrased description, nothing else."
    )

    chat_completion = client.chat.completions.create(
            messages=[
            {
                "role": "user",
                "content": prompt_description,
            }
        ],
        model="gpt-4o-mini",
    )
    rephrased_description = chat_completion.choices[0].message.content

    # Define the prompt for title
    prompt_title = (
        f"Rephrase the following issue title, keeping the general idea and length the same but changing the wording so that it is noticeably different. "
        f"Issue title: {issue_title}. Ensure that you give ONLY the rephrased title, nothing else."
    )

    chat_completion = client.chat.completions.create(
            messages=[
            {
                "role": "user",
                "content": prompt_title,
            }
        ],
        model="gpt-4o-mini",
    )
    rephrased_title = chat_completion.choices[0].message.content

    return rephrased_description, rephrased_title


# Function to create dataframe for domain
def create_domain_df(domain, cntr, temp_df, average_samples, client):
    # Setup
    synthetic_data = []
    synthetic_data_columns = list(temp_df.columns)

    # Create df with positive instances and get samples needed to reach average
    positive_df = temp_df[temp_df[domain] == 1]
    samples_needed = int(average_samples / len(positive_df))
    total_samples = len(positive_df)

    # Create synthetic instances for each instance
    for index, row in positive_df.iterrows():
        curr_description = row['issue description']
        curr_title = row['issue text']
        if total_samples >= average_samples:
            break

        # Create number of samples needed for each isntance to reach average
        for i in range(0, samples_needed):
            curr_row = list(row)
            #curr_description, curr_title = 'test_title', 'test_text'
            curr_description, curr_title = create_synthetic_data(curr_description, curr_title, client)
            curr_row[4] = curr_title
            curr_row[5] = curr_description
            curr_row[0] = cntr
            synthetic_data.append(curr_row)
            cntr += 1
            total_samples += 1

    # Join synthetic and original instances
    synthetic_df = pd.DataFrame(columns=synthetic_data_columns, data=synthetic_data)
    joined_df = pd.concat([positive_df, synthetic_df], ignore_index=True)
    negative_df = temp_df[temp_df[domain] == 0]

    # Join positive data with negative instances
    negative_df_len = len(joined_df)
    negative_df = negative_df.sample(n=negative_df_len, random_state=42)
    temp_df = pd.concat([negative_df, joined_df], ignore_index=True)

    return temp_df, cntr


# Function to populate dataframe dictionary
def populate_dataframe_dictionary(formatted_domains, df, client):
    # Setup variables
    dataframe_dictionary = {}
    domains_list = list(formatted_domains.keys())

    cntr = df['Index'].max() + 1
    average_samples = df[domains_list].sum().mean()
    majority_class_sample_size = 500

    for domain in domains_list:

        columns_to_keep = [domain]
        # Drop all columns past index 17, except for the ones in `columns_to_keep`
        temp_df = pd.concat([df.iloc[:, :17], df[columns_to_keep]], axis=1)

        # Get count of positive and negative instances
        positive_count = len(temp_df[temp_df[domain] > 0])
        negative_count = len(temp_df[temp_df[domain] <= 0])

        if positive_count < average_samples:
            print(f"Creating synthetic data for domain: {domain}...")
            temp, cntr = create_domain_df(domain, cntr, temp_df, average_samples, client)
            # Store the balanced dataframe
            dataframe_dictionary[domain] = {'df': temp}

        elif positive_count > negative_count:
            # Majority class is positive
            # Get all negative instances (values <= 0)
            negative_df = temp_df[temp_df[domain] <= 0]
            if len(negative_df) > 500:
                num_to_sample = 500
            else:
                num_to_sample = len(negative_df)

            # Sample 500 positive instances
            positive_df = temp_df[temp_df[domain] > 0].sample(n=num_to_sample, random_state=42)

            # If the number of negative instances is less than 500, sample them all
            if len(negative_df) >= majority_class_sample_size:
                negative_df = negative_df.sample(n=num_to_sample, random_state=42)

            # Concatenate the sampled positive instances with the negative instances
            temp = pd.concat([negative_df, positive_df])

            # Store the balanced dataframe
            dataframe_dictionary[domain] = {'df': temp}

        else:
            # Majority class is negative
            # Get all positive instances (values > 0)
            positive_df = temp_df[temp_df[domain] > 0]

            if len(positive_df) > 500:
                num_to_sample = 500
            else:
                num_to_sample = len(positive_df)

            # Sample 500 negative instances
            negative_df = temp_df[temp_df[domain] <= 0].sample(n=num_to_sample, random_state=42)

            # If the number of positive instances is less than 500, sample them all
            if len(positive_df) >= majority_class_sample_size:
                positive_df = positive_df.sample(n=num_to_sample, random_state=42)

            # Concatenate the sampled positive instances with the negative instances
            temp = pd.concat([negative_df, positive_df])
            # Store the balanced dataframe
            dataframe_dictionary[domain] = {'df': temp}

    return dataframe_dictionary


# Function to get every possible combination of subdomains
def get_combos(subdomains):
    # Generate all combinations
    combinations_list = []
    for r in range(1, len(subdomains) + 1):
        combinations_list.extend(itertools.combinations(subdomains, r))

    # Convert to list of lists
    result = [list(combo) for combo in combinations_list]

    return result


# Function to balance subdomain data
def balance_data(combos, count_dictionary, prompt_cntr, subdomains, subdomain_descriptions, average, client):
    finished = False
    target = average
    cntr = 0
    curr_combo = combos[0]
    data = []

    # Continue generating synthetic data until each subdomain has 100 instances
    while finished == False:

        # Create synthetic instance and drop combos including subdomains with 100 instances
        title, text = create_synthetic_instance(count_dictionary, curr_combo, subdomains, subdomain_descriptions, client)
        combos = drop_combos(count_dictionary, combos, target)

        # Finish when each subdomain has 100 instances
        if check_counts(count_dictionary, target):
            finished = True

        # Update variables
        else:
            encoded_labels = get_labels(subdomains, curr_combo)  # Get encoded labels based on current combo
            curr_combo = combos[(cntr + 1) % len(combos)]
            cntr += 1
            prompt_cntr += 1

            data.append([prompt_cntr, title, text] + encoded_labels)  # Add to data, appending encoded labels

    return prompt_cntr, data


# Function to check if counts are at 100
def check_counts(count_dictionary, target):
    for domain, count in count_dictionary.items():
        if count < target:
            return False

    return True


# Function to drop combos with subdomains that have >= 100 instances
def drop_combos(count_dictionary, combos, target):
    combos_to_remove = []
    temp = []

    # iterate through count dictionary
    for domain, count in count_dictionary.items():

        # If count for current subdomain > target, find each combo containing that subdomains
        if count >= target:
            for index, combo in enumerate(combos):
                if domain in combo:
                    combos_to_remove.append(combo)

    # Populate temp with only valid combos
    for combo in combos:
        if combo not in combos_to_remove:
            temp.append(combo)
    return temp


# Function to encode labels
def get_labels(subdomains, combo):
    encoded_labels = []

    # Create encoded labels based on current combo
    for subdomain in subdomains:
        if subdomain in combo:
            encoded_labels.append(1)
        else:
            encoded_labels.append(0)

    return encoded_labels


# Function to create synthetic instance of data
def create_synthetic_instance(count_dictionary, combo, subdomains, subdomain_descriptions, client):
    # Select random issue type
    issue_types = ['Feature Addition', 'Feature Improvement', 'Bug Fix', 'Performance Optimization']
    type = random.choice(issue_types)  # Get a random value

    # Update count dictionary
    for domain in combo:
        count_dictionary[domain] += 1

    title = 'title'
    text = 'text'

    subdomains = str(subdomain_descriptions)

    # Create prompt based on subdomains and issue type
    prompt = (
    f"Given the following labels and their descriptions: {subdomains}, generate a synthetic GitHub Issue that corresponds to all the listed labels. "
    f"Your response should include only the issue title and the issue text, separated by '||'. "
    f"Do not include any labels in your output. "
    f"Example format: 'Implement Multi-Factor Authentication for User Login || We need to enhance the security of our user login process by implementing multi-factor authentication (MFA). This will require integrating an additional verification step, such as a one-time code sent via SMS or email.' "
    f"Make sure to keep the content concise and relevant to the provided labels. "
    f"NOTE: The issue type is {type}."
    )

    # Prompt GPT
    chat_completion = client.chat.completions.create(
            messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-4o-mini",
    )

    # Split into title and text, use cleaning function
    synthetic_issue = chat_completion.choices[0].message.content
    split = synthetic_issue.split('||')
    title = clean_text(split[0])
    text = clean_text(split[1])

    return title, text


def create_subdomain_df(df, subdomains, data):
    # Drop all other domains and instances
    curr_df = df.drop(columns=['Repo Name', 'PR #', 'Pull Request', 'created_at', 'closed_at', 'userlogin', 'author_name', 'most_recent_commit', 'filename', 'file_commit', 'api', 'function_name', 'api_domain', 'subdomain'])
    curr_df = pd.concat([curr_df.iloc[:, :3], curr_df[subdomains]], axis=1)

    # Keep n number of zero instances
    zero_instances = curr_df[curr_df[subdomains].eq(0).all(axis=1)]
    num_zero_instances = len(zero_instances)
    n = 100
    n_to_keep = min(n, num_zero_instances)
    zero_instances_to_keep = zero_instances.sample(n=n_to_keep, random_state=1)  # Random sample of n

    # Concatenate instances where each domain is zero with instances where any of the subdomains is 1
    curr_df = pd.concat([
        curr_df[~curr_df[subdomains].eq(0).all(axis=1)],  # Keep rows where not all are zero
        zero_instances_to_keep  # Add the kept zero instances
    ])

    # Combine synthetic df with original
    synthetic_df = pd.DataFrame(data=data, columns=curr_df.columns)
    curr_df = pd.concat([curr_df, synthetic_df])

    curr_df.reset_index(drop=True, inplace=True)

    return curr_df


def populate_subdomain_dictionary(formatted_domains, df, client):
    subdomain_dictionary = {}
    subdomains_list = []
    for domain, subdomains in formatted_domains.items():
        subdomain_dictionary[domain] = {}
        for subdomain, description in subdomains.items():
            subdomains_list.append(subdomain)

    average = df[subdomains_list].sum().mean()
    index = df['Index'].max()
    for domain, subdomains in formatted_domains.items():
        print(f"Creating df for: {domain}")
        if 'df' in subdomain_dictionary[domain]:

            print(f"df exists for domain: {domain}")

        elif domain:
            if not subdomains:
                print(f"No subdomains for domain: {domain}")
            else:
                print('---------------------------------------------------------------------------------')
                print(f"Creating synthetic data for subdomains: {domain}...")
                subdomain_descriptions = subdomains
                subdomains = list(subdomains.keys())

                count_dictionary = {}
                for subdomain in subdomains:
                    count_dictionary[subdomain] = df[subdomain].sum()

                combos = get_combos(subdomains)

                index, synthetic_data = balance_data(combos, count_dictionary, index, subdomains, subdomain_descriptions, average, client)

                subdomain_dictionary[domain]['df'] = create_subdomain_df(df, subdomains, synthetic_data)
    return subdomain_dictionary


# Function to split dataframes into testing and training sets
def split_domain_dataframes(dataframe_dictionary):
    for domain, data in dataframe_dictionary.items():
        curr_df = data['df']
        # Randomly sample 70% of the rows for the first DataFrame
        training_df = curr_df.sample(frac=0.7, random_state=1)

        # The remaining 30% of the rows for the second DataFrame
        testing_df = curr_df.drop(training_df.index)
        data['training_df'] = training_df
        data['testing_df'] = testing_df

    return dataframe_dictionary


def split_subdomain_dataframes(subdomain_dictionary):
    for domain, data in subdomain_dictionary.items():
        if 'df' not in data:
            print(f"Subdomain df not found for Domain: {domain}")
        else:
            print(f"Splitting data for domain: {domain}")
            curr_df = data['df']
             # Randomly sample 70% of the rows for the first DataFrame
            training_df = curr_df.sample(frac=0.7, random_state=1)

            # The remaining 30% of the rows for the second DataFrame
            testing_df = curr_df.drop(training_df.index)
            data['training_df'] = training_df
            data['testing_df'] = testing_df
    return subdomain_dictionary




# Function to construct messages and store in a jsonl file
def generate_domain_messages_json(domain, filepath, training_df):
    # Open the file in write mode
    with open(filepath, 'w', encoding='utf-8') as f:
        # Iterate over the rows in the DataFrame
        for index, row in training_df.iterrows():
            # Create the user message by formatting the prompt with the title and body
            user_message = (
                f"Classify a GitHub issue by indicating whether the domain [{domain}] is relevant to the issue given its title: [{row['issue text']}], "
                f"body: [{row['issue description']}], and repository [{row['Repo Name']}]. Ensure that you Provide ONLY a list of relevant subdomains from the provided list. "
                f"domain is relevant to the issue."
            )

            assistant_message = str(row[domain])

            # Construct the conversation object
            conversation_object = {
                "messages": [
                    {"role": "system", "content": "Classify GitHub issues"},
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": assistant_message}
                ]
            }

            # Write the conversation object to one line in the file
            f.write(json.dumps(conversation_object, ensure_ascii=False) + '\n')


# Function to populate dataframe_dictionary with message filepath
def generate_domain_messages(dataframe_dictionary):
    # Create messages for each domain
    for domain, data in dataframe_dictionary.items():
        filepath = "../data/Domain_Messages/" + domain.replace('/', '-') + ".jsonl"
        training_df = data['training_df']
        generate_domain_messages_json(domain, filepath, training_df)
        data['gpt_messages'] = filepath

    return dataframe_dictionary


def generate_subdomain_messages_json(subdomains, filepath, training_df):
    subdomain_list = training_df.columns[3:]
    # Open the file in write mode
    with open(filepath, 'w', encoding='utf-8') as f:
        assistant_message = ""
        # Iterate over the rows in the DataFrame
        for index, row in training_df.iterrows():
            assistant_message = []
            # Create the user message by formatting the prompt with the title and body
            user_message = (
                f"Classify a GitHub issue by indicating whether each subdomain in the list [{subdomains}] is relevant to the issue given its title: [{row['issue text']}], "
                f"and body: [{row['issue description']}]. Ensure that you provide ONLY a list of relevant subdomains and that each subdomain is in the list shown before"
            )

            for subdomain in subdomain_list:
                if row[subdomain] == 1:
                    assistant_message.append(subdomain)

            # Construct the conversation object
            conversation_object = {
                "messages": [
                    {"role": "system", "content": "Classify GitHub issues"},
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": str(assistant_message)}
                ]
            }

            # Write the conversation object to one line in the file
            f.write(json.dumps(conversation_object, ensure_ascii=False) + '\n')


def generate_subdomain_messages(subdomain_dictionary, formatted_domains):
    for domain, data in subdomain_dictionary.items():
        if 'df' not in data:
            print(f"Domain {domain} has no df")
        else:
            filepath = "../data/Subdomain_Messages/" + domain + " Subdomains.jsonl"
            subdomains = str(formatted_domains[domain])
            subdomains = subdomains.replace('{', '')
            subdomains = subdomains.replace('}', '')

            training_df = data['training_df']
            generate_subdomain_messages_json(subdomains, filepath, training_df)
            data['gpt_messages'] = filepath
    return subdomain_dictionary


# Function to fine tune a gpt model
def fine_tune_gpt_combined(file, domain, client):
    # Upload training file
    print(f"Uploading file {file.split('/')[-1]}...")
    training_file = client.files.create(
        file=open(file, 'rb'),
        purpose='fine-tune')

    # Start fine tuning job
    print('Starting fine tuning process...')
    ft_job = client.fine_tuning.jobs.create(
        training_file=training_file.id,
        model="gpt-4o-mini-2024-07-18",
        suffix=domain)

    print('Waiting for fine tune to finish...')
    # Return fine tuned model when fine tuning is finished
    tuned_model = client.fine_tuning.jobs.retrieve(ft_job.id).fine_tuned_model

    while (tuned_model == None):
        tuned_model = client.fine_tuning.jobs.retrieve(ft_job.id).fine_tuned_model

    return tuned_model


# Function to populate data_frame_dictionary with gpt models
def get_domain_models(dataframe_dictionary, client):
    for domain, data in dataframe_dictionary.items():
        if 'tuned_model' in data:
            print(f"Model already exists for domain: {domain}, {data['tuned_model']}")
        else:
            print(f"No model found for domain: {domain}, creating one now")
            filepath = data['gpt_messages']
            data['tuned_model'] = fine_tune_gpt_combined(filepath, domain, client)
    return dataframe_dictionary


# Function to populate subdomain_dictionary with gpt models
def get_subdomain_models(subdomain_dictionary, client):
    for domain, data in subdomain_dictionary.items():
        if 'df' not in data:
            print(f"Domain {domain} has no df")

        elif 'tuned_model' in data:
            print(f"Model already exists for domain: {domain}")

        else:
            if domain:
                domain_str = domain + ' Subdomains'
                print(f"No model found for domain: {domain_str}, creating one now")
                filepath = data['gpt_messages']
                data['tuned_model'] = fine_tune_gpt_combined(filepath, domain, client)
    return subdomain_dictionary


# Function to create metrics df
def create_domain_performance_df(dataframe_dictionary):
    # Data Format: [FP, TP, FN, TN]
    performance_columns = ['Domain', 'Accuracy', 'Precision (1)', 'Recall (1)', 'F1 (1)', 'Precision (0)', 'Recall (0)',
                           'F1 (0)', 'Confusion Matrix']

    performance_df = pd.DataFrame(columns=performance_columns)
    sum_list = [0, 0, 0, 0]

    for domain, data in dataframe_dictionary.items():
        if 'scores' not in data:
            print(f"Scores not found for domain {domain}, unable to calculate metrics")
        else:
            value = data['scores']
            sum_list[0] += value[0]
            sum_list[1] += value[1]
            sum_list[2] += value[2]
            sum_list[3] += value[3]

            accuracy = (value[1] + value[3]) / sum(value)
            accuracy = float("{:.2f}".format(accuracy))

            # Calculate metrics for positive cases
            positive_precision = (value[1]) / (value[1] + value[0]) if (value[1] + value[0]) > 0 else 0
            positive_precision = float("{:.2f}".format(positive_precision))

            positive_recall = (value[1]) / (value[1] + value[2]) if (value[1] + value[2]) > 0 else 0
            positive_recall = float("{:.2f}".format(positive_recall))

            positive_F1 = 2 * (positive_precision * positive_recall) / (positive_precision + positive_recall) if (
                                                                                                                             positive_precision + positive_recall) > 0 else 0
            positive_F1 = float("{:.2f}".format(positive_F1))

            # Calculate metrics for negative cases
            negative_precision = (value[3]) / (value[3] + value[2]) if (value[3] + value[2]) > 0 else 0
            negative_precision = float("{:.2f}".format(negative_precision))

            negative_recall = (value[3]) / (value[3] + value[0]) if (value[3] + value[0]) > 0 else 0
            negative_recall = float("{:.2f}".format(negative_recall))

            negative_F1 = 2 * (negative_precision * negative_recall) / (negative_precision + negative_recall) if (
                                                                                                                             negative_precision + negative_recall) > 0 else 0
            negative_F1 = float("{:.2f}".format(negative_F1))

            confusion_matrix = "0[{}  {}]\n1[{}  {}]\n   0     1".format(value[3], value[0], value[2], value[1])
            new_row = [domain, accuracy, positive_precision, positive_recall, positive_F1, negative_precision,
                       negative_recall, negative_F1, confusion_matrix]
            performance_df.loc[len(performance_df)] = new_row

    return performance_df, sum_list


# Function to populate scores (TP, FP TN, FN)
def populate_domain_scores(scores, testing_df, domain, responses):
    for index, row in testing_df.iterrows():
        if row['Index'] in responses:
            try:
                curr_response = responses[row['Index']]
                pred_y = int(curr_response['response'])
                true_y = int(row[domain])
                for domain in list(testing_df.columns[17:]):

                    # false positive
                    if true_y == 0 and pred_y == 1:
                        scores[domain][0] += 1

                    # true positive
                    elif true_y == 1 and pred_y == 1:
                        scores[domain][1] += 1

                    # false negative
                    elif true_y == 1 and pred_y == 0:
                        scores[domain][2] += 1

                    # true negative
                    elif true_y == 0 and pred_y == 0:
                        scores[domain][3] += 1
            except ValueError:
                # Handle the case where the string is not properly formatted
                print("PR #" + str(row["PR #"]) + " response not in json format")
        else:
            n = 0
            # print("PR #" + str(row['PR #']) + " Issue not in response json")
    return scores[domain]


# Function to get scores for each domain
def get_domain_scores(dataframe_dictionary):
    for domain, data in dataframe_dictionary.items():
        if 'predictions' not in data:
            print(f"Predictions not found for domain: {domain}")
        else:
            testing_df = data['testing_df']

            domains = list(testing_df.columns[17:])

            scores = {}

            for each in domains:
                scores[each] = [0, 0, 0, 0]

            scores = populate_domain_scores(scores, testing_df, domain, data['predictions'])
            data['scores'] = scores
    return dataframe_dictionary


# Function to predict for instances in testing set
def predict_for_domain(testing_df, tuned_model, openai_key, domain):
    all_responses = {}
    counter = 0
    for index, row in testing_df.iterrows():
        temp_dic = {}
        subdomains_response = []
        if counter <= len(testing_df):
            # create user and system messages
            user_message = (
                f"Classify a GitHub issue by indicating whether the following domain: [{domain}] is relevant to the issue given its title: [{row['issue text']}], "
                f"body: [{row['issue description']}], and repository [{row['Repo Name']}]. Ensure that you provide ONLY a 0 (negative) or a 1 (positive) to determine whether the domains fits"
                f"Example: 0")
            system_message = "Refer to these domains" + ""
            print(user_message)

            valid_response = 0
            query_count = 0

            # query fine tuned model
            while valid_response == 0:
                domain_response = query_gpt(user_message, tuned_model, openai_key)
                if domain_response == '1' or domain_response == '0':
                    valid_response = 1
                else:
                    if query_count == 2:
                        print('failed to get proper response after three attempts')
                        break
                    print(f"Invalid response: {domain_response} requerying...")
                    query_count += 1

            if valid_response == 1:
                temp_dic['response'] = domain_response
                all_responses[row['Index']] = temp_dic

            counter += 1

    return all_responses


# Function to generate metrics csv
def produce_domain_csv(dataframe_dictionary, openai_key):
    for domain, data in dataframe_dictionary.items():
        if 'tuned_model' in data:

            print(f"predictions not found for domain: {domain}, predicting now...")
            tuned_model = data['tuned_model']
            testing_df = data['testing_df']
            data['predictions'] = predict_for_domain(testing_df, tuned_model, openai_key, domain)

        else:
            print(f"Tuned model not found for domain: {domain}, can't generate predictions")
    print(dataframe_dictionary['Application Performance Manager']['predictions'])

    dataframe_dictionary = get_domain_scores(dataframe_dictionary)
    performance_df, sum_list = create_domain_performance_df(dataframe_dictionary)
    performance_df.to_csv('../data/Model_Metrics/domain_performance.csv', index=False)


def predict_for_subdomains(testing_df, tuned_model, subdomains, openai_key):
    all_responses = {}
    counter = 0
    for index, row in testing_df.iterrows():
        temp_dic = {}
        if counter <= len(testing_df):
            # create user and system messages
            user_message = (
                f"Classify a GitHub issue by indicating whether each subdomain in the list [{subdomains}] is relevant to the issue given its title: [{row['issue text']}], "
                f"and body: [{row['issue description']}]. Ensure that you provide ONLY a list of relevant subdomains and that each subdomain is in the list shown before. If none apply to the issue, respond with an empty list (ie [])."
                f" Example: [Subdomain1, Subdomain2]")
            domain_response = query_gpt(user_message, tuned_model, openai_key)

            temp_dic['response'] = domain_response
            all_responses[row['Index']] = temp_dic
            counter += 1

    return all_responses


def populate_subdomain_scores(scores, testing_df, responses):
    columns = testing_df.columns[3:]
    for index, row in testing_df.iterrows():
        if row['Index'] in responses:
            try:
                curr_response = responses[row['Index']]
                domains = ast.literal_eval(curr_response['response'])
                curr_response = domains
                for domain in list(columns):
                    if domain in curr_response:
                        pred_y = 1
                        true_y = row[domain]
                    else:
                        pred_y = 0
                        true_y = row[domain]

                    # false positive
                    if true_y == 0 and pred_y == 1:
                        scores[domain][0] += 1

                    # true positive
                    elif true_y == 1 and pred_y == 1:
                        scores[domain][1] += 1

                    # false negative
                    elif true_y == 1 and pred_y == 0:
                        scores[domain][2] += 1

                    # true negative
                    elif true_y == 0 and pred_y == 0:
                        scores[domain][3] += 1
            except ValueError:
                # Handle the case where the string is not properly formatted
                print("Index #" + str(row["Index"]) + " response not in json format")
        else:
            print("Index #" + str(row['Index']) + " Issue not in response json")

    return scores


def get_subdomain_scores(subdomain_dictionary):
    for domain, data in subdomain_dictionary.items():
        if 'predictions' not in data:
            print(f"No predictions for domain: {domain}, skipping...")

        else:
            print(domain)
            testing_df = data['testing_df']
            columns = list(testing_df.columns[3:])
            scores = {}
            for each in columns:
                scores[each] = [0, 0, 0, 0]

            scores = populate_subdomain_scores(scores, testing_df, data['predictions'])
            data['scores'] = scores

    return subdomain_dictionary


def create_subdomain_performance_df(subdomain_data):
    # Data Format: [FP, TP, FN, TN]
    performance_columns = ['Domain', 'Accuracy', 'Precision (1)', 'Recall (1)', 'F1 (1)', 'Precision (0)', 'Recall (0)',
                           'F1 (0)', 'Confusion Matrix']

    performance_df = pd.DataFrame(columns=performance_columns)
    sum_list = [0, 0, 0, 0]

    for domain, data in subdomain_data.items():
        if 'scores' not in data:
            print('here')

        else:
            for subdomain, value in data['scores'].items():
                print(f"Domain: {subdomain}")
                sum_list[0] += value[0]
                sum_list[1] += value[1]
                sum_list[2] += value[2]
                sum_list[3] += value[3]

                accuracy = (value[1] + value[3]) / sum(value)
                accuracy = float("{:.2f}".format(accuracy))

                # Calculate metrics for positive cases
                positive_precision = (value[1]) / (value[1] + value[0]) if (value[1] + value[0]) > 0 else 0
                positive_precision = float("{:.2f}".format(positive_precision))

                positive_recall = (value[1]) / (value[1] + value[2]) if (value[1] + value[2]) > 0 else 0
                positive_recall = float("{:.2f}".format(positive_recall))

                positive_F1 = 2 * (positive_precision * positive_recall) / (positive_precision + positive_recall) if (
                                                                                                                                 positive_precision + positive_recall) > 0 else 0
                positive_F1 = float("{:.2f}".format(positive_F1))

                # Calculate metrics for negative cases
                negative_precision = (value[3]) / (value[3] + value[2]) if (value[3] + value[2]) > 0 else 0
                negative_precision = float("{:.2f}".format(negative_precision))

                negative_recall = (value[3]) / (value[3] + value[0]) if (value[3] + value[0]) > 0 else 0
                negative_recall = float("{:.2f}".format(negative_recall))

                negative_F1 = 2 * (negative_precision * negative_recall) / (negative_precision + negative_recall) if (
                                                                                                                                 negative_precision + negative_recall) > 0 else 0
                negative_F1 = float("{:.2f}".format(negative_F1))

                confusion_matrix = "0[{}  {}]\n1[{}  {}]\n   0     1".format(value[3], value[0], value[2], value[1])
                new_row = [subdomain, accuracy, positive_precision, positive_recall, positive_F1, negative_precision,
                           negative_recall, negative_F1, confusion_matrix]
                performance_df.loc[len(performance_df)] = new_row

    return performance_df, sum_list


def produce_subdomain_csv(subdomain_dictionary, formatted_domains, openai_key):
    for domain, data in subdomain_dictionary.items():
        if 'tuned_model' in data:
            print(f"predictions not found for {domain} subdomains:, predicting now...")
            subdomains = str(formatted_domains[domain])
            subdomains = subdomains.replace('{', '')
            subdomains = subdomains.replace('}', '')

            tuned_model = data['tuned_model']
            testing_df = data['testing_df']
            data['predictions'] = predict_for_subdomains(testing_df, tuned_model, subdomains, openai_key)
        else:
            print(f"Tuned model not found for domain: {domain}, can't generate predictions")
    print(subdomain_dictionary['Application Performance Manager']['predictions'])
    subdomain_dictionary = get_subdomain_scores(subdomain_dictionary)

    performance_df, sum_list = create_subdomain_performance_df(subdomain_dictionary)
    performance_df.to_csv('Model_Metrics/subdomain_performance.csv', index=False) 


def get_model_json(domain_dictionary, subdomain_dictionary):
    gpt_models = {}
    curr_domain_model = ''
    curr_subdomain_model = ''
    for domain, data in domain_dictionary.items():
        if 'tuned_model' not in data:
            curr_domain_model = 'None'
        else:
            curr_domain_model = data['tuned_model']
        if 'tuned_model' not in subdomain_dictionary[domain]:
            curr_subdomain_model = 'None'
        else:
            curr_subdomain_model = subdomain_dictionary[domain]['tuned_model']
        gpt_models[domain] = {'domain_model' : curr_domain_model, 'subdomain_model' : curr_subdomain_model}

    return gpt_models


# Function to get labels for issue.
# 'gpt_models' is a dictionary containing the contents of the file 'data/gpt_models'
# 'domain_labels' is a dictionary containing the contents of the file data/formatted_domain_labels
# The function returns a dictionary with the predictions for each domain and their subdomains
def label_issue_binary_classification(
    issue: Issue, gpt_models, domain_labels, openai_key, max_domains=None
):
    """Function to get labels for issue.

    Args:
        issue_title (Issue): Issue to classify
        gpt_models (dict[str, dict[str, Any]]): Dictionary of models by domain.
        domain_labels (dict[str, dict[str, Any]]): Domain label dictionary from `formatted_domain_labels.json`

    Returns:
        dict[str, dict[str, Any]]: Responses from the domain label dictionary.
    """
    print("TITLE: ", issue.title)
    response_dic = {}
    counter = 0
    for domain, data in domain_labels.items():
        if max_domains is not None and counter > max_domains:
            break  # skip after finding max REAL domains.

        print(f"Getting predictions for domain: {domain}")
        # Load domain and subdomain models
        domain_model = gpt_models[domain]["domain_model"]
        subdomain_model = gpt_models[domain]["subdomain_model"]

        # Create prompt for domain
        domain_prompt = (
            f"Classify a GitHub issue by indicating whether the following domain: [{domain}:{data['domain_description']}] is relevant to the issue given its title: [{issue.title}], "
            f"body: [{issue.body}']. Ensure that you provide ONLY a 0 (not relevant) or a 1 (relevant) to determine whether the domains fits."
            f" Example response: 0"
        )

        domain_response = query_gpt(
            domain_prompt, domain_model, openai_key
        )  # Prompt GPT model

        try:
            domain_response = int(clean_text(domain_response))
        except:
            domain_response = 0

        # check if domain_response is 1 (domain applies to issue)
        if domain_response == 1:
            counter += 1
            print(f"\tGetting subdomain predictions for domain: {domain}")

            response_clean = set()
            fail_safe = 0
            while len(response_clean) == 0:
                recv = get_subdomain_bin_class(
                    domain, data, issue, subdomain_model, openai_key
                )
                for i in recv:
                    response_clean.add(i)
                fail_safe += 1
                if fail_safe > 5:
                    break

            subdomain_response = list(response_clean)

        else:
            subdomain_response = []
            continue

        response_dic[domain] = {
            "domain_response": domain_response,
            "subdomain_response": subdomain_response,
        }

    print(response_dic)
    return response_dic


# ------------------------------------------ #


def get_subdomain_bin_class(domain, data, issue, subdomain_model, openai_key):
    subdomain_dict = {}
    for subdomain_key, subdomain_description in data.items():
        if subdomain_key == "domain_description":
            continue
        subdomain_dict[subdomain_key] = subdomain_description

    subdomain_string = json.dumps(
        subdomain_dict, indent=2
    )  # You might still want to convert it to ensure it's readable
    # subdomain_prompt = (
    #     f"Classify a GitHub issue by indicating whether each subdomain in the list [{subdomain_string}] is relevant to the issue given its title: [{issue.title}], "
    #     f"and body: [{issue.body}]. Ensure that you provide ONLY a list of relevant subdomains and that each subdomain is in the list shown before"
    # )

    subdomain_prompt = (
        f"Classify a GitHub issue by indicating TWO domains that are relevant to the issue based on its title: [{issue.title}] "
        f"and body: [{issue.body}]. \n"
        f"Prioritize positive precision by selecting a domain only when VERY CERTAIN it is relevant to the issue text.  Return as a JSON list with each key being the domain and value being a brief description of this domain. Refer to ONLY THESE domains when classifying: {subdomain_string}."
        f'\n\nImportant: Ensure that you provide the name of TWO domains in JSON LIST FORMAT. TWO DOMAINS: ie ["Application-Integration", "Cloud-Scalability"]'
    )
    subdomain_response = query_gpt(
        subdomain_prompt, subdomain_model, openai_key
    )  # Prompt GPT model

    subdomain_response = (
        subdomain_response.replace("'", '"').replace("{", "[").replace("}", "]")
    )
    response_clean = []
    malformed = False
    basic_response = []
    try:
        response = json.loads(subdomain_response)
    except:
        # print(f"Malformed JSON: {subdomain_response}")
        basic_response = subdomain_response.split('",')
        malformed = True
        # pass each string.

    if malformed:
        for domain in basic_response:
            if len(domain) < 5:
                continue
            domain = clean_domains(
                domain, "", subdomain_dict, formatted=True
            )  # from AI Taxonomy
            response_clean.append(domain)
    else:
        for item in response:
            domain = clean_domains(
                item, "", subdomain_dict, formatted=True
            )  # from AI Taxonomy
            response_clean.append(domain)
    return response_clean


def clean_text(text):
    cleaned_count = 0
    original_count = 0
    if not isinstance(text, str):
        original_count += 1
        return text

    # Remove double quotation marks
    text = text.replace('"', "")

    # Remove text starting with "DevTools" and ending with "(automated)"
    text = re.sub(r"DevTools.*?\(automated\)", "", text)

    # Lowercasing should be one of the first steps to ensure uniformity
    text = text.lower()

    # Remove emojis
    text = emoji.demojize(text)

    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", "", text)

    # Remove HTML tags
    text = re.sub(r"<.*?>", "", text)

    # Remove special characters and punctuation
    text = re.sub(f"[{re.escape(string.punctuation)}]", "", text)

    # Remove '#' characters
    text = text.replace("#", "")

    # Remove consecutive whitespaces and replace with a single space
    text = re.sub(r"\s+", " ", text)

    # Split the text into words
    words = text.split()

    # Remove words that are over 20 characters
    words = [word for word in words if len(word) <= 20]

    # Join the remaining words back into cleaned text
    cleaned_text = " ".join(words)

    cleaned_count += 1
    return cleaned_text


def sort_dict_by_values(d, reverse=True):
    # Sort the dictionary by its values
    sorted_dict = dict(sorted(d.items(), key=lambda item: item[1], reverse=reverse))
    return sorted_dict


def get_top_domains(n, d, df):
    # Get top n domains, drop the rest
    counter = 1
    columns_to_drop = []
    for key, value in d.items():
        if counter > n:
            columns_to_drop.append(key)
        counter += 1
    df = df.drop(columns=columns_to_drop)
    return df


def filter_domains(df):
    domains = df.columns[16:]
    columns_to_drop = []
    occurrence_dictionary = {}
    for domain in domains:
        # get occurrence rate of each domain
        column_values = df[domain].tolist()
        occurrence = column_values.count(1)
        lower_bound = int(len(df) * 0.40)
        upper_bound = int(len(df) * 0.80)

        # drop those that are outside of the bounds
        if occurrence < lower_bound or occurrence > upper_bound:
            columns_to_drop.append(domain)
        else:
            occurrence_dictionary[domain] = occurrence

    df = df.drop(columns=columns_to_drop)

    # sort occurence dictionary to determine top domains and return top 15
    occurrence_dictionary = sort_dict_by_values(occurrence_dictionary)
    num_of_domains = 15
    return get_top_domains(num_of_domains, occurrence_dictionary, df)


def generate_system_message(domain_dictionary, subdomain_dictionary, df):
    formatted_domains = {}
    formatted_subdomains = {}

    for item in domain_dictionary["Items"]:
        domain = tuple(item.keys())[0]
        domain_description = item[domain]

        formatted_domains[domain] = domain_description

        if domain in subdomain_dictionary:
            # formatted_subdomains[domain] = subdomain_dictionary[domain]
            # Create a subdomain entry for each subdomain under this domain
            subdomain_list = subdomain_dictionary[domain]
            for subdomain_info in subdomain_list:
                subdomain = tuple(subdomain_info.keys())[0]
                subdomain_description = subdomain_info[subdomain]

                formatted_subdomains[f"{domain}-{subdomain}"] = subdomain_description

    # The system_message could be adjusted to include just domain names if detailed info is not needed

    return formatted_domains, formatted_subdomains


def generate_gpt_messages(domain_message, subdomain_message, df, out_jsonl):
    # Open the file in write mode
    assistant_message = {}
    with open(out_jsonl, "w", encoding="utf-8") as f:
        # Iterate over the rows in the DataFrame
        for index, row in df.iterrows():
            # Create the user message by formatting the prompt with the title and body
            user_message = (
                f"Classify a GitHub issue by indicating whether each domain and subdomain is relevant to the issue based on its title: [{row['issue text']}] "
                f"and body: [{row['issue description']}]. Ensure that every domain/subdomain is accounted for, and its relevance is indicated with a 1 (relevant) or a 0 (not relevant)."
            )

            # logic to update assistant message with values in df
            for column in df.columns:
                if column in subdomain_message:
                    if row[column] > 0:
                        assistant_message[column] = 1
                    else:
                        assistant_message[column] = 0
            # Construct the conversation object
            combined = domain_message | subdomain_message
            conversation_object = {
                "messages": [
                    {
                        "role": "system",
                        "content": f"Refer to these domains and subdomains {combined}"
                        + " for definitions when classifying",
                    },
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": str(assistant_message)},
                ]
            }

            # Write the conversation object to one line in the file
            f.write(json.dumps(conversation_object, ensure_ascii=False) + "\n")


def generate_gpt_message_one_issue(system_message, gpt_output, issue: Issue):
    raise NotImplementedError  # Must be fixed!
    # Open the file in write mode

    # Create the user message by formatting the prompt with the title and body
    user_message = (
        f"Classify a GitHub issue by indicating whether each domain and subdomain is relevant to the issue based on its title: [{issue.title}] "
        f"and body: [{issue.body}]. Ensure that every domain/subdomain is accounted for, and its relevance is indicated with a 1 (relevant) or a 0 (not relevant)."
    )

    # logic to update assistant message with values in df
    for column in df.columns:
        if column in gpt_output:
            if row[column] > 0:
                assistant_message[column] = 1
            else:
                assistant_message[column] = 0

    # Construct the conversation object
    conversation_object = {
        "messages": [
            {
                "role": "system",
                "content": "Refer to these domains and subdomains when classifying "
                + system_message,
            },
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": str(assistant_message)},
        ]
    }

    # Write the conversation object to one line in the file
    f.write(json.dumps(conversation_object, ensure_ascii=False) + "\n")


def fine_tune_gpt(output_jsonl):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    # uploading a training file
    domain_classifier_training_file = client.files.create(
        file=open(output_jsonl, "rb"), purpose="fine-tune"
    )
    print("Beginning fine tuning process")
    # creating a fine-tuned model
    ft_job_dc = client.fine_tuning.jobs.create(
        training_file=domain_classifier_training_file.id,
        model="gpt-4o-mini",
        suffix="issue_classifier",
    )

    while True:
        response = client.fine_tuning.jobs.retrieve(ft_job_dc.id)
        if response.status == "succeeded":
            # Retrieving the state of a fine-tune
            issue_classifier = client.fine_tuning.jobs.retrieve(
                ft_job_dc.id
            ).fine_tuned_model
            return issue_classifier
        if response.status == "failed":
            print("process failed")
            return


# copy / rename of get_open_issues for imports
def git_helper_get_open_issues(owner, repo, access_token) -> list[Issue]:
    return get_open_issues(owner, repo, access_token)


def git_helper_get_issues(owner, repo, access_token, open_issues=True) -> list[Issue]:
    return get_issues(owner, repo, access_token, open_issues)


def get_issues(owner, repo, access_token, open_issues=True, max_count=None):
    data = []
    # GitHub API URL for fetching issues
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"

    # Headers for authentication
    if access_token is not None:
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }
    else:
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }

    if max_count is None:
        page_q = 100
    else:
        page_q = 20

    if open_issues:
        # Parameters to fetch only open issues
        params = {
            "state": "open",
            "per_page": page_q,  # Number of issues per page (maximum is 100)
            "page": 1,  # Page number to start fetching from
        }
    else:
        params = {
            "state": "closed",
            "per_page": page_q,  # Number of issues per page (maximum is 100)
            "page": 1,  # Page number to start fetching from
        }

    issues = []
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break

        issues_page = response.json()
        if not issues_page:
            break

        issues.extend(issues_page)
        if max_count is not None and max_count // page_q < params["page"]:
            break  # stop! reached max.
        params["page"] += 1

    # Add extracted issues to dataframe
    for i in issues:
        if i["body"] is None:
            i["body"] = ""
        data.append(Issue(i["number"], i["title"], i["body"]))
    print(f"Total issues fetched: {len(issues)}")

    return data


def get_open_issues(owner, repo, access_token, max_count=None) -> list[Issue]:
    return get_issues(owner, repo, access_token, max_count=max_count)


def get_open_issues_without_token(owner: str, repo: str, max_count=None) -> list[Issue]:
    return get_issues(owner, repo, None, max_count=max_count)


def get_issues_without_token(
    owner: str, repo: str, open_issues=True, max_count=None
) -> list[Issue]:
    return get_issues(owner, repo, None, open_issues=open_issues, max_count=max_count)


def query_gpt(prompt, model, openai_key, max_retries=5):
    """Function to query gpt model, parameters are prompt and model

    Args:
        prompt (str): Prompt text
        model (Any): Pretrained model to use
    """
    client = OpenAI(api_key=openai_key)
    attempt = 0
    # attempt to query model
    while attempt < max_retries:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                client.chat.completions.create,
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            try:
                response = future.result()
                return response.choices[0].message.content
            except Exception as e:
                print(f"Attempt {attempt + 1}/{max_retries} - An error occurred: {e}")
            finally:
                attempt += 1

    print("Failed to get a response after several retries.")
    return None


def get_gpt_responses(open_issue_df, issue_classifier, domains_string, openai_key):
    raise NotImplementedError  # Use get_gpt_response_one_issue() instead


def label_issue_tiered_classification(issue, model, domains, subdomains, openai_key):
    return get_gpt_response_one_issue(issue, model, domains, subdomains, openai_key)


def get_gpt_response_one_issue(issue, model, domains, subdomains, openai_key):
    # create user and system messages
    combined = domains | subdomains

    # print("Initial Domains: ", list(domains.keys()))
    text = json.dumps(
        domains, indent=2
    )  # You might still want to convert it to ensure it's readable

    user_message = (
        f"Classify a GitHub issue by indicating up to THREE domains that are relevant to the issue based on its title: [{issue.title}] "
        f"and body: [{issue.body}]. \n"
        f"Prioritize positive precision by selecting a domain only when VERY CERTAIN it is relevant to the issue text. Return as a JSON list with each key being the domain and value being a brief description of this domain. Refer to ONLY THESE domains and their descriptions when classifying: {text}."
        f'\n\nImportant: Ensure that you provide the name and description of THREE domains in JSON LIST FORMAT. ie [{{"Integration" : "Description"}}, {{"Cloud": "Description"}},  {{"Computer Graphics": "Description"}}]'
    )

    # query fine tuned model
    response = query_gpt(user_message, model, openai_key)

    # Clean response and match to domains
    response_clean = []
    malformed = False
    basic_response = []
    try:
        response = json.loads(response)
    except:
        # print(f"Malformed JSON: {response}")
        basic_response = response.split('"}')
        malformed = True
        # pass each string.

    if malformed:
        for domain in basic_response:
            if len(domain) < 5:
                continue
            domain = clean_domains(
                domain, "", domains, formatted=True
            )  # from AI Taxonomy
            response_clean.append(domain)
    else:
        for item in response:
            dname = list(item.keys())[0]
            desc = item[dname]
            domain = clean_domains(
                dname, desc, domains, formatted=True
            )  # from AI Taxonomy
            response_clean.append(domain)

    filtered_subdomains = {}
    for response_domain in response_clean:
        for subdomain in subdomains:
            if subdomain.find(response_domain) != -1:
                filtered_subdomains[subdomain] = subdomains[subdomain]

    # print("Filter: ", list(filtered_subdomains.keys()))
    text = json.dumps(
        filtered_subdomains, indent=2
    )  # You might still want to convert it to ensure it's readable

    user_message = (
        f"Classify a GitHub issue by indicating up to THREE domains that are relevant to the issue based on its title: [{issue.title}] "
        f"and body: [{issue.body}]. \n"
        f"Prioritize positive precision by selecting a domain only when VERY CERTAIN it is relevant to the issue text.  Return as a JSON list with each key being the domain and value being a brief description of this domain. Refer to ONLY THESE domains when classifying: {text}."
        f'\n\nImportant: Ensure that you provide the name and description of THREE domains in JSON LIST FORMAT. ie [{{"Application-Integration" : "Description"}}, {{"Cloud-Scalability": "Description"}},  {{"Computer Graphics-3D Rendering": "Description"}}]'
    )

    response = query_gpt(user_message, model, openai_key)

    # Clean response and match to domains
    response_clean = []
    malformed = False
    basic_response = []
    try:
        response = json.loads(response)
    except:
        basic_response = response.split('"}')
        malformed = True
        # pass each string.

    if malformed:
        for domain in basic_response:
            if len(domain) < 5:
                continue
            domain = clean_subdomains(domain, "", filtered_subdomains)
            # from AI Taxonomy
            response_clean.append(domain)
    else:
        for item in response:
            dname = list(item.keys())[0]
            desc = item[dname]
            domain = clean_subdomains(dname, desc, filtered_subdomains)
            # from AI Taxonomy
            response_clean.append(domain)

    return response_clean


def responses_to_csv(gpt_responses):
    columns = ["Issue #", "Predictions"]

    prediction_data = []

    for key, value in gpt_responses.items():
        prediction_data.append([key, value])

    gpt_predictions = pd.DataFrame(columns=columns, data=prediction_data)

    return gpt_predictions


# Random Forest Functions
def extract_text_features(data):
    X_text = data[["issue text", "issue description"]]
    X_text["combined_text"] = X_text["issue text"] + " " + X_text["issue description"]
    tfidf = TfidfVectorizer(max_features=1000)
    X_text_features = tfidf.fit_transform(X_text["combined_text"]).toarray()
    return X_text_features, tfidf


def transform_labels(data):
    y = data.drop(columns=["issue text", "issue description"])
    y = y.apply(lambda x: x.index[x == 1].tolist(), axis=1)
    mlb = MultiLabelBinarizer()
    y_transformed = mlb.fit_transform(y)
    y_df = pd.DataFrame(y_transformed, columns=mlb.classes_)
    return y_df, mlb


def create_combined_features(x_text_features):
    X_combined = pd.DataFrame(
        x_text_features, columns=list(range(x_text_features.shape[1]))
    )
    return X_combined


def perform_mlsmote(X, y, n_sample):

    def nearest_neighbour(X):
        nbs = NearestNeighbors(
            n_neighbors=3, metric="euclidean", algorithm="kd_tree"
        ).fit(X)
        _, indices = nbs.kneighbors(X)
        return indices

    # Calculate class distribution
    class_distribution = y.sum(axis=0)
    max_class_count = class_distribution.max()

    # Determine the number of samples needed for each class
    samples_needed = (max_class_count - class_distribution).astype(int)

    indices2 = nearest_neighbour(X.values)
    n = len(indices2)
    new_X = []
    target = []

    for class_idx, samples in samples_needed.items():
        if samples > 0:
            for _ in range(samples):
                reference = random.randint(0, n - 1)
                neighbour = random.choice(indices2[reference, 1:])
                all_point = indices2[reference]
                nn_df = y[y.index.isin(all_point)]
                ser = nn_df.sum(axis=0, skipna=True)
                new_target = np.array([1 if val > 2 else 0 for val in ser])
                ratio = random.random()
                gap = X.loc[reference, :] - X.loc[neighbour, :]
                new_sample = np.array(X.loc[reference, :] + ratio * gap)
                new_X.append(new_sample)
                target.append(new_target)

    new_X = pd.DataFrame(new_X, columns=X.columns)
    target = pd.DataFrame(target, columns=y.columns)

    # Append the new samples to the original data
    X_combined = pd.concat([X, new_X], axis=0)
    y_combined = pd.concat([y, target], axis=0)

    return X_combined, y_combined


def train_random_forest(x_train, y_train):
    param_grid = {
        "estimator__n_estimators": [200],
        "estimator__max_depth": [20],
        "estimator__min_samples_split": [10],
        "estimator__min_samples_leaf": [1],
        "estimator__max_features": ["sqrt"],
    }

    rf = RandomForestClassifier(random_state=4, class_weight="balanced")
    multi_rf = MultiOutputClassifier(rf)

    grid_search = GridSearchCV(
        estimator=multi_rf,
        param_grid=param_grid,
        cv=5,
        n_jobs=-1,
        scoring=make_scorer(f1_score, average="macro", zero_division=1),
    )
    grid_search.fit(x_train, y_train)

    best_rf = grid_search.best_estimator_
    print(f"Best parameters found: {grid_search.best_params_}")

    scores = cross_val_score(
        best_rf,
        x_train,
        y_train,
        cv=5,
        scoring=make_scorer(f1_score, average="macro", zero_division=1),
    )
    print(f"Cross-validation F1 scores: {scores}")
    print(f"Mean F1 score: {scores.mean()}")

    # Feature importances for multilabel classifier
    importances = np.mean(
        [
            tree.feature_importances_
            for estimator in best_rf.estimators_
            for tree in estimator.estimators_
        ],
        axis=0,
    )
    indices = np.argsort(importances)[::-1]

    print("Feature ranking:")
    for f in range(x_train.shape[1]):
        print(f"{f + 1}. Feature {indices[f]} ({importances[indices[f]]})")

    return best_rf


def train_random_forest(x_train, y_train):
    clf = RandomForestClassifier(random_state=42)
    clf.fit(x_train, y_train)
    return clf


def clean_text_rf(vectorizer, df):
    # combine text columns
    text = df[["Title", "Body"]]
    text["combined_text"] = text["Title"] + " " + text["Body"]

    # vectorize text columns
    vectorized_text = vectorizer.transform(text["combined_text"]).toarray()
    return vectorized_text


def predict_open_issues(open_issue_df, model, data, y_df):
    # Predict probabilities for open issues
    predicted_probabilities = model.predict_proba(data)

    # Get used domains from y_df and issue numbers from open_issue_df
    columns = y_df.columns
    columns = columns.insert(0, "Issue #")
    issue_numbers = open_issue_df["Issue #"].values

    # Link issue number with predictions and add to data
    prediction_data = []
    for i in range(data.shape[0]):
        curr_prediction = [
            proba[i][1] for proba in predicted_probabilities
        ]  # Extract the probability of the positive class
        curr_issue = [issue_numbers[i]]
        prediction_data.append(curr_issue + curr_prediction)

    # Convert data to DataFrame
    prediction_df = pd.DataFrame(columns=columns, data=prediction_data)
    return prediction_df


def parse_args():
    parser = argparse.ArgumentParser(description="Process some files.")
    parser.add_argument(
        "--config", type=str, required=True, help="Path to the conf.json file"
    )
    parser.add_argument(
        "--domains", type=str, required=True, help="Path to the Domains.json file"
    )
    parser.add_argument(
        "--db", type=str, required=True, help="Path to the SQLite database file"
    )
    parser.add_argument("--method", type=str, required=True, help="Prediction method")
    return parser.parse_args()


def run_llm(args):
    # old version before integration. See `main.py` now.
    raise NotImplementedError
    # Load JSON from file
    with open(args.config, "r") as f:
        repo_data = json.load(f)

    with open(args.domains, "r") as file:
        domain_dictionary = json.load(file)

    # Get repo data
    github_key = repo_data["github_token"]
    owner = repo_data["repo_owner"]
    repo = repo_data["repo_name"]
    openAI_key = repo_data["openAI_key"]

    # Load data and preprocess
    print("Loading data from database")
    db_path = args.db  # Use the database path from the arguments
    df = db_to_df(db_path)
    columns_to_convert = df.columns[15:]
    df[columns_to_convert] = df[columns_to_convert].applymap(
        lambda x: 1 if x > 0 else 0
    )
    df["issue text"] = df["issue text"].apply(clean_text)
    df["issue description"] = df["issue description"].apply(clean_text)
    df = filter_domains(df)

    # Generate fine tuning file
    system_message, assistant_message = generate_system_message(domain_dictionary, df)
    generate_gpt_messages(system_message, assistant_message, df)

    # Fine tune GPT Model
    llm_classifier = fine_tune_gpt(openAI_key)

    # Extract open issues
    print("Extracting open issues...")
    open_issue_data = get_open_issues(owner, repo, github_key)
    open_issue_data["Title"] = open_issue_data["Title"].apply(clean_text)
    open_issue_data["Body"] = open_issue_data["Body"].apply(clean_text)

    # Classify open issues
    print("Classifying open Issues...")
    gpt_responses = get_gpt_responses(
        open_issue_data, llm_classifier, system_message, openAI_key
    )
    predictions_df = responses_to_csv(gpt_responses)
    predictions_df.to_csv("llm_prediction_data.csv", index=False)

    print("Open issue predictions written to csv")


def run_rf(args):
    # old version before integration. See `main.py` now.
    raise NotImplementedError
    # Load JSON from file
    with open(args.config, "r") as f:
        repo_data = json.load(f)

    # Get repo data
    github_key = repo_data["github_token"]
    owner = repo_data["repo_owner"]
    repo = repo_data["repo_name"]

    # Load data and preprocess
    print("Loading data from database")
    db_path = args.db  # Use the database path from the arguments
    df = db_to_df(db_path)
    columns_to_convert = df.columns[15:]
    df[columns_to_convert] = df[columns_to_convert].applymap(
        lambda x: 1 if x > 0 else 0
    )
    df = df.drop(
        columns=[
            "PR #",
            "Pull Request",
            "created_at",
            "closed_at",
            "userlogin",
            "author_name",
            "most_recent_commit",
            "filename",
            "file_commit",
            "api",
            "function_name",
            "api_domain",
            "subdomain",
        ]
    )
    df = df.dropna()

    print("processing data...")
    X_text_features, tfidf = extract_text_features(df)

    # Transform labels
    y_df, mlb = transform_labels(df)

    # Combine features
    X_combined = create_combined_features(X_text_features)

    # Perform MLSMOTE to augment the data
    print("balancing classes...")
    X_augmented, y_augmented = perform_mlsmote(X_combined, y_df, n_sample=500)

    print("training RF model...")
    X_combined = pd.concat([X_combined, X_augmented], axis=0)
    y_combined = pd.concat([y_df, y_augmented], axis=0)

    # Train
    clf = train_random_forest(X_combined, y_combined)

    print("collecting open issues...")
    open_issue_data = get_open_issues(
        owner, repo, github_key
    )  # get open issue number and text

    vectorized_text = clean_text_rf(tfidf, open_issue_data)  # vectorize issue text

    print("classifying open issues...")
    predictions_df = predict_open_issues(
        open_issue_data, clf, vectorized_text, y_df
    )  # predict for open issues

    predictions_df.to_csv(
        "open_issue_predictions.csv", index=False
    )  # write predictions to csv


def main():
    args = parse_args()  # Parse the command-line arguments

    if args.method == "LLM":
        run_llm(args)

    elif args.method == "RF":
        run_rf(args)


if __name__ == "__main__":
    main()
