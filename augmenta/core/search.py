from brave import AsyncBrave
from typing import List

async def search_web(query: str, results: int = 5, engine: str = "brave") -> List[str]:
    """
    Search the web for a query and return valid URLs.
    
    Args:
        query (str): Search query.
        results (int): Number of results to return per page.
        engine (str): Currently only supports "brave".

    Returns:
        List[str]: List of valid URLs from the search results.
    """
    if engine == "brave":
        brave = AsyncBrave()
        search_results = await brave.search(q=query, count=results)
        return [str(item['url']) for item in search_results.web_results]
    else:
        raise ValueError("Invalid search engine. Currently only 'brave' is supported.")