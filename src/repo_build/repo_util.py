import requests
import os
import json
import shutil
import tempfile
import zipfile
import subprocess
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

def find_manifest_json_files(start_path):
    manifest_files = []
    for root, dirs, files in os.walk(start_path):
        if 'manifest.json' in files:
            manifest_files.append(os.path.join(root, 'manifest.json'))
    return manifest_files

def find_manifest_json_file(start_path):
    outp = find_manifest_json_files(start_path)
    if len(outp) > 0: 
      return find_manifest_json_files(start_path)[0]
    else:
      return None

def extract_version_from_manifest(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('version')  # Returns None if 'version' key is missing
    except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
        print(f"Error reading {file_path}: {e}")
        return None


def unzip_and_rename_top_folder(zip_path, target_dir_name, output_dir='.'):
    # Step 1: Extract to a temp location
    if os.path.isdir(output_dir + "/" + target_dir_name):
      shutil.rmtree(output_dir + "/" + target_dir_name)
      print("Path replaced")
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        # Step 2: Find the top-level folder
        extracted_items = os.listdir(tmpdir)
        top_level_path = os.path.join(tmpdir, extracted_items[0])  # assumes 1 top-level item

        # Step 3: Define the final destination path
        final_path = os.path.join(output_dir, target_dir_name)

        # Step 4: Move and rename the folder
        shutil.move(top_level_path, final_path)

        print(f"Unzipped and renamed to: {final_path}")


def find_tags_with_manifest_version(repo_path, tags, desired_version):
    if not os.path.isdir(repo_path):
        raise ValueError("Invalid repo path")

    original_head = subprocess.run(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        cwd=repo_path, capture_output=True, text=True
    ).stdout.strip()
    # subprocess.run(['git', 'checkout', original_head], cwd=repo_path, check=True)

    matching_tags = []

    for tag in tags:
        try:
            # Checkout the tag
            subprocess.run(['git', 'checkout', tag], cwd=repo_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Find manifest.json
            manifest_path = find_manifest_json_file(repo_path)
            if not manifest_path:
                continue

            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                actual_version = data.get('version')

                if actual_version == desired_version:
                    print("Check: ")
                    print((tag, actual_version, desired_version))
                    matching_tags.append(tag)

        except Exception:
            pass  # skip tag on error

    # Restore original HEAD
    subprocess.run(['git', 'checkout', original_head], cwd=repo_path, check=True)

    return matching_tags

# def checkout_git_ref(repo_path, ref_name):
#     subprocess.run(['git', 'checkout', ref_name], cwd=repo_path, check=True)


def build_git_ref(repo_path, ref_name, build_dir='dist'):
    # Step 1: Checkout the git reference
    subprocess.run(['git', 'checkout', ref_name], cwd=repo_path, check=True)

    # Step 2: Run npm install
    subprocess.run(['npm', 'install'], cwd=repo_path, check=True)

    # Step 3: Run npm build
    subprocess.run(['npm', 'run', 'build'], cwd=repo_path, check=True)

    # Step 4: Find files in the build directory
    full_build_path = os.path.join(repo_path, build_dir)
    if not os.path.exists(full_build_path):
        raise FileNotFoundError(f"Build directory '{full_build_path}' not found.")

    manifest_dirs = []
    for root, _, files in os.walk(full_build_path):
        if 'manifest.json' in files:
            manifest_dirs.append(os.path.relpath(root, repo_path))

    return manifest_dirs


def compare_dirs_with_diffoscope(path1, path2):
    with tempfile.NamedTemporaryFile(delete=False) as diff_file:
        result = subprocess.run(
            ['diffoscope', '--exclude-directory-metadata=recursive',
             '--text', diff_file.name, path1, path2],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        with open(diff_file.name, 'r') as f:
            diff_content = f.read()
        os.unlink(diff_file.name)
        return diff_content, len(diff_content)
# import subprocess
# import os
# def get_all_git_branches(repo_path):
#     if not os.path.isdir(repo_path):
#         raise ValueError(f"Path '{repo_path}' does not exist or is not a directory.")

#     # Ensure it's a Git repo
#     if not os.path.isdir(os.path.join(repo_path, '.git')):
#         raise ValueError(f"Path '{repo_path}' is not a Git repository.")

#     # Fetch remote branches
#     subprocess.run(['git', 'fetch', '--all'], cwd=repo_path, check=True)

#     # Get local branches
#     local_branches = subprocess.run(
#         ['git', 'branch'],
#         cwd=repo_path,
#         capture_output=True,
#         text=True,
#         check=True
#     ).stdout.strip().split('\n')

#     local_branches = [branch.strip().lstrip('* ') for branch in local_branches]

#     # Get remote branches
#     remote_branches = subprocess.run(
#         ['git', 'branch', '-r'],
#         cwd=repo_path,
#         capture_output=True,
#         text=True,
#         check=True
#     ).stdout.strip().split('\n')

#     remote_branches = [branch.strip() for branch in remote_branches]

#     return {
#         'local': local_branches,
#         'remote': remote_branches
#     }
