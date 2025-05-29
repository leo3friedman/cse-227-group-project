import json
from pathlib import Path
import tempfile
import dr_extract_dift as df  # contains extractor()
import os

# Paths
current_file = Path(__file__)
input_json = current_file.parent.parent.parent / 'data' / 'scraped_metadata' / 'metadata.json'
output_json = current_file.parent / 'pipeline_update.json'

# Load data
with open(input_json, 'r') as f:
    metadata = json.load(f)

# Get token once
token = os.getenv("GITHUB_TOKEN")

for entry in metadata:
    repo_url = entry.get("repo_url")
    scraped = entry.get("scraped_metadata", [])
    cws_url = scraped[0].get("cws_url") if scraped else None

    buildable, timeout, target_version_match = df.extractor(repo_url, "/workspace/pipeline_output", cws_url, token=token)

    entry["buildable"] = buildable
    entry["timeout"] = timeout
    entry["target_version_match"] = target_version_match

# Save updated results
with open(output_json, 'w') as f:
    json.dump(metadata, f, indent=4)

print(f"Written to {output_json}")
