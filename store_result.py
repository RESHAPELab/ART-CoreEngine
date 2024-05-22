import csv
import os
import sqlite3
import pandas as pd

def create_and_populate_db(db_path):
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''CREATE TABLE IF NOT EXISTS example_table (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        age INTEGER
                    )''')
    
    # Insert data
    cursor.execute("INSERT INTO example_table (name, age) VALUES ('Alice', 30)")
    cursor.execute("INSERT INTO example_table (name, age) VALUES ('Bob', 25)")
    cursor.execute("INSERT INTO example_table (name, age) VALUES ('Charlie', 35)")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()

def sqlite_to_csv(db_path, table_name, output_csv_path):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    
    # Load the table into a pandas DataFrame
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)
    
    # Export the DataFrame to a CSV file
    df.to_csv(output_csv_path, index=False)  # index=False to avoid writing row numbers

    # Close the connection
    conn.close()

    print(f"Table {table_name} has been exported to {output_csv_path}")



def in_csv(csv_file, key_name):
    if os.path.exists(csv_file):
        with open(csv_file, 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if row and row[0] == key_name:
                    return True

    return False


def get_from_csv(csv_file, key_name):
    if os.path.exists(csv_file):
        with open(csv_file, 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if row and row[0] == key_name:
                    return row[1]
    return None


def add_to_csv(csv_file, key_name, label):
    found = in_csv(csv_file, key_name)

    if not found:
        with open(csv_file, 'a', newline='') as file:
            writer = csv.writer(file)
            file.seek(0, os.SEEK_END)  # Move pointer to the end of file
            if file.tell() == 0:  # Check if file is empty
                writer.writerow(['key', 'label'])  # Write header row if file is empty
            writer.writerow([key_name, label])


def store_file(csv_file, file_name, domains, subdomains):
    found = in_csv(csv_file, file_name)

    if not found:
        with open(csv_file, 'a', newline='') as file:
            file.seek(0, os.SEEK_END)  # Move pointer to the end of file
            writer = csv.writer(file)
            if file.tell() == 0:  # Check if file is empty
                writer.writerow(['filename', 'domains', 'subdomains'])  # Write header row if file is empty
            domains_str = ', '.join(domains)
            subdomains_str = ', '.join(subdomains)
            if subdomains_str == "":
                subdomains_str = "None Used"
            writer.writerow([file_name, domains_str, subdomains_str])


# Example usage:
# csv_file = 'data.csv'
# key_name = input("Enter key name to check and possibly add: ")
# description = input("Enter description: ")
#
# add_to_csv(csv_file, key_name, description)
# print(get_from_csv('function_storage.csv', 'java.util.List'))

# csv_file = 'test.csv'
# file_name = 'java.util.test'
# domains = ['UI', 'DB', 'etc.']
# subdomains = ['UI-event', 'DB-connection', 'etc']
#
# store_file(csv_file, file_name, domains, subdomains)


# Example usage of SQL to CSV

# # Path to your SQLite database
# db_path = 'example.db'

# # Create and populate the database
# create_and_populate_db(db_path)

# # Export the table to a CSV
# sqlite_to_csv(db_path, 'example_table', 'output.csv')

# # Load and print the CSV to verify
# df = pd.read_csv('output.csv')
# print(df)