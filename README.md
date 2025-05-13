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

After running the scaper, run:
```
python3 src/scraper/extract_chromex.py --end 10000
python3 src/scraper/extract_chromex.py --start 10000
```
To generate the json files with github repos linked with their extension urls
(Due to the maximum request constraint hourly from the github API, please run the second command an hour after the first command)

### Output

All the scraped GitHub urls can be found in `./src/scraper/extracted_urls`

- All the raw json responses can be found in `./src/scraper/scraped_repos`
- Any bucket files can be found in `./src/scraper/buckets`
