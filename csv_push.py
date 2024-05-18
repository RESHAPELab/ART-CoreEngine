import csv


def find_values_by_filename(csv_file, filename):
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file, delimiter=',')

        # Check if 'filename' exists in the fieldnames
        if 'filename' not in reader.fieldnames:
            return "Column 'filename' not found in the CSV file"

        # Iterate over each row
        for row in reader:
            # Check if the filename contains the given filename
            if filename in row['filename']:
                return row['domains'], row['subdomains']


        # If the filename is not found
        return filename + " not found"


# Example usage
# csv_file = 'test.csv'
# filename_to_find = 'src/main/java/org/jabref/gui/entryeditor/fileannotationtab/FileAnnotationTab.java'
# result = find_values_by_filename(csv_file, filename_to_find)
#
# if isinstance(result, tuple):
#     domains, subdomains = result
#     print("{" + filename_to_find + ": [" + domains + "], [" + subdomains + "]}")
# else:
#     print(result)
