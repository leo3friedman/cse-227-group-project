# from pathlib import Path
# import json
# import subprocess
# import shutil
# import tempfile

# # Optional project-specific utilities
# import repo_util as UTIL

# # Set up paths
# current_file = Path(__file__)
# links_path = current_file.parent.parent.parent / 'data' / 'scraped_links' / 'chrome_links.json'

# # Load GitHub -> Chrome Web Store mapping
# with open(links_path, 'r', encoding='utf-8') as f:
#     repo_links = json.load(f)

# # Define keywords to search in README
# KEYWORDS = {
#     "npm_install": ["npm install", "npm i"],
#     "npm_build": ["npm run build"],
#     "yarn_install": ["yarn install", "yarn", "yarn i"],
#     "yarn_build": ["yarn build", "yarn run build"]
# }

# def check_readme_for_package_manager_commands(repo_url: str):
#     temp_dir = tempfile.mkdtemp()
#     try:
#         subprocess.run(["git", "clone", "--depth=1", repo_url, temp_dir],
#                        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

#         # Find README.md (case-insensitive)
#         readme_path = None
#         for filename in ["README.md", "readme.md"]:
#             candidate = Path(temp_dir) / filename
#             if candidate.exists():
#                 readme_path = candidate
#                 break

#         if not readme_path:
#             return {key: False for key in KEYWORDS} | {"reason": "No README.md", "keep": False}

#         with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
#             content = f.read().lower()

#         result = {
#             key: any(keyword in content for keyword in KEYWORDS[key])
#             for key in KEYWORDS
#         }

#         has_install = result["npm_install"] or result["yarn_install"]
#         has_build = result["npm_build"] or result["yarn_build"]
#         should_keep = has_install and has_build

#         result["keep"] = should_keep
#         result["reason"] = None if should_keep else "Missing install or build command"
#         return result

#     except subprocess.CalledProcessError:
#         return {key: False for key in KEYWORDS} | {"reason": "Git clone failed", "keep": False}
#     except Exception as e:
#         return {key: False for key in KEYWORDS} | {"reason": str(e), "keep": False}
#     finally:
#         shutil.rmtree(temp_dir)

# results = {}
# for repo_url, extension_links in repo_links.items():
#     print(f"Checking {repo_url}...")
#     result = check_readme_for_package_manager_commands(repo_url)
#     if result.get("keep", False):
#         # Add the Chrome extension link(s) under a key like "chrome_links"
#         result["chrome_links"] = extension_links
#         results[repo_url] = result

# # Output results next to script
# output_path = current_file.parent / "readme_pm_keep_only_with_links.json"
# with open(output_path, "w", encoding="utf-8") as f:
#     json.dump(results, f, indent=2)

# print(f"Done. {len(results)} repos kept. Results saved to {output_path}")


import subprocess
import tempfile
import shutil
import json
from pathlib import Path

# Paths
current_file = Path(__file__)
input_json = current_file.parent.parent.parent / 'data' / 'scraped_links' / 'chrome_links.json'
output_json = current_file.parent / 'successful_builds.json'

# Load GitHub to Chrome Web Store mapping
with open(input_json, 'r', encoding='utf-8') as f:
    repo_links = json.load(f)

successful = {}

def try_build(repo_url):
    temp_dir = tempfile.mkdtemp()
    try:
        # Clone the repo
        subprocess.run(
            ['git', 'clone', '--depth=1', repo_url, temp_dir],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120  # 2-minute timeout
        )

        # Run npm install
        subprocess.run(
            ['npm', 'install'],
            cwd=temp_dir,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120  # 2-minute timeout
        )

        # Run npm run build
        subprocess.run(
            ['npm', 'run', 'build'],
            cwd=temp_dir,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120  # 2-minute timeout
        )

        return True
    except subprocess.TimeoutExpired:
        print(f"[Timeout] {repo_url} took too long")
        return False
    except subprocess.CalledProcessError:
        return False
    finally:
        shutil.rmtree(temp_dir)


# Main loop
for repo, chrome_links in repo_links.items():
    print(f"Trying: {repo}")
    if try_build(repo):
        successful[repo] = chrome_links

# Save results
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump(successful, f, indent=2)

print(f"\nDone. Successful builds: {len(successful)}")
print(f"Results saved to {output_json}")
