import json
import os
from utils import write_json_to_file

def extract_urls(input_directory, output_filepath):
    output_urls = []
    for filename in os.listdir(input_directory):
        filepath = os.path.join(input_directory, filename)
        with open(filepath) as f:
            json_data = json.load(f)
            items = json_data.get("items")
            repository_urls = [item.get("html_url") for item in items]
            output_urls += repository_urls

    write_json_to_file(output_filepath, output_urls)
    print(f"Extraction succeeded!\nWrote to file: {output_filepath}")

