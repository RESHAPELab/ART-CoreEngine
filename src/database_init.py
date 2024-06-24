from datetime import datetime
import json
import os
import sqlite3
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
            CREATE UNIQUE INDEX IF NOT EXISTS "QuickFuncLookup" ON "functions" (
                "classname"	ASC,
                "function_name"	ASC
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
                        "pullNumber"	INTEGER UNIQUE NOT NULL,
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
    cur.execute(
        """
            CREATE UNIQUE INDEX IF NOT EXISTS "QuickFileClassFunction" ON "api_file_register" (
                "filename"	ASC,
                "commit_hash"	ASC,
                "classname"	ASC,
                "function_name"	ASC
            );
            """
    )

    cur.execute(
        """CREATE INDEX IF NOT EXISTS "QuickFunctionCache" ON "function_cache" (
            "classname",
            "function_name",
            "subdomain"
        )"""
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
