import os
import sys
import json
import glob


def combine_chrome_links(extract_dir: str) -> None:
    # Combine chrome_links batches 
    combined_links: dict[str, list[str]] = {}
    links_pattern = os.path.join(extract_dir, "chrome_links_*_*.json")
    for filepath in glob.glob(links_pattern):
        filename = os.path.basename(filepath)
        if filename in ("chrome_links.json", "chrome_links_noext.json"): continue
        if filename.startswith("chrome_links_noext_"): continue
        with open(filepath, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: skipping invalid JSON {filename}")
                continue
        for repo, links in data.items():
            if repo in combined_links:
                seen = set(combined_links[repo])
                for link in links:
                    if link not in seen:
                        combined_links[repo].append(link)
                        seen.add(link)
            else:
                combined_links[repo] = list(links)

    # Combine chrome_links_noext batches 
    combined_noext: list[str] = []
    noext_pattern = os.path.join(extract_dir, "chrome_links_noext_*_*.json")
    for filepath in glob.glob(noext_pattern):
        filename = os.path.basename(filepath)
        if filename in ("chrome_links_noext.json", "chrome_links.json"): continue
        with open(filepath, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: skipping invalid JSON {filename}")
                continue
        combined_noext.extend(data)
    combined_noext = list(dict.fromkeys(combined_noext))

    # Write combined outputs 
    out_links = os.path.join(extract_dir, "chrome_links.json")
    out_noext = os.path.join(extract_dir, "chrome_links_noext.json")
    with open(out_links, 'w') as f:
        json.dump(combined_links, f, indent=2)
    with open(out_noext, 'w') as f:
        json.dump(combined_noext, f, indent=2)

    print(f"Combined chrome_links.json entries: {len(combined_links)} repos")
    print(f"Combined chrome_links_noext.json entries: {len(combined_noext)} repos")

    # Determine remaining repos
    github_links_file = os.path.join(extract_dir, 'github_links.json')
    if os.path.isfile(github_links_file):
        with open(github_links_file, 'r') as f:
            try:
                all_repos = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: could not parse {github_links_file}")
                return
        # repos not in either combined set
        remaining = [r for r in all_repos if r not in combined_links and r not in combined_noext]
        # write remaining file
        out_remaining = os.path.join(extract_dir, 'chrome_links_remaining.json')
        with open(out_remaining, 'w') as f:
            json.dump(remaining, f, indent=2)
        print(f"Remaining repos (not in chrome_links or chrome_links_noext): {len(remaining)} entries")
    else:
        print(f"No github_links.json found in {extract_dir}, skipping remaining list.")


def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    extract_dir = os.path.join(BASE_DIR, 'extracted_urls')
    if not os.path.isdir(extract_dir):
        print(f"Error: directory not found: {extract_dir}")
        return
    combine_chrome_links(extract_dir)
    print(f"Combined JSON files saved in {extract_dir}:")
    print("  - chrome_links.json")
    print("  - chrome_links_noext.json")
    print("  - chrome_links_remaining.json")


if __name__ == '__main__':
    main()
