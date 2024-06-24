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

try:
    from src.database_manager import DatabaseManager
    from src.open_issue_classification import (
        generate_system_message,
        get_gpt_response_one_issue,
        clean_text_rf,
        predict_open_issues,
    )
    from src.issue import Issue
except:
    from database_manager import DatabaseManager
    from open_issue_classification import (
        generate_system_message,
        get_gpt_response_one_issue,
        clean_text_rf,
        predict_open_issues,
    )
    from issue import Issue


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


# def predict_open_issues(open_issue_df, model, data, y_df):

#     # predict for open issues
#     predicted_values = model.predict(data)

#     # get used domains from csv and issue numbers from df
#     columns = y_df.columns
#     columns = columns.insert(0, "Issue #")
#     issue_numbers = open_issue_df["Issue #"].values

#     # link issue number with predictions and add to data
#     prediction_data = []
#     for i in range(len(predicted_values)):
#         curr_prediction = predicted_values[i].tolist()
#         curr_issue = [issue_numbers[i]]
#         prediction_data.append(curr_issue + curr_prediction)

#     # convert data to df
#     prediction_df = pd.DataFrame(columns=columns, data=prediction_data)
#     return prediction_df


if __name__ == "__main__":
    db = DatabaseManager()
    external = External_Model_Interface(
        "open_ai", db, "./output/rf_model.pkl", "./data/domain_labels.json"
    )
    issue = Issue(
        1,
        "Database connection fails when power goes off.",
        """Hey, I noticed that when I unplug my computer, the database server on my computer stops working.
                This is definitely an issue.""",
    )
    print(external.predict_issue(issue))

    db.close()
