

import os
import sqlite3


class DatabaseManager():
    def __init__(self, dbfile : str = "./generatedFiles/main.db", cachefile : str ="./generatedFiles/cache.db"):
        """_summary_

        Args:
            dbfile (str, optional): Database file. Defaults to "./generatedFiles/main.db".
        """
        self.conn = sqlite3.connect(dbfile)
    
    def add_pull_request(self, row : list):
        # TODO
        """From csv list.

        Args:
            row (list): csv list of params.
        """
        pass

    def get_unprocessed_files(self):
        # go file by file that has not been processed.
        cur = self.conn.cursor()
        cur.execute("SELECT filename, commit_hash FROM files_changed WHERE processed IS NULL")
        return cur.fetchall()

    def store_class_classification(self, class_name, domain):
        cur = self.conn.cursor()
        cur.execute("SELECT domain FROM api_cache WHERE classname = ?",(class_name,))
        row = cur.fetchone()
        if(row is None):
            cur.execute("INSERT INTO api_cache (classname, domain) VALUES (?,?)",(class_name, domain))
            return True
        else:
            return False

    def store_function_classification(self, class_name, function_name, sub_domain):
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

    def mark_file_as_processed(self, file, commit, status='y'):
        cur = self.conn.cursor()
        cur.execute(f"UPDATE files_changed SET processed=? WHERE filename=? AND commit_hash=?",(status,file,commit))

    def cache_classify_API(self, api : str):
        cur = self.conn.cursor()
        cur.execute(f"SELECT domain FROM api_cache WHERE classname = ?", (api,))
        row = cur.fetchone()
        if(row is None):
            return None
        else:
            return row[0]
    
    def cache_classify_function(self, api : str, function_name : str):
        cur = self.conn.cursor()
        cur.execute(f"SELECT subdomain FROM function_cache WHERE function_name = ? AND classname = ?", (function_name, api))
        row = cur.fetchone()
        if(row is None):
            return None
        else:
            return row[0]

    def save(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def save_caches(self):
        # TODO
        pass

    def load_caches(self):
        # TODO
        pass
        