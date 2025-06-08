import json
from pathlib import Path
import dr_extract_dift as df  # contains extractor()
import os
import shutil

# Paths
current_file = Path(__file__)
input_json = current_file.parent.parent.parent / 'data' / 'scraped_metadata' / 'gh_linked_metadata.json'
output_json = current_file.parent / 'new_pipeline_update.json'
resume_log = current_file.parent / 'resume_log.txt'
pipeline_output_dir = Path("/workspace/pipeline_output")

# Output subdirectories to preserve
output_subdir1 = pipeline_output_dir / "output_text"
output_subdir2 = pipeline_output_dir / "output_html"
output_subdir3 = pipeline_output_dir / "output_parsed"
preserve_dirs = {output_subdir1, output_subdir2, output_subdir3}

# Clean the pipeline_output directory at script start
if pipeline_output_dir.exists() and pipeline_output_dir.is_dir():
    for item in pipeline_output_dir.iterdir():
        try:
            if item in preserve_dirs:
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except Exception as e:
            print(f"Warning: Failed to delete {item}: {e}")

# Load metadata
if output_json.exists():
    with open(output_json, 'r') as f:
        metadata = json.load(f)
else:
    with open(input_json, 'r') as f:
        metadata = json.load(f)

# Load resume point
start_index = 0
if resume_log.exists():
    with open(resume_log, 'r') as f:
        try:
            start_index = int(f.read().strip())
        except ValueError:
            pass

# Get GitHub token
token = os.getenv("GITHUB_TOKEN")
github_username = os.getenv("GITHUB_USERNAME")

# Flatten the dict into list of tuples [(cws_url, metadata_dict)]
metadata_items = list(metadata.items())

# Process from the resume point
for i in range(start_index, len(metadata_items)):
    cws_url, data = metadata_items[i]
    repo_url = data.get("repo_url")
    user_count = data.get("user_count")
    print(f"Index {i}: user_count = {user_count} (type: {type(user_count)})")
    # Safely convert user_count to int
    try:
        user_count_int = int(user_count)
    except (TypeError, ValueError):
        print(f"Warning: Invalid user_count ({user_count}) for {cws_url}, treating as 0")
        user_count_int = 0

    # Skip if user count is less than 10,000
    if user_count_int < 10000:
        with open(resume_log, 'w') as f:
            f.write(str(i + 1))
        continue

    try:
        buildable, timeout, target_version_match, has_manifest, exist = df.extractor(
            github_link=repo_url,
            path=str(pipeline_output_dir),
            crx_link=cws_url,
            github_username=github_username,
            token=token
        )

        data["buildable"] = buildable
        data["timeout"] = timeout
        data["target_version_match"] = target_version_match
        data["has_manifest"] = has_manifest
        data["exist"] = exist

    except Exception as e:
        print(f"Error processing index {i} — {repo_url} / {cws_url}: {e}")
        with open(resume_log, 'w') as f:
            f.write(str(i + 1))
        continue

    # Update resume log
    with open(resume_log, 'w') as f:
        f.write(str(i + 1))

    # Update output JSON
    with open(output_json, 'w') as f:
        json.dump(metadata, f, indent=4)

    print(f"Finished index {i}: {cws_url}")

print(f"All processed (or resumed) and written to {output_json}")
