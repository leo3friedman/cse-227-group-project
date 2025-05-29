import json
from pathlib import Path
import tempfile
import dr_extract_dift as df  # contains extractor()

# Paths
current_file = Path(__file__)
input_json = current_file.parent.parent.parent / 'data' / 'scraped_metadata' / 'metadata.json'
output_json = current_file.parent / 'pipeline_update.json'

# Load data
with open(input_json, 'r') as f:
    metadata = json.load(f)

for entry in metadata:
    repo_url = entry.get("repo_url")
    scraped = entry.get("scraped_metadata", [])
    cws_url = scraped[0].get("cws_url")

    buildable, timeout, has_manifest = df.extractor(repo_url, "/workspace/pipeline_output", cws_url)

    entry["buildable"] = buildable
    entry["timeout"] = timeout
    entry["has_manifest"] = has_manifest

# Save updated results
with open(output_json, 'w') as f:
    json.dump(metadata, f, indent=4)

print(f"Written to {output_json}")
