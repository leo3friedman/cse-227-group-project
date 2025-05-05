# cse-227-group-project

## GitHub Repository Scraper

#### Description:

A tool to scrape the urls of Github repositories that are likely to host the source code of Chrome Extensions.

#### Run Steps:

1. Create a fine grained personal access token (no permissions are required). [View Steps Here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)
2. Create a `secret.json` file in `./src/scraper` with the following content:

```
{
  "github_access_token": <YOUR-TOKEN>
}
```

3. Run the scraper via `python3 src/scraper/scrape_repos.py`
4. Run the url extractor via `python3 src/scraper/extract_repo_urls.py`
