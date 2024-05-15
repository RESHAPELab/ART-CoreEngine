import requests


def get_github_file_content(repo_owner, repo_name, file_path, file_name):
    base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"
    url = f"{base_url}/{file_path}"

    response = requests.get(url)
    data = response.json()

    if isinstance(data, list):
        # If data is a list, it means it's a directory, so we need to navigate further
        for item in data:
            if item['type'] == 'dir':
                # Recursively navigate directories
                subdir_path = f"{file_path}/{item['name']}"
                content = get_github_file_content(repo_owner, repo_name, subdir_path, file_name)
                if content is not None:
                    return content
            elif item['type'] == 'file' and item['name'] == file_name:
                # If it's a file and matches our desired file name, fetch its content
                file_content_url = item['download_url']
                file_content_response = requests.get(file_content_url)
                file_content = file_content_response.text
                return file_content

# Example
# repo_owner = 'JabRef'
# repo_name = 'jabref'
# file_path = 'src/main/java/org/jabref/gui/contentselector'
# file_name = 'ContentSelectorDialogView.java'
#
# print(get_github_file_content(repo_owner, repo_name, file_path, file_name))