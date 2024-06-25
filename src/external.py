"""
ART-CoreEngine - 2024 - Benjamin Carter 

This file holds the outbound API calls that the UI team can later use.
It is meant to be imported into any external application

The contents of this class shall not depend on anything external.
It must be self contained.

"""

import json
import pickle

import pandas as pd
from src.database_manager import DatabaseManager
from src.open_issue_classification import (
    generate_system_message,
    get_gpt_response_one_issue,
    clean_text_rf,
    predict_open_issues,
)
from src.issue_class import Issue


class External_Model_Interface:
    def __init__(
        self, open_ai_key: str, db: DatabaseManager, model_file: str, domain_file: str
    ):

        with open(model_file, "rb") as f:
            self.model = pickle.load(f)

        with open(domain_file, "r") as f:
            self.domains = json.load(f)

        self.db = db

        self.__open_ai_key = open_ai_key

    def predict_issue(self, issue: Issue):

        if self.model["type"] == "gpt":
            return self.__gpt_predict(issue)
        elif self.model["type"] == "rf":
            return self.__rf_predict(issue)
        else:
            raise NotImplementedError("Model type not recognized")

    def __gpt_predict(self, issue: Issue):
        llm_classifier = self.model["model"]

        columns = self.db.get_df_column_names()
        empty = list(range(len(columns)))
        df = pd.DataFrame(data=empty, columns=columns)

        system_message, assistant_message = generate_system_message(self.domains, df)

        # equiv to get_gpt_responses()
        response = get_gpt_response_one_issue(
            issue, llm_classifier, system_message, self.__open_ai_key
        )

        return response

    def __rf_predict(self, issue: Issue):
        clf = self.model["model"]
        vx = self.model["vectorizer"]
        y_df = self.model["labels"]

        df = pd.DataFrame(columns=["Issue #", "Title", "Body"], data=[issue.get_data()])
        vectorized_text = clean_text_rf(vx, df)

        # predict open issues ()
        predictions = predict_open_issues(df, clf, vectorized_text, y_df)

        max_value = 0.0
        domain_max = ""
        for column in predictions.columns:
            if len(column) < 3 or column == "Issue #":
                continue
            value = predictions[column][0]
            if value > max_value:
                max_value = value
                domain_max = column

        return domain_max
