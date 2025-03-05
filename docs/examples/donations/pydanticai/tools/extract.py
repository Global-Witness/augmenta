def visit_webpage(url: str) -> str:
    """
    Visits a webpage at the given url and reads its content as a markdown string. Use this to browse webpages.
    
    Args:
        url: The url of the webpage to visit.
    """
    try:
        from trafilatura import fetch_url, extract
    except ImportError as e:
        raise ImportError(
            "You must install `trafilatura` to run this tool"
        ) from e
    
    downloaded = fetch_url(url)
    result = extract(downloaded, output_format="markdown")
    
    return result