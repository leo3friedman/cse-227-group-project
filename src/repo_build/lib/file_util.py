import os
import json
import shutil
import tempfile
import zipfile
import subprocess
import argparse


def absolute_path(path_str):
    if not os.path.isabs(path_str):
        raise argparse.ArgumentTypeError(f"Path '{path_str}' is not an absolute path.")
    return path_str

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
    # Step 1: Remove existing target directory if it exists
    final_path = os.path.join(output_dir, target_dir_name)
    if os.path.isdir(final_path):
        shutil.rmtree(final_path)

    # Step 2: Extract to a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        extracted_items = os.listdir(tmpdir)

        # If there's only one folder, move it and rename
        if len(extracted_items) == 1 and os.path.isdir(os.path.join(tmpdir, extracted_items[0])):
            top_level_path = os.path.join(tmpdir, extracted_items[0])
            shutil.move(top_level_path, final_path)
        else:
            # Otherwise, make a new directory and move everything into it
            os.makedirs(final_path)
            for item in extracted_items:
                item_path = os.path.join(tmpdir, item)
                shutil.move(item_path, final_path)

    print(f"Unzipped and renamed to: {final_path}")


def find_refs_with_manifest_version(repo_path, refs, desired_version):
    if not os.path.isdir(repo_path):
        raise ValueError("Invalid repo path")

    # Save original HEAD to restore it later
    original_head = subprocess.run(
        ['git', 'rev-parse', 'HEAD'],
        cwd=repo_path, capture_output=True, text=True
    ).stdout.strip()

    matching_refs = []
    has_manifest = False
    for ref in refs:
        try:
            # Checkout the ref (tag or commit SHA)
            subprocess.run(
                ['git', 'checkout', '--quiet', '--detach', ref],
                cwd=repo_path, check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            # Find and read manifest.json
            manifest_path = find_manifest_json_file(repo_path)
            # print(manifest_path)
            if not manifest_path:
                continue
            # there is a manifest.json path!
            has_manifest = True
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                actual_version = data.get('version')
                # print(actual_version)

                if actual_version == desired_version:
                    matching_refs.append(ref)

        except Exception:
            continue  # Skip ref on error

    # Restore original HEAD
    subprocess.run(['git', 'checkout', '--quiet', original_head], cwd=repo_path, check=True)

    return matching_refs, has_manifest

# def checkout_git_ref(repo_path, ref_name):
#     subprocess.run(['git', 'checkout', ref_name], cwd=repo_path, check=True)
'''
inputs:
directory_of_reporistory: ex: /workspace/data/darkreader/darkreader

output:
list of directories that contain the manifest.json(top level): ex: /workspace/data/darkreader/darkreader/build/dist/chrome-mv3
'''
# def find_directories_with_min_version(directory_of_repository):
#     matching_directories = []

#     for root, dirs, files in os.walk(directory_of_repository):
#         # print(root)
#         if "manifest.json" in files:
#             manifest_path = os.path.join(root, "manifest.json")
#             try:
#                 # with open(manifest_path, "r") as f:
#                 #     manifest_data = json.load(f)
#                 if "minimum_chrome_version" in manifest_data:
#                     matching_directories.append(root)
#             except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
#                 print(f"Error reading {manifest_path}: {e}")

#     return matching_directories

# def find_directories_with_min_version(directory_of_repository):
#     with_min_version = []
#     without_min_version = []

#     for root, dirs, files in os.walk(directory_of_repository):
#         if "manifest.json" in files:
#             manifest_path = os.path.join(root, "manifest.json")
#             try:
#                 with open(manifest_path, "r", encoding="utf-8") as f:
#                     manifest_data = json.load(f)
#                 if "minimum_chrome_version" in manifest_data:
#                     with_min_version.append(root)
#                 else:
#                     without_min_version.append(root)
#             except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
#                 print(f"Error reading {manifest_path}: {e}")
    
#     return {
#         "with_min_version": with_min_version,
#         "without_min_version": without_min_version
#     }
import os

def find_directories_with_manifest_json(directory_of_repository):
    matching_directories = []

    for root, dirs, files in os.walk(directory_of_repository):
        if "manifest.json" in files:
            matching_directories.append(root)

    return matching_directories

'''
return:
(
manifest_directories - list of top level directories containing a manifest.json file
-- data if this reference is buildable
-- data if this reference had a timeout during building
-- 
)
'''
# def build_git_ref(repo_path, ref_name):
#     # print(f"repo path: {repo_path}")
#     # print(f"ref name: {ref_name}")
#     # Step 1: Checkout the git reference
#     try:
#         subprocess.run(['git', 'checkout', ref_name], cwd=repo_path, check=True)

#         # Step 2: Run npm install
#         subprocess.run(
#                 ['npm', 'install'],
#                 cwd=repo_path,
#                 check=True,
#                 stdout=subprocess.DEVNULL,
#                 stderr=subprocess.DEVNULL,
#                 timeout=120  # 2-minute timeout
#             )

#         '''
#         # Step 2: Run npm install
#     subprocess.run(['npm', 'install'], cwd=repo_path, check=True)

#     # Step 3: Run npm build
#     subprocess.run(['npm', 'run', 'build'], cwd=repo_path, check=True)
#         '''
#         # Step 3: Run npm build
#         subprocess.run(
#                 ['npm', 'run', 'build'],
#                 cwd=repo_path,
#                 check=True,
#                 stdout=subprocess.DEVNULL,
#                 stderr=subprocess.DEVNULL,
#                 timeout=120  # 2-minute timeout
#             )
#         # will return empty array if 
#         manifest_dirs = find_directories_with_min_version(repo_path)

#         return manifest_dirs
#     except subprocess.TimeoutExpired:
#         print(f"[Timeout] {ref_name} took too long")
#         return manifest_dirs
#     except subprocess.CalledProcessError:
#         print(f"[Commands Failed] {ref_name}")
#         return manifest_dirs
# def build_git_ref(repo_path, ref_name):
#     manifest_result = {
#         "with_min_version": [],
#         "without_min_version": []
#     }

#     try:
#         subprocess.run(['git', 'checkout', ref_name], cwd=repo_path, check=True)

#         subprocess.run(
#             ['npm', 'install'],
#             cwd=repo_path,
#             check=True,
#             stdout=subprocess.DEVNULL,
#             stderr=subprocess.DEVNULL,
#             timeout=120
#         )

#         subprocess.run(
#             ['npm', 'run', 'build'],
#             cwd=repo_path,
#             check=True,
#             stdout=subprocess.DEVNULL,
#             stderr=subprocess.DEVNULL,
#             timeout=120
#         )

#         # Analyze manifest.json files after build
#         manifest_result = find_directories_with_min_version(repo_path)

#         return {
#             "buildable": True,
#             "timeout": False,
#             "manifest_result": manifest_result
#         }

#     except subprocess.TimeoutExpired:
#         print(f"[Timeout] {ref_name} took too long")
#         return {
#             "buildable": False,
#             "timeout": True,
#             "manifest_result": manifest_result
#         }

#     except subprocess.CalledProcessError:
#         print(f"[Commands Failed] {ref_name}")
#         return {
#             "buildable": False,
#             "timeout": False,
#             "manifest_result": manifest_result
#         }
import subprocess

def build_git_ref(repo_path, ref_name):
    manifest_dirs = []

    try:
        subprocess.run(['git', 'checkout', ref_name], cwd=repo_path, check=True)

        subprocess.run(
            ['npm', 'install'],
            cwd=repo_path,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120
        )

        subprocess.run(
            ['npm', 'run', 'build'],
            cwd=repo_path,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120
        )

        # Check for presence of manifest.json files
        manifest_dirs = find_directories_with_manifest_json(repo_path)

        return manifest_dirs, True, False

    except subprocess.TimeoutExpired:
        print(f"[Timeout] {ref_name} took too long")
        manifest_dirs = find_directories_with_manifest_json(repo_path)
        return manifest_dirs, False, True

    except subprocess.CalledProcessError:
        print(f"[Commands Failed] {ref_name}")
        manifest_dirs = find_directories_with_manifest_json(repo_path)
        return manifest_dirs, False, False



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

def compare_dirs_with_diffoscope_recorded(path1, path2, output_path):
    # Run diffoscope and write its output directly to output_path
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(output_path)
    result = subprocess.run(
        ['diffoscope', '--exclude-directory-metadata=recursive',
         '--text', output_path, path1, path2],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )


def remove_chromex(path):
    """
    Removes the .git directory in the given path to uninitialize a Git repo.
    """
    shutil.rmtree(path)
    print(f"Removed directory from {path}")

def remove_file(path):
    """
    Removes the file at the given path.
    """
    if os.path.isfile(path):
        os.remove(path)