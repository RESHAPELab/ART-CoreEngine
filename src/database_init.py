from datetime import datetime
import json
import os
import pickle
import sqlite3
import tqdm
from src.database_manager import DatabaseManager


RED_COLOR = "\033[1m\033[38;5;9m"
YELLOW_COLOR = "\033[1m\033[38;5;11m"
RESET_COLOR = "\033[0m"

BASE_PATH = "./output/"
OUTPUT_DB = BASE_PATH + "main.db"
AI_RES_DB = BASE_PATH + "ai_result_backup.db"


def __init_ai_res_db():
    conn = sqlite3.connect(AI_RES_DB)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS apis (
                classname TEXT,
                domain TEXT,
                context_tokens INTEGER,
                response_tokens INTEGER,
                context BLOB,
                response BLOB,
                PRIMARY KEY("classname")
                )
    """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS functions (
                classname TEXT,
                function_name TEXT,
                subdomain TEXT,
                context_tokens INTEGER,
                response_tokens INTEGER,
                context BLOB,
                response BLOB
                )
    """
    )
    cur.execute(
        """
            CREATE TABLE IF NOT EXISTS "settings" (
            "rowID"	INTEGER PRIMARY KEY AUTOINCREMENT,
            "key"	TEXT UNIQUE NOT NULL,
            "value"	TEXT NOT NULL
        )
    """
    )
    cur.execute("SELECT value FROM settings WHERE key = 'created'")

    row = cur.fetchone()
    if row is None:
        print(f"{YELLOW_COLOR}Warning: Missing AI result backup file.")
        print(
            "This could result in previous AI calls being repeated, charging extra money"
        )
        print(
            "Check to see if you have an older version of `output/ai_result_backup.db` before continuing"
        )
        ans = input(f"Type 'yes' to continue. {RESET_COLOR}")
        if ans != "yes":
            print("Quitting.")
            conn.commit()
            cur.close()
            conn.close()
            os.unlink("./output/ai_result_backup.db")
        else:
            print("Created new AI result backup file")
            cur.execute(
                "INSERT INTO settings (key, value) VALUES ('created',?)",
                (datetime.now(),),
            )

    conn.commit()
    cur.close()
    conn.close()


