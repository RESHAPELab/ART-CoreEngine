import csv
import csv_push


def read_specific_column(filepath, column_name):
    with open(filepath, 'r') as file:
        csv_reader = csv.DictReader(file)
        column_values = []
        for row in csv_reader:
            column_values.append(row[column_name])
        return [column.split(',') for column in column_values]


def read_full_column(filepath, column_name):
    with open(filepath, 'r') as file:
        csv_reader = csv.DictReader(file)
        column_values = []
        for row in csv_reader:
            column_values.append(row[column_name])
        return [column for column in column_values]
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

def update_csv_with_results(file_path, column_name, results):
    with open(file_path, 'r') as file:
        csv_reader = csv.DictReader(file)
        fieldnames = csv_reader.fieldnames + ['Result']  # Add 'Result' as a new field
        rows = []
        for row in csv_reader:
            row['Result'] = results.pop(0)  # Add result to the row
            rows.append(row)

    with open(file_path, 'w', newline='') as file:
        csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_writer.writerows(rows)


# column_data = read_full_column('issues_data2.csv', 'PR Files')
# results = []
#
# for file in column_data:
#     # Convert the string to an actual array
#     array = eval(file)
#     array_of_javas = []
#     for input in array:
#         if input.endswith(".java"):
#             array_of_javas.append(input)
#
#     array_of_results = []
#     for java_file in array_of_javas:
#         result = csv_push.find_values_by_filename('test.csv', java_file)
#         if isinstance(result, tuple):
#             domains, subdomains = result
#             array_of_results.append("{" + java_file + ": [" + domains + "], [" + subdomains + "]}")
#         else:
#             array_of_results.append(result)
#     results.append(array_of_results)
#
# update_csv_with_results('issues_data2 test.csv', 'PR Files', results)
    # print(array[0])
    #
    # # Print the array
    # print("Yippee: " + str(array))
