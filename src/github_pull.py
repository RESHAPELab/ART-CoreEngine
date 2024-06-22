import requests


def get_github_single_file(repo_owner : str, repo_name : str, commit : str, file_path : str, download_to : str):
    """Download file from github

    Args:
        repo_owner (str): Repo Owner
        repo_name (str): Repo Name
        commit (str): Commit
        file_path (str): File path with file name
        download_to (str): download location. Relative to CWD

    Raises:
        ValueError: Network or Download Failure.
    """
    base_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}"
    url = f"{base_url}/{commit}/{file_path}"

    response = requests.get(url)
    if(response.ok and response.status_code == 200):
        f = open(download_to, "wb")
        f.write(response.content)
        f.close()
    else:
        raise ValueError(f"Network Failed to Download File! Code: {response.status_code}")

    

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
