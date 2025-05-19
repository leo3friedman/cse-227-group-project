import unittest
from cws_page_fetcher import extract_metadata
from utils import read_html_file, read_txt_file
import os
from bs4 import BeautifulSoup
import re


class TestCwsPageFetcher(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")

    def test_parser(self):
        dark_reader_filepath = os.path.join(self.fixtures_dir, "dark-reader-cws.html")
        dark_reader_html = read_html_file(dark_reader_filepath)
        dark_reader_soup = BeautifulSoup(dark_reader_html, "html.parser")
        dark_reader_overview_filepath = os.path.join(
            self.fixtures_dir, "dark-reader-cws-overview.txt"
        )
        dark_reader_overview = read_txt_file(dark_reader_overview_filepath)
        stripped_overview = re.sub(r"\s+", "", dark_reader_overview)
        self.assertDictEqual(
            extract_metadata(dark_reader_soup),
            {
                "user_count": 6000000,
                "rating": 4.7,
                "rating_count": 12300,
                "version": "4.9.106",
                "size": "781KiB",
                "overview": stripped_overview,
            },
        )

    def test_parser_2(self):
        google_scraper_filepath = os.path.join(
            self.fixtures_dir, "google-scraper-cws.html"
        )
        google_scraper_html = read_html_file(google_scraper_filepath)
        google_scraper_soup = BeautifulSoup(google_scraper_html, "html.parser")
        google_scraper_overview_filepath = os.path.join(
            self.fixtures_dir, "google-scraper-cws-overview.txt"
        )
        google_scraper_overview = read_txt_file(google_scraper_overview_filepath)
        stripped_overview = re.sub(r"\s+", "", google_scraper_overview)
        self.assertDictEqual(
            extract_metadata(google_scraper_soup),
            {
                "user_count": 96,
                "rating": 3.0,
                "rating_count": 1,
                "version": "1.0.1",
                "size": "6.09KiB",
                "overview": stripped_overview,
            },
        )


if __name__ == "__main__":
    unittest.main()
