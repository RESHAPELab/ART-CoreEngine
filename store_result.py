import csv
import os


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
