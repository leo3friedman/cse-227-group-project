# import zipfile
# import os
# import subprocess
from pathlib import Path
import repo_util as UTIL
import sys

# Unzip dark reader
current_file = Path(__file__)
darkreader_path = current_file.parent.parent.parent / 'data' / 'darkreader'
zip_path = darkreader_path + "/darkreader-dist.zip"

# TODO: Notice that we assume git is already pulled
git_path = darkreader_path + './darkreader'

### Extract chromex and get version

# Extracting chromex
extractname = "chromex_data"
UTIL.unzip_and_rename_top_folder(zip_path, extractname)

# Getting version number
chromex_path = darkreader_path + "/chromex_data"
# manifest_paths = UTIL.find_manifest_json_files(chromex_path)
# Get first manifest (assumes there is just one in chromex)
manifest_path = UTIL.find_manifest_json_file(chromex_path)


## TODO: Use all targeted versions or single out best one from possible manifest_paths
# target_versions = []
# for manifest_path in manifest_paths:
#   target_versions.append(UTIL.extract_version_from_manifest(manifest_path))
# print(target_versions[0])
target_version = UTIL.extract_version_from_manifest(manifest_path)

# output = UTIL.get_all_git_branches(git_path)
# print(output)

### Get all possible releases and check which ones have correct version number
releases = UTIL.get_github_releases("darkreader", "darkreader")
tag_versions = [r['tag_name'] for r in releases]
print("Target version: ",target_version)

# possible_branches = UTIL.find_tags_with_manifest_version(git_path, tag_versions, target_versions[0])
possible_branches = UTIL.find_tags_with_manifest_version(git_path, tag_versions, target_version)
print("Possible branches: ")
print(possible_branches)

### 
for branch in possible_branches:
  # TODO: Instead of forcing to build folder, just search for all instances of manifests
  # TODO: Look for only chrome (find some defining feature)
  built_locations = UTIL.build_git_ref(git_path, branch, 'build')
  min_length = sys.maxsize
  bestbuild = ""
  for build in built_locations:
    release_path = git_path + "/" + build
    diff_data, diff_len = UTIL.compare_dirs_with_diffoscope(chromex_path, release_path)
    if diff_len < min_length:
      min_length = diff_len
      bestbuild = release_path
  print((bestbuild, min_length))

# # Clone repo etc


# # Build chromex

# # command = ["npm", "run", "build"]

# # Compare using diffoscope
# # "diffoscope --exclude-directory-metadata=recursive --html diff.html Dark-Reader/ darkreader/build/release/chrome-mv3/"
# command = ["diffoscope", "--exclude-directory-metadata=recursive", "--html diff.html", "Dark-Reader/", "darkreader/build/release/chrome-mv3/"]