def __init_output_db():
    conn = sqlite3.connect(OUTPUT_DB)
    cur = conn.cursor()
    cur.execute(
        """
                      CREATE TABLE IF NOT EXISTS "files_changed" (
                        "rowID"	INTEGER PRIMARY KEY AUTOINCREMENT,
                        "filename"	TEXT,
                        "processed" TEXT,
                        "commit_hash" TEXT
                    )
                      """
    )
    cur.execute(
        """
                    CREATE TABLE IF NOT EXISTS "api_file_register" (
                        "rowID"	INTEGER PRIMARY KEY AUTOINCREMENT
                    )
                """
    )
    cur.execute(
        """
                      CREATE TABLE IF NOT EXISTS "pull_request_commits" (
                        "rowID"	INTEGER PRIMARY KEY AUTOINCREMENT,
                        "commit_hash" TEXT
                    )
                      """
    )
    cur.execute(
        """
                      CREATE TABLE IF NOT EXISTS "pull_request_comments" (
                            "rowID"	INTEGER PRIMARY KEY AUTOINCREMENT,
                            "comment"	TEXT NOT NULL,
                            "user"	TEXT
                        )
                      """
    )
    cur.execute(
        """
                      CREATE TABLE IF NOT EXISTS "settings" (
                        "rowID"	INTEGER PRIMARY KEY AUTOINCREMENT,
                        "key"	TEXT UNIQUE NOT NULL,
                        "value"	TEXT NOT NULL
                    )
                      """
    )
    cur.execute(
        """
                      CREATE TABLE IF NOT EXISTS "pull_requests" (
                        "rowID"	INTEGER PRIMARY KEY AUTOINCREMENT,
                        "pullNumber"	INTEGER NOT NULL,
                        "title"	TEXT NOT NULL,
                        "descriptionText"	TEXT,
                        "created"	TEXT NOT NULL,
                        "closed"	TEXT,
                        "userlogin"	TEXT,
                        "author"	TEXT,
                        "most_recent_commit" TEXT
                    )
                      """
    )
    cur.execute(
        """
                    CREATE TABLE IF NOT EXISTS "api_cache" (
                    "classname"	TEXT,
                    "domain"	TEXT,
                    "context" BLOB,
                    "response" BLOB,
                    "context_tokens" INTEGER,
                    "response_tokens" INTEGER,
                    "transferred" INTEGER,
                    PRIMARY KEY("classname")
                    )
                """
    )
    cur.execute(
        """
                    CREATE TABLE IF NOT EXISTS "function_cache" (
                    "function_name"	TEXT,
                    "subdomain"	TEXT,
                    "context" BLOB,
                    "response" BLOB,
                    "context_tokens" INTEGER,
                    "response_tokens" INTEGER,
                    "transferred" INTEGER
                )
                """
    )
    cur.execute(
        """
                CREATE TABLE IF NOT EXISTS "files_downloaded" (
                    "rowID"	INTEGER PRIMARY KEY AUTOINCREMENT,
                    "filepath"	TEXT,
                    "hash"	TEXT,
                    "ending" TEXT
                )
                """
    )

    # Data structure for export... this defines the output table. It is an SQL view to use
    # all the power SQL has. query_generator generates the 1/0 columns.
    cur.execute(
        f"""
                CREATE VIEW IF NOT EXISTS outputTable AS
                    SELECT
                        a.pullNumber as "PR #",
                        'True' as "Pull Request",
                        a.title as "issue text",
                        a.descriptionText as "issue description",
                        a.created as "created_at",
                        a.closed as "closed_at",
                        a.userlogin as "userlogin",
                        a.author as "author_name",
                        a.most_recent_commit as "most_recent_commit",
                        b.filename as "filename",
                        b.commit_hash as "file_commit",

                        --- core engine fields

                        c.classname as "api",
                        c.function_name as "function_name",
                        d.domain as "api_domain",
                        f.subdomain as "subdomain",

                        {query_generator()}

                    FROM
                        pull_requests as a,
                        files_changed as b,
                        api_file_register as c,
                        api_cache as d,
                        function_cache as f
                    WHERE
                        a.pullNumber = b.pullNumber AND
                        b.filename = c.filename AND
                        b.commit_hash = c.commit_hash AND
                        c.function_name = f.function_name AND
                        c.classname = f.classname AND
                        c.classname = d.classname
                ;
                """
    )

    conn.commit()
    cur.execute("UPDATE api_cache SET transferred = NULL")
    cur.execute("UPDATE function_cache SET transferred = NULL")
    cur.execute("SELECT value FROM settings WHERE key = 'create'")

    row = cur.fetchone()
    if row is None:
        print("New main.db generated")
        cur.execute(
            "ALTER TABLE pull_request_comments ADD COLUMN pullNumber INTEGER REFERENCES pull_requests(pullNumber)"
        )
        cur.execute(
            "ALTER TABLE pull_request_commits ADD COLUMN pullNumber INTEGER REFERENCES pull_requests(pullNumber)"
        )
        cur.execute(
            "ALTER TABLE files_changed ADD COLUMN pullNumber INTEGER REFERENCES pull_requests(pullNumber)"
        )
        cur.execute(
            "ALTER TABLE function_cache ADD COLUMN classname TEXT REFERENCES api_cache(classname)"
        )
        cur.execute(
            "ALTER TABLE api_file_register ADD COLUMN filename TEXT REFERENCES files_changed(filename)"
        )
        cur.execute(
            "ALTER TABLE api_file_register ADD COLUMN commit_hash TEXT REFERENCES files_changed(commit_hash)"
        )
        cur.execute(
            "ALTER TABLE api_file_register ADD COLUMN classname TEXT REFERENCES api_cache(class_name)"
        )
        cur.execute(
            "ALTER TABLE api_file_register ADD COLUMN function_name TEXT REFERENCES function_cache(function_name)"
        )
        cur.execute(
            "INSERT INTO settings (key, value) VALUES ('create', ?)",
            (datetime.now(),),
        )
        conn.commit()
        cur.close()
        conn.close()
    else:
        print(f"Using main.db generated from {row[0]}")
        conn.commit()
        cur.close()
        conn.close()

