import json
import os
import datetime


def extract_repo_urls():
    scrape_dir = os.path.join(os.getcwd(), "scraped_repos")
    directories = [
        name
        for name in os.listdir(scrape_dir)
        if os.path.isdir(os.path.join(scrape_dir, name))
    ]
    output_filepath = os.path.join(
        os.getcwd(), "analyzed_repos", f"{datetime.datetime.now()}.json"
    )
    newest_scape_directory_name = directories[-1]
    output_urls = []
    newest_scrape_directory = os.path.join(scrape_dir, newest_scape_directory_name)
    for filename in os.listdir(newest_scrape_directory):
        filepath = os.path.join(newest_scrape_directory, filename)
        with open(filepath) as f:
            json_data = json.load(f)
            items = json_data.get("items")
            repository_urls = [item.get("html_url") for item in items]
            output_urls += repository_urls

    write_to_file(output_filepath, output_urls)
    print(f"Extraction succeeded!\nWrote to file: {output_filepath}")


def write_to_file(filepath, json_data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(json_data, f, indent=4)


if __name__ == "__main__":
    extract_repo_urls()
