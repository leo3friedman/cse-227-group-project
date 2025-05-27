from pathlib import Path
import lib.git_util as GIT_UTIL

current_file = Path(__file__)
darkreader_path = current_file.parent.parent.parent / 'data' / 'darkreader'
git_path = darkreader_path / 'darkreader'
print(git_path)
GIT_UTIL.remove_git_repo(git_path)