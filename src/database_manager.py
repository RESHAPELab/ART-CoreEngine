#  DatabaseManager.py
#  Benjamin Carter
#  5/22/2024
#
#  This file holds the DatabaseManager class, which holds all the main procedures to enact on the databases.
#  Short procedures. This does not include large data import/exports (like in database_init.py)
#  See database_init.py for structure of database.

from datetime import datetime
import os
import sqlite3
from typing import Iterable, Optional


class DatabaseManager:
    """Database Manager class. Holds operating functions consisting with the database."""

    def __init__(
        self,
        dbfile: str = "./output/main.db",
        cachefile: str = "./output/ai_result_backup.db",
    ):
        """Construct and open connection to database.

        Args:
            dbfile (str, optional): _description_. Defaults to "./output/main.db".
            cachefile (str, optional): _description_. Defaults to "./output/cache.db".
        """
        self.conn = sqlite3.connect(dbfile)
        self.cache_file = cachefile
        self.cache_update = False

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
        cur = self.conn.cursor()
        cur.execute(
            "SELECT pullNumber FROM pull_requests WHERE pullNumber = ?", (issue_number,)
        )
        out = cur.fetchone()
        return out is not None

    def get_unprocessed_files(
        self, pr: Optional[int] = None
    ) -> Iterable[tuple[str, str]]:
        """Get list of files changed that have not been analyzed yet.

        Args:
            pr (Optional[int]): Pull request number to query.

        Returns:
            Iterable[tuple[str, str]]: SQL table with columns: file_path and commit_hash
        """
        # go file by file that has not been processed.
        cur = self.conn.cursor()
        if pr is None:
            cur.execute(
                "SELECT filename, commit_hash FROM files_changed WHERE processed IS NULL"
            )
        else:
            cur.execute(
                "SELECT filename, commit_hash FROM files_changed WHERE processed IS NULL AND pullNumber=?",
                (pr,),
            )
        return cur.fetchall()

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
            context_token_number (int) : Number of tokens used in context
            response_token_number (int) : Number of tokens used in response
            context (bytes) : Compressed context fed to AI
            response (bytes) : Compressed response returned by AI

        Returns:
            bool: True if new record. False if already in cache.
        """
        cur = self.conn.cursor()
        cur.execute("SELECT domain FROM api_cache WHERE classname = ?", (class_name,))
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO api_cache (classname, domain, context, response, context_tokens, response_tokens) VALUES (?,?,?,?,?,?)",
                (
                    class_name,
                    domain,
                    context,
                    response,
                    context_token_number,
                    response_token_number,
                ),
            )
            cur.execute(
                "INSERT INTO function_cache (classname, function_name, subdomain) VALUES (?,'N/A','N/A')",
                (class_name,),
            )  # Don't store a repeated response. Save the response in api_cache.
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
        cur = self.conn.cursor()
        cur.execute("SELECT domain FROM api_cache WHERE classname = ?", (class_name,))
        row = cur.fetchone()
        if row is None:
            raise ValueError(
                f"Please classify class first by running store_class_classification({class_name}, DOMAIN). Class {class_name} is not currently in the database"
            )

        cur.execute(
            "SELECT subdomain FROM function_cache WHERE classname = ? AND function_name = ?",
            (class_name, function_name),
        )
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO function_cache (classname, function_name, subdomain, context_tokens, response_tokens, context, response) VALUES (?,?,?,?,?,?,?)",
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
        cur = self.conn.cursor()
        name, ending = os.path.splitext(file)
        cur.execute(
            "INSERT INTO files_downloaded (filepath, hash, ending) VALUES (?,?,?)",
            (file, commit, ending),
        )
        cur.execute("SELECT seq FROM sqlite_sequence WHERE name = 'files_downloaded'")
        index = cur.fetchone()[0]

        return f"output/downloaded_files/{index}{ending}"

    def mark_file_as_processed(self, file: str, commit: str, status: str = "y"):
        """Mark file as processed.

        Args:
            file (str): file path
            commit (str): commit hash
            status (str, optional): status of the file. Defaults to 'y' meaning success.
        """
        cur = self.conn.cursor()
        cur.execute(
            f"UPDATE files_changed SET processed=? WHERE filename=? AND commit_hash=?",
            (status, file, commit),
        )

    def cache_classify_API(self, api: str) -> str | None:
        """Classify API from cache

        Args:
            api (str): API/Class name

        Returns:
            (str | None): domain or None if not in cache
        """
        cur = self.conn.cursor()
        cur.execute(f"SELECT domain FROM api_cache WHERE classname = ?", (api,))
        row = cur.fetchone()
        if row is None:
            return None
        else:
            return row[0]

    def cache_classify_function(self, api: str, function_name: str) -> str | None:
        """Classify function from cache

        Args:
            api (str): api name
            function_name (str): function name

        Returns:
            (str | None): subdomain or None if not in cache
        """
        cur = self.conn.cursor()
        cur.execute(
            f"SELECT subdomain FROM function_cache WHERE function_name = ? AND classname = ?",
            (function_name, api),
        )
        row = cur.fetchone()
        if row is None:
            return None
        else:
            return row[0]

    def mark_file_api_use(self, file: str, commit_hash: str, class_name: str) -> bool:
        """Mark file using a certain API

        Args:
            file (str): File path
            commit_hash (str): Commit Hash
            class_name (str): Class API

        Returns:
            bool: True if added. False if already added.
        """
        cur = self.conn.cursor()
        params = (file, commit_hash, class_name)
        cur.execute(
            f"SELECT rowID FROM api_file_register WHERE filename = ? AND commit_hash = ? AND classname = ? AND function_name = 'N/A'",
            params,
        )
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO api_file_register (filename, commit_hash, classname, function_name) VALUES (?,?,?,'N/A')",
                params,
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
        cur = self.conn.cursor()
        params = (file, commit_hash, class_name, function_name)
        cur.execute(
            f"SELECT rowID FROM api_file_register WHERE filename = ? AND commit_hash = ? AND classname = ? AND function_name = ?",
            params,
        )
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO api_file_register (filename, commit_hash, classname,function_name) VALUES (?,?,?,?)",
                params,
            )
            return True
        else:
            return False

    def save(self):
        """Commit all changes to file"""
        self.conn.commit()
        if self.cache_update:
            self.save_caches()
            self.cache_update = False

    def close(self):
        """Close database connection"""
        self.conn.close()

    def save_caches(self):
        """Copy cache tables to separate cache DB's as backup."""
        backup_connection = sqlite3.connect(self.cache_file)
        backup = backup_connection.cursor()

        cur = self.conn.cursor()
        cur.execute(
            "SELECT classname, domain, context_tokens, response_tokens, context, response FROM api_cache WHERE transferred IS NULL"
        )
        rows = cur.fetchall()
        for row in rows:
            backup.execute(
                "SELECT classname, domain FROM apis WHERE classname = ?", (row[0],)
            )
            test = backup.fetchone()
            if test is None:
                backup.execute(
                    "INSERT INTO apis (classname, domain, context_tokens, response_tokens, context, response) VALUES (?, ?, ?, ?, ?, ?)",
                    (row[0], row[1], row[2], row[3], row[4], row[5]),
                )
            else:
                pass  # assume backup is right! Differing domains.
        cur.execute("UPDATE api_cache SET transferred = 1 WHERE transferred IS NULL")
        self.conn.commit()

        backup_connection.commit()

        cur.execute(
            "SELECT classname, function_name, subdomain, context_tokens, response_tokens, context, response FROM function_cache WHERE transferred IS NULL"
        )
        rows = cur.fetchall()
        for row in rows:
            backup.execute(
                "SELECT classname, function_name, subdomain FROM functions WHERE classname = ? AND function_name = ?",
                (row[0], row[1]),
            )
            test = backup.fetchone()
            if test is None:
                backup.execute(
                    "INSERT INTO functions (classname, function_name, subdomain, context_tokens, response_tokens, context, response) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (row[0], row[1], row[2], row[3], row[4], row[5], row[6]),
                )
            else:
                pass  # assume backup is right! Differing subdomains.

        cur.execute(
            "UPDATE function_cache SET transferred = 1 WHERE transferred IS NULL"
        )
        self.conn.commit()

        backup_connection.commit()
        backup.close()
        backup_connection.close()

    def load_caches(self):
        """Load cache tables from cache DB's backup."""
        backup_connection = sqlite3.connect(self.cache_file)
        backup = backup_connection.cursor()

        cur = self.conn.cursor()
        backup.execute("SELECT classname, domain FROM apis")
        rows = backup.fetchall()
        for row in rows:
            cur.execute(
                "SELECT classname, domain FROM api_cache WHERE classname = ? AND domain = ?",
                (row[0], row[1]),
            )
            test = cur.fetchone()
            if test is None:
                cur.execute(
                    "INSERT INTO api_cache (classname, domain) VALUES (?, ?)",
                    (row[0], row[1]),
                )

        backup.execute("SELECT classname, function_name, subdomain FROM functions")
        rows = backup.fetchall()
        for row in rows:
            cur.execute(
                "SELECT classname, function_name, subdomain FROM function_cache WHERE classname = ? AND function_name = ? AND subdomain = ?",
                (row[0], row[1], row[2]),
            )
            test = cur.fetchone()
            if test is None:
                cur.execute(
                    "INSERT INTO function_cache (classname, function_name, subdomain) VALUES (?, ?, ?)",
                    (row[0], row[1], row[2]),
                )

        self.conn.commit()
        backup.close()
        backup_connection.close()

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
            is_pr = data["is_pr"]

            if not (is_pr):
                continue  # skip if not pr.

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

            commit_hashes = " | ".join(commit_hashes)

            vals = (
                issue_num,
                issue_title,
                issue_body,
                created,
                closed,
                userlogin,
                author,
                newest_commit_hash,
            )
            cur.execute(
                "INSERT INTO pull_requests (pullNumber, title, descriptionText, created, closed, userlogin, author, most_recent_commit) VALUES (?,?,?,?,?,?,?,?)",
                vals,
            )
            for comment in comments:
                if comment == "":
                    continue
                cur.execute(
                    "INSERT INTO pull_request_comments (pullNumber, comment) VALUES (?,?)",
                    (issue_num, comment),
                )

            for file_change in set(files_changed):
                if file_change == "":
                    continue

                search_request = cur.execute(
                    "SELECT pullNumber FROM files_changed WHERE filename=? AND commit_hash=?",
                    (file_change, newest_commit_hash),
                )

                search_result = search_request.fetchone()
                if search_result is None:  # no duplicates!
                    cur.execute(
                        "INSERT INTO files_changed (pullNumber, filename, commit_hash) VALUES (?, ?, ?)",  # sets processed to NULL
                        (issue_num, file_change, newest_commit_hash),
                    )
                elif search_result[0] != issue_num:
                    cur.execute(
                        "UPDATE files_changed SET pullNumber=? WHERE filename = ? AND commit_hash = ?",
                        (issue_num, file_change, newest_commit_hash),
                    )
            if newest_commit_hash != "":
                for commit in commit_hashes:
                    cur.execute(
                        "INSERT INTO pull_request_commits (pullNumber, commit_hash) VALUES (?,?)",
                        (issue_num, commit),
                    )

        self.conn.commit()
