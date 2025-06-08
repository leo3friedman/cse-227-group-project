import requests
import os
import shutil
import subprocess
import re
import time

def get_headers(token=None):
    if token:
        return {'Authorization': f'token {token}'}
    else:
        return {}

# Gets all releases, supports optional token
def get_github_releases(repo_owner, repo_name, token=None):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
    headers = get_headers(token)
    response = requests.get(url, headers=headers)
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

def get_default_branch(repo_owner, repo_name, token=None):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    headers = get_headers(token)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['default_branch']

def get_github_commits(repo_owner, repo_name, branch=None, per_page=100, max_pages=10, token=None):
    headers = get_headers(token)

    if branch is None:
        branch = get_default_branch(repo_owner, repo_name, token=token)

    commits = []
    for page in range(1, max_pages + 1):
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"
        params = {
            'sha': branch,
            'per_page': per_page,
            'page': page
        }

        while True:
            response = requests.get(url, params=params, headers=headers)

            if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
                reset_time = int(response.headers.get("X-RateLimit-Reset", time.time()))
                sleep_duration = max(reset_time - int(time.time()), 0) + 1
                print(f"Rate limit exceeded. Sleeping for {sleep_duration} seconds...")
                time.sleep(sleep_duration)
                continue

            try:
                response.raise_for_status()
                break
            except requests.exceptions.HTTPError as e:
                print(f"HTTP error on page {page}: {e}")
                return commits

        page_commits = response.json()
        if not page_commits:
            break

        for commit in page_commits:
            commits.append({
                'sha': commit['sha'],
                'author': commit['commit']['author']['name'],
                'date': commit['commit']['author']['date'],
                'message': commit['commit']['message'],
                'url': commit['html_url']
            })

        time.sleep(1)  # Be kind to GitHub's API

    return commits

# Git clones repo (no token needed)
def get_git_clone(user, repo_name, repo_location, github_user, github_token):
    repo_url = f"https://{github_user}:{github_token}@github.com/{user}/{repo_name}.git"
    destination_path = repo_location
    print(f"Cloning repo: {repo_name} from {repo_url} into {destination_path}")

    try:
        subprocess.run(["git", "clone", repo_url, destination_path], check=True)
        print("Clone successful.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to clone repository. Error: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


# Removes the git repo after usage
def remove_git_repo(path):
    git_dir = os.path.join(path, '.git')
    if os.path.isdir(git_dir):
        shutil.rmtree(path)
        print(f"Removed Git repository from {path}")
    else:
        print(f"No Git repository found in {path}")

def get_user_repo(url):
    match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if match:
        username = match.group(1)
        repo = match.group(2)
        return (username, repo)
    else:
        return None
