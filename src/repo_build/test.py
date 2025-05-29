# import lib.diff_util as DIFF_UTIL
import lib.git_crx as CRX_UTIL
import lib.file_util as FILE_UTIL
import lib.git_util as GIT_UTIL
import re
# DIFF_UTIL.compare_dirs_with_diffoscope_recorded("./diff_parser.py", "./dr-extract_dift.py", "./outputs/text.txt")
# a = CRX_UTIL.fetch_extension_zip("https://chromewebstore.google.com/detail/dark-reader/eimadpbcbfnmbkopoojfekhnkhdbieeh", 
#                               output_base_dir= "./outputs")
# print(a)
# FILE_UTIL.unzip_and_rename_top_folder(a, "hello", output_dir="./outputs")


username, reponame = GIT_UTIL.get_user_repo("https://github.com/mrsafacon/TwitchChatToggle-ChromeExtension")

print(username)
print(reponame)