from trafilatura import fetch_url, extract
from typing import List

def extract_url(source):
    downloaded = fetch_url(source)
    result = extract(downloaded, output_format="markdown")
    return result

def extract_urls(urls: List[str]):
    results = []
    for url in urls:
        results.append((url, extract_url(url)))
    return results
