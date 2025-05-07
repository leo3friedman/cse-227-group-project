import json
import os
import datetime
import time
import math
import argparse
from utils import (
    fetch_with_rety,
    write_json_to_file,
    get_latest_file,
    read_json_file,
    print_progress,
    directory_contains_files,
)

from extract_repo_urls import extract_urls


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


def find_buckets(url, query, min_size_in_kb=0, max_size_in_kb=1000000):
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


def bucket_fetch_repos(url, buckets_filepath, output_dir):
    buckets = read_json_file(buckets_filepath)
    print(f"Fetching {len(buckets)} buckets. This may take awhile...")

    start_time = time.time()
    total_items = sum(bucket.get("number_of_items") for bucket in buckets)
    items_found = 0

    for bucket_index, bucket in enumerate(buckets):
        query = bucket.get("query")
        repo_response_pages = fetch_paged_repos(url, query)
        for page, repo_json in repo_response_pages:
            filename = f"bucket_{bucket_index}_page_{page}.json"
            filepath = os.path.join(output_dir, filename)
            items_found += len(repo_json.get("items", []))
            write_json_to_file(filepath, repo_json)
            print_progress(items_found, total_items)
    elapsed_time = time.time() - start_time
    print(
        f"\nFound a total of {items_found} out of {total_items} items in {elapsed_time:.2f} seconds."
    )


def fetch_paged_repos(url, query):
    max_items_allowed_by_github = 1000
    items_per_page = 100
    upper_max_page_limit = max_items_allowed_by_github / items_per_page

    max_allowed_pages = upper_max_page_limit
    page = 1
    response_pages = []
    while page <= max_allowed_pages:
        params = get_params(query, page)
        headers = get_headers()
        response = fetch_with_rety(url, params, headers)
        response_json = response.json()

        total_items = response_json.get("total_count", max_items_allowed_by_github)
        pages_required = math.ceil(total_items / items_per_page)
        max_allowed_pages = min(pages_required, upper_max_page_limit)
        response_pages.append((page, response_json))
        page += 1

    return response_pages


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
    any_buckets_computed_yet = directory_contains_files(bucket_output_dir)
    
    should_calculate_buckets = not any_buckets_computed_yet or args.recalculate_buckets
    if should_calculate_buckets:
        bucket_filename = f"{str(datetime.datetime.now())}.json"
        bucket_filepath = os.path.join(bucket_output_dir, bucket_filename)
        all_buckets = []
        for bucket_query in queries:
            print(f"Calculating buckets for q={bucket_query}. This may take awhile...")

            buckets = find_buckets(
                url,
                bucket_query,
            )

            all_buckets += buckets

        write_json_to_file(bucket_filepath, all_buckets)

    buckets_file_to_scrape = (
        bucket_filepath
        if should_calculate_buckets
        else get_latest_file(bucket_output_dir)
    )

    scraped_repo_output_dir = os.path.join(
        this_directory, "scraped_repos", str(datetime.datetime.now())
    )

    bucket_fetch_repos(url, buckets_file_to_scrape, scraped_repo_output_dir)

    extracted_urls_output_filepath = os.path.join(
        this_directory, "extracted_urls", f"{datetime.datetime.now()}.json"
    )

    extract_urls(scraped_repo_output_dir, extracted_urls_output_filepath)
