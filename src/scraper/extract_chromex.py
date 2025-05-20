import os
import sys
import json
import asyncio
import aiohttp
import re
from urllib.parse import urlparse
from typing import List, Optional, Tuple

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SECRET_PATH = os.path.join(BASE_DIR, "secret.json")
LINKS_PATH = os.path.join(BASE_DIR, "extracted_urls", "github_links.json")

# Load GitHub token
with open(SECRET_PATH) as f:
    token = json.load(f)["github_access_token"]
HEADERS = {
    "Authorization": f"token {token}",
    "Content-Type": "application/json"
}

# Regex to find Chrome Web Store links
CHROME_LINK_RE = re.compile(
    r'https?://(?:chrome\.google\.com/webstore/detail/[^\s)]+|chromewebstore\.google\.com/[^\s)]+)'
)

# Progress bar
def print_progress(current: int, total: int, bar_length: int = 40) -> None:
    percent = current / total if total else 1
    filled_len = int(bar_length * percent)
    bar = '=' * filled_len + '-' * (bar_length - filled_len)
    sys.stdout.write(f"\rProgress: [{bar}] {current}/{total}")
    sys.stdout.flush()

# Extract owner and repo from GitHub URL
def repo_from_url(url: str) -> Tuple[str, str]:
    parts = urlparse(url).path.strip("/\n").split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {url}")
    return parts[0], parts[1]

# GraphQL query for manifest and README entries
GQL_QUERY = """
query($owner:String!,$name:String!){
  repository(owner:$owner,name:$name){
    manifest: object(expression: "HEAD:manifest.json") { ... on Blob { byteSize } }
    root: object(expression: "HEAD:") {
      ... on Tree { entries { name object { ... on Blob { text } } } }
    }
  }
}
"""

# Extract Chrome Web Store links from text
def extract_links_from_text(text: str) -> List[str]:
    return list(dict.fromkeys(CHROME_LINK_RE.findall(text)))

# Handle rate limit exceeded and exit
def handle_rate_limit(resp: aiohttp.ClientResponse, repo_url: str):
    if resp.status == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
        reset = resp.headers.get("X-RateLimit-Reset")
        print(f"\nRate limit reached for {repo_url}, reset at {reset}")
        sys.exit(1)

# Fetch manifest and README via GraphQL and extract links
async def fetch_and_extract(session: aiohttp.ClientSession, repo_url: str) -> Tuple[str, Optional[List[str]]]:
    owner, name = repo_from_url(repo_url)
    payload = {"query": GQL_QUERY, "variables": {"owner": owner, "name": name}}
    async with session.post("https://api.github.com/graphql", json=payload, headers=HEADERS) as resp:
        handle_rate_limit(resp, repo_url)
        if resp.status != 200:
            print(f"HTTP {resp.status} for {repo_url}")
            return repo_url, None
        data = await resp.json()
        if "errors" in data:
            for err in data["errors"]:
                if err.get("type") == "RATE_LIMITED":
                    reset = resp.headers.get("X-RateLimit-Reset")
                    print(f"Rate limit reached for {repo_url}, reset at {reset}")
                    sys.exit(1)
            return repo_url, None
        repo_data = data.get("data", {}).get("repository", {})
        # skip repos without manifest
        if not repo_data.get("manifest"):
            return repo_url, None
        # scan all README-like entries for links
        for entry in repo_data.get("root", {}).get("entries", []):
            name_lower = entry.get("name", "").lower()
            if name_lower.startswith("readme"):
                blob = entry.get("object") or {}
                text = blob.get("text", "") or ""
                links = extract_links_from_text(text)
                if links:
                    return repo_url, links
        # manifest exists but no links found
        return repo_url, []

# Main function
async def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Scrape Chrome extension links with slicing and indexed outputs"
    )
    parser.add_argument(
        "--start", type=int, default=0,
        help="Start index (0-based) of repos list"
    )
    parser.add_argument(
        "--end", type=int, default=None,
        help="End index (exclusive) of repos list"
    )
    args = parser.parse_args()

    # Load URLs and slice
    with open(LINKS_PATH) as f:
        repo_urls = json.load(f)
    total_repos = len(repo_urls)
    start = args.start
    end = args.end if args.end is not None else total_repos
    if start < 0 or start >= total_repos or end < start:
        print(f"Invalid range: start={start}, end={end}, total={total_repos}")
        return
    subset = repo_urls[start:end]
    total = len(subset)

    results_with = {}
    results_noext = []
    timeout = aiohttp.ClientTimeout(total=120)
    connector = aiohttp.TCPConnector(limit=20)

    async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout, connector=connector) as session:
        tasks = [asyncio.create_task(fetch_and_extract(session, url)) for url in subset]
        for idx, fut in enumerate(asyncio.as_completed(tasks), start=1):
            repo_url, links = await fut
            if links is None:
                continue
            if links:
                results_with[repo_url] = links
            else:
                results_noext.append(repo_url)
            print_progress(idx, total)

    out_dir = os.path.join(BASE_DIR, "extracted_urls")
    os.makedirs(out_dir, exist_ok=True)

    # Generate indexed output file names
    suffix = f"_{start}_{end}"
    out_with = os.path.join(out_dir, f"chrome_links{suffix}.json")
    out_noext = os.path.join(out_dir, f"chrome_links_noext{suffix}.json")

    # Report counts
    passed = len(results_with)
    no_ext = len(results_noext)
    print(f"\nRepos with manifest and links: {passed}/{total}. Repos with manifest but no links: {no_ext}/{total}.")

    # Write outputs
    with open(out_with, "w") as f:
        json.dump(results_with, f, indent=2)
    with open(out_noext, "w") as f:
        json.dump(results_noext, f, indent=2)
    print(f"Saved extension link JSON to {out_with} and no-link list to {out_noext}")

if __name__ == "__main__":
    asyncio.run(main())
