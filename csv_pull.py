import csv


def read_specific_column(filepath, column_name):
    with open(filepath, 'r') as file:
        csv_reader = csv.DictReader(file)
        column_values = []
        for row in csv_reader:
            column_values.append(row[column_name])
        return [column.split(',') for column in column_values]
# File path
# file_path = './issues_data2.csv'
# column_name = 'PR Files'


def pull_csv(file_path, column_name):
    column_data = read_specific_column(file_path, column_name)
    change_files = set()

    for column in column_data:
        for item in column:
            if item.endswith(".java'"):
                cleaned_item = item.replace('[', '').replace(']', '').replace("'", "")
                change_files.add(cleaned_item)
    return change_files

# for file in change_files:
#     print("Yippee: " + str(file))
