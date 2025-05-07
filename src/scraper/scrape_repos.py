import requests
import json
import os
import datetime
import time
import math
import argparse
import sys
import logging

logging.basicConfig(
    level=logging.ERROR,
    filename="errors.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def get_params(query, page=1):
    return {"q": query, "per_page": 100, "page": page}


def get_github_acess_token():
    this_directory = os.path.dirname(os.path.abspath(__file__))
    secret_filepath = os.path.join(this_directory, "secret.json")
    with open(secret_filepath) as json_file:
        json_data = json.load(json_file)
        github_access_token = json_data["github_access_token"]

    return github_access_token


def get_headers():
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {get_github_acess_token()}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def find_buckets(url, query, min_size_in_kb, max_size_in_kb):
    buckets = list()

    filtered_query = f"{query} size:{min_size_in_kb}..{max_size_in_kb}"
    total_items = items_returned(url, filtered_query)
    remaining_items = total_items

    while remaining_items > 0 and max_size_in_kb > 0:
        filtered_query = f"{query} size:{min_size_in_kb}..{max_size_in_kb}"
        amount_returned = items_returned(url, filtered_query)

        while amount_returned > 1000:
            min_size_in_kb = int((max_size_in_kb + min_size_in_kb) / 2)
            filtered_query = f"{query} size:{min_size_in_kb}..{max_size_in_kb}"
            amount_returned = items_returned(url, filtered_query)

        buckets.append(
            {
                "min_size_in_kb": min_size_in_kb,
                "max_size_in_kb": max_size_in_kb,
                "query": filtered_query,
                "number_of_items": amount_returned,
            }
        )
        remaining_items -= amount_returned
        max_size_in_kb = min_size_in_kb - 1
        min_size_in_kb = 0
        print_progress(total_items - remaining_items, total_items)

    total_found = sum(b.get("number_of_items", 0) for b in buckets)
    print(f"\nFound a total of {total_found} out of {total_items} items.")
    return buckets


def items_returned(url, query):
    params = get_params(query, 1)
    headers = get_headers()
    response = fetch_with_rety(url, params, headers)
    response_json = response.json()
    return response_json["total_count"]


def fetch_repos(url, queries):
    this_directory = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(
        this_directory, "scraped_repos", str(datetime.datetime.now())
    )

    max_items_allowed_by_github = 1000
    items_per_page = 100
    upper_max_page_limit = max_items_allowed_by_github / items_per_page

    for queryIndex, query in enumerate(queries):
        max_allowed_pages = upper_max_page_limit
        page = 1
        while page <= max_allowed_pages:
            print(f"querying page: {page} of queryIndex: {queryIndex}...")

            params = {"q": query, "per_page": items_per_page, "page": page}
            response = fetch_with_rety(url, params, get_headers())
            response_json = response.json()

            total_items = response_json.get("total_count", max_items_allowed_by_github)
            pages_required = math.ceil(total_items / items_per_page)
            max_allowed_pages = min(pages_required, upper_max_page_limit)

            filename = f"query_{queryIndex}_page_{page}.json"
            filepath = os.path.join(output_dir, filename)
            write_to_file(filepath, response_json)

            page += 1

    print(f"Extraction succeeded!\nWrote to directory: {output_dir}")


def fetch_with_rety(url, params, headers, max_retries=3, request_timeout=5):
    delay = 1
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url, params=params, headers=headers, timeout=request_timeout
            )

            if response.ok:
                return response
            else:
                logger.error(f"Request Error {response.status_code}: {response.text}")

        except requests.exceptions.Timeout:
            logger.error(
                f"Request Error: Request timed out after {request_timeout} seconds."
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error: {e}")

        logger.error(f"Backing off. Attempt: {attempt}/{max_retries}...")
        time.sleep(delay)
        delay *= 2

    raise Exception("Max retries exceeded")


def write_to_file(filepath, json_data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(json_data, f, indent=4)

def get_latest_file(path):
    files = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    return max(files, key=os.path.getmtime) if files else None

def print_progress(iteration, total, length=40):
    percent = int(100 * (iteration / float(total)))
    filled = int(length * iteration // total)
    bar = "=" * filled + "-" * (length - filled)
    sys.stdout.write(f"\r[{bar}] {percent}%")
    sys.stdout.flush()


if __name__ == "__main__":
    this_directory = os.path.dirname(os.path.abspath(__file__))
    url = "https://api.github.com/search/repositories"
    queries = [
        "chromewebstore.google.com in:readme",
        "chrome.google.com/webstore in:readme",
    ]

    parser = argparse.ArgumentParser()
    parser.add_argument("--recalculate_buckets", action="store_true")
    args = parser.parse_args()

    bucket_output_dir = os.path.join(this_directory, "buckets")
    any_buckets_computed_yet = any(os.scandir(bucket_output_dir))
    if args.recalculate_buckets or not any_buckets_computed_yet:
        bucket_filename = f"{str(datetime.datetime.now())}.json"
        bucket_filepath = os.path.join(bucket_output_dir, bucket_filename)
        all_buckets = []
        for queryIndex, bucket_query in enumerate(queries):
            print(
                f"Calculating buckets for query {queryIndex}. This may take awhile..."
            )
            starting_min_in_kb = 0
            starting_max_in_kb = 1000000

            buckets = find_buckets(
                url, bucket_query, starting_min_in_kb, starting_max_in_kb
            )

            all_buckets += buckets

        write_to_file(bucket_filepath, all_buckets)
    else:
    
    # recent_buckets_file = get_latest_file(bucket_output_dir)
    # with open(recent_buckets_file) as f:
    #     buckets = json.
        fetch_repos(url, queries)
