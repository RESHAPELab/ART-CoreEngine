#  DatabaseManager.py
#  Benjamin Carter
#  5/22/2024
#  
#  This file holds the DatabaseManager class, which holds all the main procedures to enact on the databases.
#  Short procedures. This does not include large data import/exports (like in database_init.py)
#  See database_init.py for structure of database.

import os
import sqlite3
from typing import Iterable

class DatabaseManager():
    """Database Manager class. Holds operating functions consisting with the database.
    """
    def __init__(self, dbfile : str = "./generatedFiles/main.db", cachefile : str ="./generatedFiles/cache.db"):
        """Construct and open connection to database.

        Args:
            dbfile (str, optional): _description_. Defaults to "./generatedFiles/main.db".
            cachefile (str, optional): _description_. Defaults to "./generatedFiles/cache.db".
        """
        self.conn = sqlite3.connect(dbfile)
    
    def add_pull_request(self, row : list):
        # TODO
        """From csv list. Adds a single pull request.

        Args:
            row (list): csv list of params.
        """
        raise NotImplementedError
        pass

    def get_unprocessed_files(self) -> Iterable[tuple[str, str]]:
        """Get list of files changed that have not been analyzed yet.

        Returns:
            Iterable[tuple[str, str]]: SQL table with columns: file_path and commit_hash
        """
        # go file by file that has not been processed.
        cur = self.conn.cursor()
        cur.execute("SELECT filename, commit_hash FROM files_changed WHERE processed IS NULL")
        return cur.fetchall()

    def store_class_classification(self, class_name : str, domain : str) -> bool:
        """Store a class/API domain classification in the main cache

        Args:
            class_name (str): API/Class full name
            domain (str): Class domain

        Returns:
            bool: True if new record. False if already in cache.
        """
        cur = self.conn.cursor()
        cur.execute("SELECT domain FROM api_cache WHERE classname = ?",(class_name,))
        row = cur.fetchone()
        if(row is None):
            cur.execute("INSERT INTO api_cache (classname, domain) VALUES (?,?)",(class_name, domain))
            return True
        else:
            return False

    def store_function_classification(self, class_name : str, function_name : str, sub_domain : str) -> bool:
        """Store a function subdomain in main cache

        Args:
            class_name (str): API/Class full name
            function_name (str): Function name
            sub_domain (str): Function sub domain

        Raises:
            ValueError: If classname is not currently registered, throw error. Assumes classname already is logged

        Returns:
            bool: True if new record. False if already in cache
        """
        cur = self.conn.cursor()
        cur.execute("SELECT domain FROM api_cache WHERE classname = ?",(class_name,))
        row = cur.fetchone()
        if(row is None):
            raise ValueError(f"Please classify class first by running store_class_classification({class_name}, DOMAIN). Class {class_name} is not currently in the database")
        
        cur.execute("SELECT subdomain FROM function_cache WHERE classname = ? AND function_name = ?",(class_name,function_name))
        row = cur.fetchone()
        if(row is None):
            cur.execute("INSERT INTO function_cache (classname, function_name, subdomain) VALUES (?,?,?)",(class_name, function_name, sub_domain))
            return True
        else:
            return False
    
    def manageDownload(self, file : str, commit : str) -> str:
        """Create an entry on the files downloaded table. Return temp name

        Args:
            file (str): filename
            commit (str): commit hash

        Returns:
            str: temp name
        """
        cur = self.conn.cursor()
        name, ending = os.path.splitext(file)
        cur.execute("INSERT INTO files_downloaded (filepath, hash, ending) VALUES (?,?,?)", (file, commit, ending))
        cur.execute("SELECT seq FROM sqlite_sequence WHERE name = 'files_downloaded'")
        index = cur.fetchone()[0]

        return f"generatedFiles/downloadedFiles/{index}{ending}"

    def mark_file_as_processed(self, file : str, commit : str, status : str ='y'):
        """Mark file as processed.

        Args:
            file (str): file path
            commit (str): commit hash
            status (str, optional): status of the file. Defaults to 'y' meaning success.
        """
        cur = self.conn.cursor()
        cur.execute(f"UPDATE files_changed SET processed=? WHERE filename=? AND commit_hash=?",(status,file,commit))

    def cache_classify_API(self, api : str) -> (str | None):
        """Classify API from cache

        Args:
            api (str): API/Class name

        Returns:
            (str | None): domain or None if not in cache
        """
        cur = self.conn.cursor()
        cur.execute(f"SELECT domain FROM api_cache WHERE classname = ?", (api,))
        row = cur.fetchone()
        if(row is None):
            return None
        else:
            return row[0]
    
    def cache_classify_function(self, api : str, function_name : str) -> (str | None):
        """Classify function from cache

        Args:
            api (str): api name
            function_name (str): function name

        Returns:
            (str | None): subdomain or None if not in cache
        """
        cur = self.conn.cursor()
        cur.execute(f"SELECT subdomain FROM function_cache WHERE function_name = ? AND classname = ?", (function_name, api))
        row = cur.fetchone()
        if(row is None):
            return None
        else:
            return row[0]

    def save(self):
        """Commit all changes to file
        """
        self.conn.commit()

    def close(self):
        """Close database connection
        """
        self.conn.close()

    def save_caches(self):
        """Copy cache tables to separate cache DB's as backup.
        """
        # TODO
        pass

    def load_caches(self):
        """Load cache tables from cache DB's as backup.
        """
        # TODO
        pass
        