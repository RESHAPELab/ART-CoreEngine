#  DatabaseManager.py
#  Benjamin Carter
#  5/22/2024
#
#  This file holds the DatabaseManager class, which holds all the main procedures to enact on the databases.
#  Short procedures. This does not include large data import/exports (like in database_init.py)
#  See database_init.py for structure of database.

from datetime import datetime
import json
import os
import sqlite3
import time
from typing import Iterable, Optional
from django.db import connection, connections
from django.db import transaction
import numpy as np
import pandas as pd
import tqdm


class DatabaseManager:
    """Database Manager class. Holds operating functions consisting with the database."""

    def __init__(
        self,
        dbfile: str = "CoreEngine/output/main.db",  # Retained for potential future use or logging
        cachefile: str = "CoreEngine/output/ai_result_backup.db",  # Retained for potential future use or logging
        label_file: str = "CoreEngine/data/subdomain_labels.json",
    ):
        """Construct and load label data.

        Args:
            dbfile (str, optional): Path to main database file. Defaults to "./output/main.db".
            cachefile (str, optional): Path to cache database file. Defaults to "./output/cache.db".
            label_file (str, optional): Path to JSON file with labels.
        """
        self.dbfile = dbfile
        self.cache_file = cachefile
        self.cache_update = False

        # Load domain labels from a JSON file
        with open(label_file, "r", encoding="UTF-8") as f:
            self.domain_labels = json.load(f)

    def add_pull_request(self, row: list):
        # TODO
        """From csv list. Adds a single pull request.

        Args:
            row (list): csv list of params.
        """
        raise NotImplementedError
        pass

    def check_if_pr_already_done(self, issue_number: int):
        """Boolean if PR is in main.db and already extracted

        Args:
            issue_number (int): Issue number

        Returns:
            bool: True if previously extracted
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pullNumber FROM pull_requests WHERE pullNumber = %s", [issue_number]
            )
            return cursor.fetchone() is not None

    def get_unprocessed_files(self, pr: Optional[int] = None) -> Iterable[tuple[str, str]]:
        """Get list of files changed that have not been analyzed yet.

        Args:
            pr (Optional[int]): Pull request number to query.

        Returns:
            Iterable[tuple[str, str]]: List of tuples with columns: file_path and commit_hash
        """
        query = "SELECT filename, commit_hash FROM files_changed WHERE processed IS NULL"
        params = []

        if pr is not None:
            query += " AND pullNumber = %s"
            params.append(pr)

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def get_processed_files(self, pr: Optional[int] = None) -> Iterable[tuple[str, str]]:
        """Get list of files changed that have been successfully analyzed yet.

        Args:
            pr (Optional[int]): Pull request number to query.

        Returns:
            Iterable[tuple[str, str]]: List of tuples with columns: file_path and commit_hash
        """
        if pr is None:
            query = "SELECT filename, commit_hash FROM files_changed WHERE processed IS NOT NULL"
        else:
            query = "SELECT filename, commit_hash FROM files_changed WHERE processed IS NOT NULL AND pullNumber=%s"
            params = [pr]

        with connection.cursor() as cursor:
            cursor.execute(query, params if pr is not None else [])
            return cursor.fetchall()

    def store_class_classification(
        self,
        class_name: str,
        domain: str,
        context_token_number: int,
        response_token_number: int,
        context: bytes,
        response: bytes,
    ) -> bool:
        """Store a class/API domain classification in the main cache

        Args:
            class_name (str): API/Class full name
            domain (str): Class domain
            context_token_number (int): Number of tokens used in context
            response_token_number (int): Number of tokens used in response
            context (bytes): Compressed context fed to AI
            response (bytes): Compressed response returned by AI

        Returns:
            bool: True if new record. False if already in cache.
        """
        with connection.cursor() as cursor:
            cursor.execute("SELECT domain FROM api_cache WHERE classname = %s", [class_name])
            row = cursor.fetchone()
            if row is None:
                cursor.execute(
                    "INSERT INTO api_cache (classname, domain, context, response, context_tokens, response_tokens) VALUES (%s, %s, %s, %s, %s, %s)",
                    (class_name, domain, context, response, context_token_number, response_token_number)
                )
                cursor.execute(
                    "INSERT INTO function_cache (classname, function_name, subdomain) VALUES (%s, 'N/A', 'N/A')",
                    [class_name]
                )
                self.cache_update = True
                return True
            else:
                return False

    def store_function_classification(
        self,
        class_name: str,
        function_name: str,
        sub_domain: str,
        context_token_number: int,
        response_token_number: int,
        context: bytes,
        response: bytes,
    ) -> bool:
        """Store a function subdomain in main cache

        Args:
            class_name (str): API/Class full name
            function_name (str): Function name
            sub_domain (str): Function sub domain
            context_token_number (int) : Number of tokens used in context
            response_token_number (int) : Number of tokens used in response
            context (bytes) : Compressed context fed to AI
            response (bytes) : Compressed response returned by AI

        Raises:
            ValueError: If classname is not currently registered, throw error. Assumes classname already is logged

        Returns:
            bool: True if new record. False if already in cache
        """
        with connection.cursor() as cursor:
            cursor.execute("SELECT domain FROM api_cache WHERE classname = %s", [class_name])
            row = cursor.fetchone()
            if row is None:
                raise ValueError(
                    f"Please classify class first by running store_class_classification({class_name}, DOMAIN). Class {class_name} is not currently in the database"
                )

            cursor.execute(
                "SELECT subdomain FROM function_cache WHERE classname = %s AND function_name = %s",
                (class_name, function_name),
            )
            row = cursor.fetchone()
            if row is None:
                cursor.execute(
                    "INSERT INTO function_cache (classname, function_name, subdomain, context_tokens, response_tokens, context, response) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (
                        class_name,
                        function_name,
                        sub_domain,
                        context_token_number,
                        response_token_number,
                        context,
                        response,
                    ),
                )
                self.cache_update = True
                return True
            else:
                return False

    def manageDownload(self, file: str, commit: str) -> str:
        """Create an entry on the files downloaded table. Return temp name

        Args:
            file (str): filename
            commit (str): commit hash

        Returns:
            str: temp name
        """
        with connection.cursor() as cursor:
            name, ending = os.path.splitext(file)
            cursor.execute(
                "INSERT INTO files_downloaded (filepath, hash, ending) VALUES (%s, %s, %s)",
                (file, commit, ending),
            )
            cursor.execute("SELECT LAST_INSERT_ID()")
            index = cursor.fetchone()[0]

            return f"output/downloaded_files/{index}{ending}"


    def mark_file_as_processed(self, file: str, commit: str, status: str = "y"):
        """Mark file as processed.

        Args:
            file (str): file path
            commit (str): commit hash
            status (str, optional): status of the file. Defaults to 'y' meaning success.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE files_changed SET processed=%s WHERE filename=%s AND commit_hash=%s",
                [status, file, commit]
            )

    def cache_classify_API(self, api: str) -> str | None:
        """Classify API from cache

        Args:
            api (str): API/Class name

        Returns:
            (str | None): domain or None if not in cache
        """
        with connection.cursor() as cursor:
            cursor.execute("SELECT domain FROM api_cache WHERE classname = %s", [api])
            row = cursor.fetchone()
            return row[0] if row else None

    def cache_classify_function(self, api: str, function_name: str) -> str | None:
        """Classify function from cache

        Args:
            api (str): api name
            function_name (str): function name

        Returns:
            (str | None): subdomain or None if not in cache
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT subdomain FROM function_cache WHERE function_name = %s AND classname = %s",
                [function_name, api]
            )
            row = cursor.fetchone()
            return row[0] if row else None


    def mark_file_api_use(self, file: str, commit_hash: str, class_name: str) -> bool:
        """Mark file using a certain API

        Args:
            file (str): File path
            commit_hash (str): Commit Hash
            class_name (str): Class API

        Returns:
            bool: True if added. False if already added.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT rowID FROM api_file_register WHERE filename = %s AND commit_hash = %s AND classname = %s AND function_name = 'N/A'",
                [file, commit_hash, class_name]
            )
            row = cursor.fetchone()
            if row is None:
                cursor.execute(
                    "INSERT INTO api_file_register (filename, commit_hash, classname, function_name) VALUES (%s, %s, %s, 'N/A')",
                    [file, commit_hash, class_name]
                )
                return True
            else:
                return False

    def mark_file_function_use(
        self, file: str, commit_hash: str, class_name: str, function_name: str
    ) -> bool:
        """Mark file using a certain function.

        Args:
            file (str): File path
            commit_hash (str): Commit Hash
            class_name (str): Class API
            function_name (str): Function

        Returns:
            bool: True if added. False if already added.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT rowID FROM api_file_register WHERE filename = %s AND commit_hash = %s AND classname = %s AND function_name = %s",
                [file, commit_hash, class_name, function_name]
            )
            row = cursor.fetchone()
            if row is None:
                cursor.execute(
                    "INSERT INTO api_file_register (filename, commit_hash, classname, function_name) VALUES (%s, %s, %s, %s)",
                    [file, commit_hash, class_name, function_name]
                )
                return True
            else:
                return False

    def save(self):
        """Commit all changes to the database."""
        if self.cache_update:
            self.save_caches()
            self.cache_update = False
        transaction.commit()

    def close(self):
        """Close database connection"""
        pass

    def save_caches(self):
        """Copy cache tables to separate cache DB's as backup."""
        default_cursor = connections['default'].cursor()  # Your primary database
        backup_cursor = connections['backup'].cursor()  # Your backup database defined in DATABASES setting

        with default_cursor as cur, backup_cursor as backup:
            cur.execute(
                "SELECT classname, domain, context_tokens, response_tokens, context, response FROM api_cache WHERE transferred IS NULL"
            )
            rows = cur.fetchall()
            for row in rows:
                backup.execute(
                    "SELECT classname, domain FROM apis WHERE classname = %s", [row[0]]
                )
                test = backup.fetchone()
                if test is None:
                    backup.execute(
                        "INSERT INTO apis (classname, domain, context_tokens, response_tokens, context, response) VALUES (%s, %s, %s, %s, %s, %s)",
                        (row[0], row[1], row[2], row[3], row[4], row[5])
                    )

            cur.execute("UPDATE api_cache SET transferred = 1 WHERE transferred IS NULL")
            transaction.commit(using='default')

            backup.execute(
                "SELECT classname, function_name, subdomain, context_tokens, response_tokens, context, response FROM function_cache WHERE transferred IS NULL"
            )
            rows = cur.fetchall()
            for row in rows:
                backup.execute(
                    "SELECT classname, function_name, subdomain FROM functions WHERE classname = %s AND function_name = %s",
                    (row[0], row[1])
                )
                test = backup.fetchone()
                if test is None:
                    backup.execute(
                        "INSERT INTO functions (classname, function_name, subdomain, context_tokens, response_tokens, context, response) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (row[0], row[1], row[2], row[3], row[4], row[5], row[6])
                    )

            transaction.commit(using='backup')

    def load_caches(self):
        """Load cache tables from cache DB's backup."""
        default_cursor = connections['default'].cursor()
        backup_cursor = connections['backup'].cursor()

        with backup_cursor as backup, default_cursor as cur:
            backup.execute("SELECT classname, domain FROM apis")
            rows = backup.fetchall()
            for row in rows:
                cur.execute(
                    "SELECT classname, domain FROM api_cache WHERE classname = %s AND domain = %s",
                    [row[0], row[1]]
                )
                test = cur.fetchone()
                if test is None:
                    cur.execute(
                        "INSERT INTO api_cache (classname, domain) VALUES (%s, %s)",
                        [row[0], row[1]]
                    )

            backup.execute("SELECT classname, function_name, subdomain FROM functions")
            rows = backup.fetchall()
            for row in rows:
                cur.execute(
                    "SELECT classname, function_name, subdomain FROM function_cache WHERE classname = %s AND function_name = %s AND subdomain = %s",
                    [row[0], row[1], row[2]]
                )
                test = cur.fetchone()
                if test is None:
                    cur.execute(
                        "INSERT INTO function_cache (classname, function_name, subdomain) VALUES (%s, %s, %s)",
                        [row[0], row[1], row[2]]
                    )

            transaction.commit(using='default')

    @transaction.atomic
    def save_pr_data(self, pr_data: dict):
        def clean_text(text):
            """Replace newline characters with spaces, handling None values."""
            if text is None:
                return ""
            return text.replace("\n", " ").replace("\r", " ")

        def get_comments(data):
            comments = data.get("comments")
            clean_comments: list = []

            if comments:
                for comment in comments.values():
                    body = clean_text(comment.get("body", ""))
                    clean_comments.append(body)

            return " | ".join(clean_comments)

        def get_commits(data):
            files_changed: list = []
            clean_commits: list = []

            commits = data.get("commits")

            if commits:
                for commit in commits.values():
                    commit_date = commit.get("date", "")
                    if commit_date:  # Only parse if commit_date is not empty
                        try:
                            commit_date_obj = datetime.strptime(
                                commit_date, "%Y-%m-%dT%H:%M:%SZ"
                            )
                            clean_commits.append(
                                (
                                    commit_date_obj,
                                    commit.get("sha", ""),
                                    commit.get("author_name", ""),
                                )
                            )
                        except ValueError:
                            continue  # Skip this commit if the date is invalid
                    files = commit.get("files", {})
                    if files:
                        files_changed.extend(files.get("file_list", []))

            # Sort commits by date (newest to oldest)
            clean_commits.sort(key=lambda x: x[0], reverse=True)
            sorted_commit_hashes = [commit[1] for commit in clean_commits]

            return sorted_commit_hashes, files_changed

        cur = self.conn.cursor()

        # "issue": clean_text(pr.get("title", "")),
        # "Pull Request": pr.get("is_pr", ""),
        # "issue text": clean_text(pr.get("title", "")),
        # "issue description": clean_text(pr.get("body", "")),
        # "pull request text": clean_text(pr.get("title", "")),
        # "pull request description": clean_text(pr.get("body", "")),
        # "created_at": clean_text(pr.get("created_at", "")),
        # "closed_at": clean_text(pr.get("closed_at", "")),
        # "userlogin": clean_text(pr.get("userlogin", "")),

        for num, data in pr_data.items():
            if not data["is_pr"]:
                continue
            with connections['default'].cursor() as cursor:
                issue_num = num
                issue_title = clean_text(data["title"])
                issue_body = clean_text(data["body"])
                created = clean_text(data["created_at"])
                closed = clean_text(data["closed_at"])
                userlogin = clean_text(data["userlogin"])
                comments = clean_text(get_comments(data))
                commit_hashes, files_changed = get_commits(data)
                newest_commit_hash = commit_hashes[0]
                author = newest_commit_hash[2]

                cursor.execute(
                    "INSERT INTO pull_requests (pullNumber, title, descriptionText, created, closed, userlogin, author, most_recent_commit) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (issue_num, issue_title, issue_body, created, closed, userlogin, author, newest_commit_hash)
                )

                for comment in comments:
                    if comment:
                        cursor.execute(
                            "INSERT INTO pull_request_comments (pullNumber, comment) VALUES (%s, %s)",
                            (issue_num, comment)
                        )

                for file_change in set(files_changed):
                    if file_change:
                        cursor.execute(
                            "SELECT pullNumber FROM files_changed WHERE filename = %s AND commit_hash = %s",
                            (file_change, newest_commit_hash)
                        )
                        search_result = cursor.fetchone()
                        if search_result is None:
                            cursor.execute(
                                "INSERT INTO files_changed (pullNumber, filename, commit_hash) VALUES (%s, %s, %s)",
                                (issue_num, file_change, newest_commit_hash)
                            )
                        elif search_result[0] != issue_num:
                            cursor.execute(
                                "UPDATE files_changed SET pullNumber = %s WHERE filename = %s AND commit_hash = %s",
                                (issue_num, file_change, newest_commit_hash)
                            )
                for commit in commit_hashes:
                    cursor.execute(
                        "INSERT INTO pull_request_commits (pullNumber, commit_hash) VALUES (%s, %s)",
                        (issue_num, commit)
                    )

    def get_df(self, prs):
        full_data = []
        with connection.cursor() as cursor:
            for pr in tqdm.tqdm(prs):
                cursor.execute(
                    """SELECT title, descriptionText, created, closed, userlogin, author, most_recent_commit
                    FROM pull_requests
                    WHERE pullNumber = %s""", [pr])
                result = cursor.fetchone()
                if result is None:
                    continue
                full_data.append(result)

        print(f"Processed {len(full_data)}. Skipped {len(prs) - len(full_data)} empty PRs")
        df = pd.DataFrame(data=full_data, columns=self.get_df_column_names())
        return df

    def get_df_column_names(self):
        """Retrieve column names for the dataframe."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'pull_requests'")
            column_names = [row[0] for row in cursor.fetchall()]
        return column_names
    # drop in replacement for get_pr_data without needing the extra db connection

    def get_pr_meta_data(self, pr):
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT title, descriptionText, created, closed, userlogin, author, most_recent_commit
                FROM pull_requests
                WHERE pullNumber = %s""", [pr])
            return cursor.fetchone()

    def get_pr_data(self, pr):
        # We assume get_pr_meta_data is already refactored to use Django's database connection.
        meta_data = self.get_pr_meta_data(pr)
        if not meta_data:
            return None
        
        base_data = [pr, True] + list(meta_data)

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    file_table.filename,
                    file_table.commit_hash,
                    apis.classname,
                    apis.domain,
                    functions.function_name,
                    functions.subdomain
                FROM
                    files_changed AS file_table
                    JOIN api_file_register AS file_apis ON file_table.filename = file_apis.filename AND file_table.commit_hash = file_apis.commit_hash
                    JOIN api_cache AS apis ON apis.classname = file_apis.classname
                    JOIN function_cache AS functions ON functions.classname = file_apis.classname AND functions.function_name = file_apis.function_name
                WHERE 
                    file_table.pullNumber = %s AND
                    file_table.processed = 'y'
            """, [pr])
            output = cursor.fetchall()

        # Initialize label data array based on domain labels structure.
        label_data = []
        for label in self.domain_labels:
            label_data.append(0)
            for sub_label in self.domain_labels[label]:
                label_data.append(0)

        zero_range = len(label_data)
        query_data = []

        for row in output:
            file_data = [
                row[0],  # filename
                row[1],  # commit_hash
                row[2],  # classname
                row[4],  # function_name
                row[3],  # domain
                row[5],  # subdomain
            ]
            # Reset label data for each row.
            temp_label_data = [0] * zero_range
            counter = 0
            for label in self.domain_labels:
                if row[3] == label:  # Domain check
                    temp_label_data[counter] = 1
                    if row[5] == "N/A":  # Subdomain check
                        break
                counter += 1
                for sub_label_dict in self.domain_labels[label]:
                    sub_label = list(sub_label_dict.keys())[0]
                    if row[5] == sub_label:
                        temp_label_data[counter] = 1
                        break
                    counter += 1

            query_data_row = base_data + file_data + temp_label_data
            query_data.append(query_data_row)

        # Collapsing data for the top file of the PR
        if len(query_data) != 0:
            first_half = list(query_data[0][:15])
            second_half = list(query_data[0][15:])
            for i in range(1, len(query_data)):
                second_half = np.add(second_half, list(query_data[i][15:]))
            combined_data = first_half + second_half.tolist()
            return combined_data
        return None


if __name__ == "__main__":
    # Test to see if both outputs are the same

    test = DatabaseManager()
    st = time.time()
    i = test.get_pr_data(86)
    print((time.time() - st) * 1000)
    st = time.time()
    i2 = test.get_pr_data_old(86)
    print((time.time() - st) * 1000)
    for x in range(len(i)):
        print(i[x], i2[x])
    test.close()
