# Searching with Augmenta

Augmenta supports several search engines out of the box. It will search for the `query_col` you specify, extract the links, and return the text from those links.

Some search engines have a rate limit, meaning they will only allow a certain number of searches in a given time period. You can configure Augmenta to respect this rate limit by setting the `rate_limit` parameter in your configuration file.

## DuckDuckGo

DuckDuckGo is a privacy-focused search engine, and the simplest to get started with, as you don't need an API key.

```yaml
search:
  engine: duckduckgo
  results: 10
  region: uk-en # optional, one of https://github.com/deedy5/duckduckgo_search?tab=readme-ov-file#regions
  safesearch: off # on, moderate, off. Defaults to "moderate".
```

In my experience, DuckDuckGo can be unreliable and will often refuse to return results. Additionally, the search results are sometimes subpar. I recommend you only use it for testing.

## Brave

Brave is another privacy-focused search engine. You will need to [sign up for a free API key](https://brave.com/search/api/), which will give you 2,000 free searches per month, or you can pay for more.

```yaml
search:
  engine: brave
  country: GB  # optional, one of https://api-dashboard.search.brave.com/app/documentation/web-search/codes#country-codes
  results: 10
  rate_limit: 2 # brave has a rate limit
```

To use Brave, you will need to set the `BRAVE_API_KEY` environment variable to your API key.

```
BRAVE_API_KEY=XXXXX
```

## Google

Google is the most powerful and highest-quality search engine, but it is limited to [just 100 free searches per day](https://developers.google.com/custom-search/v1/overview). Additional requests cost $5 per 1000 queries, up to 10k queries per day.

```yaml
search:
  engine: google
  results: 10
  lr: lang_ro # optional, restricts results to pages in the specified language
```

You can find the full list of optional parameters [here](https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list).

You will need an API key and a custom search ID (CX) to use Google search. Get them by following the instructions [here](https://developers.google.com/custom-search/v1/overview), and save them to your `.env`.

```
GOOGLE_API_KEY=XXXXX
GOOGLE_CX=XXXXX
```

Google provides the best search results, but it is also by far the most expensive.

## Oxylabs

Oxylabs is a proxy provider that offers a search API. You will need to [sign up for an account](https://oxylabs.io/products/proxy-api) and get an API key.

*instuctions coming soon*