# import zipfile
# import os
# import subprocess
from pathlib import Path
import lib.file_util as FILE_UTIL
import lib.git_util as GIT_UTIL
import lib.diff_util as DIFF_UTIL
import sys
import argparse

parser = argparse.ArgumentParser(description="Script that takes exactly 3 strings")
parser.add_argument("inputs", nargs=3, type=str, help="3 input strings")
args = parser.parse_args()
input1, input2, input3 = args.inputs
print(f"Repo name: {input1}")
print(f"username: {input2}")
print(f"Third input: {input3}")

# File locations
current_file = Path(__file__)
darkreader_path = current_file.parent.parent.parent / 'data' / 'darkreader'
zip_path = darkreader_path / "./darkreader-dist.zip"
print(f"zip path: {zip_path}")

git_path = darkreader_path / input1
print(f"git path: {git_path}")
GIT_UTIL.get_git_clone(input2, input1, darkreader_path / input1)


# Extracting chromex
# This puts it in wherever you are running the program from
extractname = "chromex_data"
FILE_UTIL.unzip_and_rename_top_folder(zip_path, extractname)

# Getting version number
chromex_path = "./chromex_data"
# manifest_paths = UTIL.find_manifest_json_files(chromex_path)
# Get first manifest (assumes there is just one in chromex)
manifest_path = FILE_UTIL.find_manifest_json_file(chromex_path)
print(f"manifest path: {manifest_path}")

## TODO: Use all targeted versions or single out best one from possible manifest_paths
# target_versions = []
# for manifest_path in manifest_paths:
#   target_versions.append(UTIL.extract_version_from_manifest(manifest_path))
# print(target_versions[0])
target_version = FILE_UTIL.extract_version_from_manifest(manifest_path)


### Get all possible releases and check which ones have correct version number
releases = GIT_UTIL.get_github_releases("darkreader", "darkreader")
tag_versions = [r['tag_name'] for r in releases]
print("Target version: ",target_version)

# possible_branches = UTIL.find_tags_with_manifest_version(git_path, tag_versions, target_versions[0])
possible_branches = FILE_UTIL.find_tags_with_manifest_version(git_path, tag_versions, target_version)
print("Possible branches: ")
print(possible_branches)


bestbuild = ""
### 
for branch in possible_branches:
  built_locations = FILE_UTIL.build_git_ref(git_path, branch)
  min_length = sys.maxsize
  for build in built_locations:
    release_path = git_path / build
    diff_data, diff_len = DIFF_UTIL.compare_dirs_with_diffoscope(chromex_path, release_path)
    if diff_len < min_length:
      min_length = diff_len
      bestbuild = release_path
  print((bestbuild, min_length))

DIFF_UTIL.compare_dirs_with_diffoscope_recorded(chromex_path, bestbuild, "./diff_output.txt")
GIT_UTIL.remove_git_repo(git_path)



# # Compare using diffoscope
# # "diffoscope --exclude-directory-metadata=recursive --html diff.html Dark-Reader/ darkreader/build/release/chrome-mv3/"
# command = ["diffoscope", "--exclude-directory-metadata=recursive", "--html diff.html", "Dark-Reader/", "darkreader/build/release/chrome-mv3/"]