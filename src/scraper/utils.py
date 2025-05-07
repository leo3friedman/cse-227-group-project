import os
import json
import logging
import requests
import time
import sys

logging.basicConfig(
    level=logging.WARNING,
    filename="errors.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def write_json_to_file(filepath, json_data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(json_data, f, indent=4)


def read_json_file(filepath):
    with open(filepath) as f:
        return json.load(f)


def get_latest_file(path):
    files = [
        os.path.join(path, f)
        for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f))
    ]
    return max(files, key=os.path.getmtime) if files else None


def directory_contains_files(directory):
    return os.path.isdir(directory) and any(os.scandir(directory))


def print_progress(iteration, total, length=40):
    percent = int(100 * (iteration / float(total)))
    filled = int(length * iteration // total)
    bar = "=" * filled + "-" * (length - filled)
    sys.stdout.write(f"\r[{bar}] {percent}%")
    sys.stdout.flush()


def fetch_with_rety(url, params, headers, max_retries=5, request_timeout=5):
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

        logger.warning(f"Backing off. Attempt: {attempt}/{max_retries}...")
        time.sleep(delay)
        delay *= 2

    raise Exception("Max retries exceeded")
