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


# Example usage:
# csv_file = 'data.csv'
# key_name = input("Enter key name to check and possibly add: ")
# description = input("Enter description: ")
#
# add_to_csv(csv_file, key_name, description)
# print(get_from_csv('function_storage.csv', 'java.util.List'))