def start():
    """Set up Databases with tables. Define database structure."""

    __init_ai_res_db()
    __init_output_db()
    
    setup_caches()
    

def setup_caches():
    """Import caches from backup."""
    db = DatabaseManager()
    db.load_caches()
    db.close()


def save_pr_data(pr_data: dict):
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

    conn = sqlite3.connect(OUTPUT_DB)
    cur = conn.cursor()

    files_added = set()

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

        print(f"Is {num} PR?: {is_pr}")

        if not(is_pr):
            continue # skip if not pr.
        
        issue_num = num
        issue_title = clean_text(data["title"])
        issue_body = clean_text(data["body"])
        created = clean_text(data["created_at"])
        closed = clean_text(data["closed_at"])
        userlogin = clean_text(data["userlogin"])
        comments = clean_text(get_comments(data))

        commit_hashes, files_changed = get_commits(data)
        print(commit_hashes)
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
            search = f"{newest_commit_hash}:{file_change}"
            if search not in files_added:  # no duplicates!
                cur.execute(
                    "INSERT INTO files_changed (pullNumber, filename, commit_hash) VALUES (?, ?, ?)",
                    (issue_num, file_change, newest_commit_hash),
                )
                files_added.add(search)
            else:
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

    cur.close()
    conn.close()


def populate_db_with_mining_data():
    """Go through the mining data "datamining.pkl" and add it to the database. Data import."""
    conn = sqlite3.connect("./output/main.db")
    cur = conn.cursor()

    with open("./output/datamining.pkl", "rb") as file:
        data = pickle.load(file)

    files_added = set()

    for row in tqdm.tqdm(data):
        # Get elements from the rows
        issue_num = row[1]
        pr_check = row[2]
        # If not a PR, skip loop
        if pr_check is not True:
            continue
        issue_text = row[3]
        issue_description = row[4]
        created = row[7]
        closed = row[8]
        userlog = row[9]
        author = row[10]
        comments = row[11]
        files_changed = row[12]
        commit_hashes = row[13]
        commit_hash = row[14]

        # Insert into tables.
        vals = (
            issue_num,
            issue_text,
            issue_description,
            created,
            closed,
            userlog,
            author,
            commit_hash,
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
            search = f"{commit_hash}:{file_change}"
            if search not in files_added:  # no duplicates!
                cur.execute(
                    "INSERT INTO files_changed (pullNumber, filename, commit_hash) VALUES (?, ?, ?)",
                    (issue_num, file_change, commit_hash),
                )
                files_added.add(search)
            else:
                cur.execute(
                    "UPDATE files_changed SET pullNumber=? WHERE filename = ? AND commit_hash = ?",
                    (issue_num, file_change, commit_hash),
                )
        if commit_hash != "":
            for commit in commit_hashes:
                cur.execute(
                    "INSERT INTO pull_request_commits (pullNumber, commit_hash) VALUES (?,?)",
                    (issue_num, commit),
                )

    cur.execute(
        "INSERT INTO settings (key, value) VALUES ('setup', ?)",
        (datetime.now(),),
    )
    conn.commit()
    cur.close()
    conn.close()


def query_generator():
    """Generate the 1/0 columns for each label.

    Returns:
        str: SQL query to be injected into the CREATE VIEW statement.
    """

    subdomain_label_file = "./data/subdomain_labels.json"

    with open(subdomain_label_file, "r", encoding="UTF-8") as f:
        labels = json.load(f)

    out = ""
    for label in labels:
        sub_labels = labels[label]

        out += f"(CASE WHEN d.domain = '{label}' THEN 1 ELSE 0 END) as '{label}'"
        for sub_label in sub_labels:
            out += ",\n"
            out += f"(CASE WHEN d.domain = '{label}' AND f.subdomain = '{list(sub_label.keys())[0]}' THEN 1 ELSE 0 END) as '{label}-{list(sub_label.keys())[0]}'"
        out += ",\n"
    return out[:-2]
