import unittest
from cws_page_fetcher import extract_metadata
from utils import read_html_file, read_txt_file
import os
from bs4 import BeautifulSoup
import re


class TestCwsPageFetcher(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")

    def test_is_supported_on_unsupported_html(self):
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


if __name__ == "__main__":
    unittest.main()
