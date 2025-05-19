# cse-227-group-project

## GitHub Repository Scraper

A tool to scrape the urls of Github repositories that are likely to host the source code of Chrome Extensions.

### Prerequisites:

1. Create a fine grained personal access token (no permissions are required). [View Steps Here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)
2. Create a `secret.json` file in `./src/scraper` with the following content:

   ```
   {
     "github_access_token": <YOUR-TOKEN>
   }
   ```

### Run instructions

Run the scraper via `python3 src/scraper/scrape_repos.py`.

- Buckets will be calulated if `./src/scraper/buckets` does not exist or is empty.
- To force buckets to be recalculated pass in the flag: `--recalculate_buckets`.
- By default the program will use the most recent file in `./src/scraper/buckets`.

To extract the chrome webstore urls from the repo urls, run:
```
python3 src/scraper/extract_chromex.py --start <start_index> --end <end_index>
```
To generate the json files with github repos linked with their extension urls
(Due to the maximum request constraint hourly from the github API, please run around 5000 requests hourly)

After scraping all the data, run:
```
python3 src/scraper/combine_chrome_links.py
```

### Output

All the scraped GitHub urls can be found in `./src/scraper/extracted_urls`

- All the raw json responses can be found in `./src/scraper/scraped_repos`
- Any bucket files can be found in `./src/scraper/buckets`

After running combine_chrome_links.py, there will be 3 json files generated:
- chrome_links.json: All the repo links with manifest.json included (a key component for chrome extensions) and a chrome webstore link to its extension
- chrome_links_noext.json: All the repo links with manifest.json included but without a chrome webstore link (or a broken link)
- chrome_links_remaining.json: All the remaining repo links (without manifest.json)
