import requests
import json
import os
import datetime
import time
import math


def fetch_with_rety(url, params, headers, max_retries=3):
    delay = 1
    for attempt in range(max_retries):
        response = requests.get(url, params=params, headers=headers)
        if response.ok:
            return response

        else:
            print(f"Error {response.status_code}: {response.text}")

        print(f"Request failed, Backing off. Attempt {attempt}/{max_retries}...")
        time.sleep(delay)
        delay *= 2

    raise Exception("Max retries exceeded")


def fetch_repos():
    with open("secret.json") as json_file:
        json_data = json.load(json_file)
        github_access_token = json_data["github_access_token"]

    url = "https://api.github.com/search/repositories"

    queries = [
        "chromewebstore.google.com in:readme",
        "chrome.google.com/webstore in:readme",
    ]

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_access_token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    max_items_allowed_by_github = 1000
    items_per_page = 100
    upper_max_page_limit = max_items_allowed_by_github / items_per_page

    output_dir = os.path.join(
        os.getcwd(), "scraped_repos", str(datetime.datetime.now())
    )

    for queryIndex, query in enumerate(queries):
        max_allowed_pages = upper_max_page_limit
        page = 1
        while page <= max_allowed_pages:
            print(f"querying page: {page} of queryIndex: {queryIndex}...")

            params = {"q": query, "per_page": items_per_page, "page": page}
            response = fetch_with_rety(url, params, headers)
            response_json = response.json()

            total_items = response_json.get("total_count", max_items_allowed_by_github)
            pages_required = math.ceil(total_items / items_per_page)
            max_allowed_pages = min(pages_required, upper_max_page_limit)

            filename = f"query_{queryIndex}_page_{page}.json"
            filepath = os.path.join(output_dir, filename)
            write_to_file(filepath, response_json)

            page += 1

    print(f"Extraction succeeded!\nWrote to directory: {output_dir}")


def write_to_file(filepath, json_data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(json_data, f, indent=4)


if __name__ == "__main__":
    fetch_repos()
