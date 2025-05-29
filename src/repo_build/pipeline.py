import json
from pathlib import Path
import dr_extract_dift as df  # contains extractor()
import os

# Paths
current_file = Path(__file__)
input_json = current_file.parent.parent.parent / 'data' / 'scraped_metadata' / 'metadata.json'
output_json = current_file.parent / 'pipeline_update.json'
resume_log = current_file.parent / 'resume_log.txt'

# Load metadata (resume from output if exists)
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
            pass  # if file is empty or invalid, default to 0

# Get GitHub token
token = os.getenv("GITHUB_TOKEN")

# Process from the resume point
for i in range(start_index, len(metadata)):
    entry = metadata[i]
    repo_url = entry.get("repo_url")
    scraped_list = entry.get("scraped_metadata", [])

    for scraped in scraped_list:
        cws_url = scraped.get("cws_url")

        try:
            buildable, timeout, target_version_match, has_manifest = df.extractor(
                repo_url,
                "/workspace/pipeline_output",
                cws_url,
                token=token
            )

            scraped["buildable"] = buildable
            scraped["timeout"] = timeout
            scraped["target_version_match"] = target_version_match
            scraped["has_manifest"] = has_manifest

        except Exception as e:
            print(f"Error processing index {i} — {repo_url} / {cws_url}: {e}")
            continue  # skip failed cws entry, move to next

    # After processing each entry:
    # 1. Update resume log
    with open(resume_log, 'w') as f:
        f.write(str(i + 1))  # next index to process

    # 2. Update output JSON with progress
    with open(output_json, 'w') as f:
        json.dump(metadata, f, indent=4)

    print(f"Finished index {i}")

print(f"All processed (or resumed) and written to {output_json}")
