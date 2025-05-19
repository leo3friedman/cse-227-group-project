from bs4 import BeautifulSoup
import argparse
import re
from utils import fetch_with_rety, read_json_file, write_json_to_file, write_html_file


def extract_html(url: str):
    response = fetch_with_rety(url, params=None, headers=None)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch page: {response.status_code}")

    page = response.text
    soup = BeautifulSoup(page, "html.parser")
    for script in soup.find_all("script"):
        script.decompose()
    body = soup.find("body")
    return body


def extract_users(soup):
    user_count_div_class = "F9iKBc"
    user_count_div = soup.find("div", class_=user_count_div_class)
    if user_count_div:
        inner_text = user_count_div.get_text()
        match = re.search(r"([\d,]+) user[s]?", inner_text)
        if match:
            return int(match.group(1).replace(",", ""))
    return None


def extract_rating(soup):
    rating_span_class = "Vq0ZA"
    rating_span = soup.find("span", class_=rating_span_class)
    if rating_span:
        inner_text = rating_span.get_text()
        match = re.search(r"([\d.]+)", inner_text)
        if match:
            return float(match.group(1))
    return None


def extract_rating_count(soup):
    rating_count_p_class = "xJEoWe"
    rating_count_p = soup.find("p", class_=rating_count_p_class)
    if rating_count_p:
        inner_text = rating_count_p.get_text()
        match = re.search(r"(\d+(\.\d)?[K]?) rating[s]?", inner_text)
        if match:
            matched_rating_count = match.group(1)
            if "K" in matched_rating_count:
                return int(float(matched_rating_count.replace("K", "")) * 1000)
            else:
                return int(matched_rating_count)
    return None


def extract_version(soup):
    version_div_class = "N3EXSc"
    version_div = soup.find("div", class_=version_div_class)
    if version_div:
        return version_div.get_text().strip()


def extract_size(soup):
    size_li_class = "ZbWJPd ZSMSLb"
    size_li = soup.find("li", class_=size_li_class)
    if size_li:
        size_li_chilren = size_li.find_all(recursive=False)
        if len(size_li_chilren) == 2:
            size_div = size_li_chilren[1]
            if size_div:
                return size_div.get_text().strip()


def extract_overview(soup):
    overview_div_class = "RNnO5e"
    overview_div = soup.find("div", class_=overview_div_class)
    if overview_div:
        overview_text = overview_div.get_text()
        return re.sub(r"\s+", "", overview_text)
    return None


def extract_metadata(soup):
    metadata = dict()
    metadata["user_count"] = extract_users(soup)
    metadata["rating"] = extract_rating(soup)
    metadata["rating_count"] = extract_rating_count(soup)
    metadata["version"] = extract_version(soup)
    metadata["size"] = extract_size(soup)
    metadata["overview"] = extract_overview(soup)
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch and save a rendered Chrome Web Store page as HTML."
    )

    parser.add_argument(
        "input_path",
        type=str,
        help="Path of the input json file containing the URLs to scrape",
    )

    parser.add_argument(
        "output_path",
        type=str,
        help="Output file path to save the parsed HTML",
    )

    parser.add_argument(
        "--failed_urls_output_path",
        type=str,
        help="Output file path to save the URLs that failed to scrape",
    )

    args = parser.parse_args()

    urls_to_scrape = read_json_file(args.input_path)

    scraped_metadata = list()
    failed_urls = list()

    for url_pair in urls_to_scrape:
        repo_url = list(url_pair.keys())[0]
        cws_urls = url_pair[repo_url]
        scrape_result = dict()
        scrape_result["repo_url"] = repo_url
        scrape_result["scraped_metadata"] = list()
        for cws_url in cws_urls:
            try:
                print(f"Fetching {cws_url}")
                soup = extract_html(cws_url)
                metadata = extract_metadata(soup)
                metadata["cws_url"] = cws_url
                scrape_result["scraped_metadata"].append(metadata)
            except Exception as e:
                print(f"Failed to fetch {cws_url}: {e}")
                failed_urls.append(cws_url)
        scraped_metadata.append(scrape_result)

    write_json_to_file(args.output_path, scraped_metadata)

    if args.failed_urls_output_path:
        write_json_to_file(args.failed_urls_output_path, failed_urls)
