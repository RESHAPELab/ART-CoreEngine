"""
ART-CoreEngine - 2024 - Anonymous

This file holds the outbound API calls that the UI team can later use.
It is meant to be imported into any external application

The contents of this class shall not depend on anything external.
It must be self contained.

"""

import json
import os
import pickle
from joblib import Memory

import pandas as pd
from .database_manager import DatabaseManager
from .classifier import (
    generate_system_message,
    get_gpt_response_one_issue,
    clean_text_rf,
    label_issue_binary_classification,
    predict_open_issues,
)
from .issue_class import Issue


class External_Model_Interface:
    def __init__(
        self,
        open_ai_key: str,
        db: DatabaseManager,
        model_file: str,
        domain_file: str,
        subdomain_file: str,
        formatted_domain_file: str,
        response_cache_key: str,
        response_cache_directory: str,
        bytes_limit: int = 1024 * 1024 * 40,  # 40 MB cache
    ):

        with open(model_file, "rb") as f:
            self.model = pickle.load(f)

        with open(domain_file, "r") as f:
            self.domains = json.load(f)

        with open(subdomain_file, "r") as f:
            self.subdomains = json.load(f)

        with open(formatted_domain_file, "r") as f:
            self.formatted_domains = json.load(f)

        if "save_version" in self.model and self.model["save_version"] == os.getenv(
            "CORE_ENGINE_VERSION"
        ):
            pass
        else:
            print(
                f"""Model save version does match current CoreEngine version. This may cause future errors
\tCoreEngine Version: {os.getenv("CORE_ENGINE_VERSION")}   Model Version: {self.model.get("save_version")}"""
            )

        self.db = db
        self.model_file_name = model_file
        self.__open_ai_key = open_ai_key
        self.response_cache_key = response_cache_key
        self.bytes_limit = bytes_limit
        if self.response_cache_key is None:
            # no caching!
            self.__cached_predictions = self.__predict_issue
        else:
            self.memory = Memory(response_cache_directory, verbose=0)
            self.__cached_predictions = self.memory.cache(
                self.__predict_issue, ignore=["num", "title", "body", "self"]
            )

    def predict_issue(self, issue: Issue, max_domains=None):
        # Cache key incorporates the model to ensure updates to the model invalidate the cache
        cache_key = f"{self.response_cache_key}_{self.model['type']}_{self.model.get('save_version')}_{self.model_file_name}_{issue.number}_{issue.title}"

        if self.response_cache_key is None:
            out = self.__cached_predictions(
                issue.number, issue.title, issue.body, None, max_domains
            )
            return out

        out = self.__cached_predictions(
            issue.number, issue.title, issue.body, cache_key, max_domains
        )
        # print(
        #     f"Predict Issue Cache Store - {cache_key}"
        # )  # Any changes to this function will invalidate cache!
        self.memory.reduce_size(bytes_limit=self.bytes_limit)
        return out

    def __predict_issue(self, num, title, body, _ignore_me, max_domains=None):
        print(
            f"Predict Issue Cache Miss - {_ignore_me}"
        )  # Any changes to this function will invalidate cache!
        issue = Issue(num, title, body)  # for caching.

        if self.model["type"] == "gpt":
            return self.__gpt_predict(issue)
        if self.model["type"] == "gpt-combined":
            return self.__gpt_combined_predict(issue, max_domains)
        elif self.model["type"] == "rf":
            return self.__rf_predict(issue)
        else:
            raise NotImplementedError("Model type not recognized")

    def __gpt_predict(self, issue: Issue):
        llm_classifier = self.model["model"]

        columns = self.db.get_df_column_names()
        empty = [list(range(len(columns)))]
        df = pd.DataFrame(data=empty, columns=columns)

        domains, subdomains = generate_system_message(self.domains, self.subdomains, df)
        # equiv to get_gpt_responses()
        response = get_gpt_response_one_issue(
            issue, llm_classifier, domains, subdomains, self.__open_ai_key
        )

        return response

    def __gpt_combined_predict(self, issue: Issue, max_domains=None):
        gpt_models = self.model["model_table"]

        response = label_issue_binary_classification(
            issue, gpt_models, self.formatted_domains, self.__open_ai_key, max_domains
        )

        # domain_response is 1 if apply. 0 if not.
        output = {}

        for domain, data in response.items():
            if data["domain_response"] == 0:
                continue
            output[domain] = data["subdomain_response"]

        return output

    def __rf_predict(self, issue: Issue):
        # print("rf")
        clf = self.model["model"]
        vx = self.model["vectorizer"]
        y_df = self.model["labels"]

        # Uncomment print statements for verbose debugging output

        # Creating DataFrame for the issue
        # print("Starting Random Forest Prediction")
        # print("Creating DataFrame for the issue")
        df = pd.DataFrame(columns=["Issue #", "Title", "Body"], data=[issue.get_data()])
        # print("DataFrame created: ")
        # print(df)

        # Cleaning and vectorizing text
        # print("Cleaning and vectorizing text")
        vectorized_text = clean_text_rf(vx, df)
        # print("Vectorized text: ")
        # print(vectorized_text)

        # Predicting open issues
        # print("Predicting open issues")
        predictions = predict_open_issues(df, clf, vectorized_text, y_df)
        # print("Predictions DataFrame: ")
        # print(predictions)

        # Calculate label frequencies
        label_frequencies = y_df.mean(axis=0)
        # print("Label frequencies:")
        # print(label_frequencies)

        # Filter out labels with more than 60% occurrence
        frequent_labels = label_frequencies[
            label_frequencies > 0.6
        ].index.tolist()  # TODO: Make this a parameter, specifies threshold of predictions.
        # TODO: limit subdomains by parameter.

        # print("Frequent labels to be dropped:")
        # print(frequent_labels)

        value_out: list[float] = []
        columns: list[str] = []

        for column in predictions.columns:
            if len(column) < 3 or column == "Issue #" or column in frequent_labels:
                continue
            value = predictions[column][0]
            # print(f"Label: {column}, Predicted Probability: {value}")

            if len(value_out) == 0:
                value_out.insert(0, value)
                columns.insert(0, column)
            else:
                x = 0
                while x < len(value_out) and value_out[x] > value:
                    x += 1
                value_out.insert(x, value)
                columns.insert(x, column)

        # print("Top 3 predictions:")
        # print(columns[:3])
        return columns[:3]
