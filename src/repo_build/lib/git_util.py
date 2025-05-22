import requests
import os
import json
import shutil
import tempfile
import zipfile
import subprocess

# Gets all releases
def get_github_releases(repo_owner, repo_name):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
    response = requests.get(url)
    response.raise_for_status()  # Raise an error on bad status

    releases = response.json()
    return [{
        'tag_name': r['tag_name'],
        'name': r.get('name'),
        'published_at': r['published_at'],
        'draft': r['draft'],
        'prerelease': r['prerelease'],
        'url': r['html_url']
    } for r in releases]

# Git clones repo
def get_git_clone(user, repo_name, repo_location):
  repo_url = "https://github.com/" + user + "/" + repo_name + ".git"
  destination_path = repo_location
  print(repo_name)

  subprocess.run(["git", "clone", repo_url, destination_path], check=True)

# Removes the git repo after usage
def remove_git_repo(path):
    """
    Removes the .git directory in the given path to uninitialize a Git repo.
    """
    git_dir = os.path.join(path, '.git')
    if os.path.isdir(git_dir):
        shutil.rmtree(path)
        print(f"Removed Git repository from {path}")
    else:
        print(f"No Git repository found in {path}")