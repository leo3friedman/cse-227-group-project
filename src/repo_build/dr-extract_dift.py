# import zipfile
# import os
# import subprocess
from pathlib import Path
import lib.file_util as FILE_UTIL
import lib.git_util as GIT_UTIL
import lib.diff_util as DIFF_UTIL
import lib.git_crx as CRX_UTIL
import sys
import argparse


def extractor(github_link, path, crx_link):
  git_output = GIT_UTIL.get_user_repo(github_link)
  if git_output == None:
    print("Failed")
    return
  else:
    username, reponame = git_output
  print(f"Absolute path: {path}")
  print(f"Username: {username}")
  print(f"Reponame: {reponame}")
  print(f"Zipfile link: {crx_link}")

  # Loading in zip location
  zip_path = CRX_UTIL.fetch_extension_zip(crx_link, 
                                output_base_dir= path)
  print(f"Zip path: {zip_path}")
  # File locations
  git_path = path + "/" + reponame
  # print(f"git path: {git_path}")
  GIT_UTIL.get_git_clone(username, reponame, git_path)


  # Extracting chromex
  # This puts it in wherever you are running the program from
  extractname = "chromex_data"
  FILE_UTIL.unzip_and_rename_top_folder(zip_path, extractname, output_dir = path)

  # Getting version number
  chromex_path = path + "/chromex_data"
  # manifest_paths = UTIL.find_manifest_json_files(chromex_path)
  # Get first manifest (assumes there is just one in chromex)
  manifest_path = FILE_UTIL.find_manifest_json_file(chromex_path)
  # print(f"manifest path: {manifest_path}")

  ## TODO: Use all targeted versions or single out best one from possible manifest_paths
  # target_versions = []
  # for manifest_path in manifest_paths:
  #   target_versions.append(UTIL.extract_version_from_manifest(manifest_path))
  # print(target_versions[0])
  target_version = FILE_UTIL.extract_version_from_manifest(manifest_path)


  ### Get all possible releases and check which ones have correct version number
  releases = GIT_UTIL.get_github_releases(username, reponame)
  tag_versions = [r['tag_name'] for r in releases]
  if tag_versions:
    print("Found releases")
  else:
    print("No releases, using commits")
    commits = GIT_UTIL.get_github_commits(username, reponame)
    tag_versions = [c['sha'] for c in commits]
    # print(tag_versions)
  # print("Target version: ",target_version)

  # possible_branches = UTIL.find_tags_with_manifest_version(git_path, tag_versions, target_versions[0])
  possible_branches = FILE_UTIL.find_refs_with_manifest_version(git_path, tag_versions, target_version)
  # print("Possible branches: ")
  # print(possible_branches)


  bestbuild = ""
  ### 
  for branch in possible_branches:
    built_locations = FILE_UTIL.build_git_ref(git_path, branch)
    min_length = sys.maxsize
    for build in built_locations:
      release_path = build
      diff_data, diff_len = DIFF_UTIL.compare_dirs_with_diffoscope(chromex_path, release_path)
      if diff_len < min_length:
        min_length = diff_len
        bestbuild = release_path
    print((bestbuild, min_length))

  DIFF_UTIL.compare_dirs_with_diffoscope_recorded(chromex_path, bestbuild, path + "/output/" + username + "_" + reponame + ".txt")

  # Clean up
  GIT_UTIL.remove_git_repo(git_path)
  FILE_UTIL.remove_chromex(chromex_path)


parser = argparse.ArgumentParser(description="Script that takes 1 absolute path, git username, git repo name, and chromex zipfile")
parser.add_argument("path", type=FILE_UTIL.absolute_path, help="Absolute file path")
parser.add_argument("github_link", type=str, help="Github repo link")
parser.add_argument("crx_link", type=str, help="Crx website")
args = parser.parse_args()
extractor(args.github_link, args.path, args.crx_link)