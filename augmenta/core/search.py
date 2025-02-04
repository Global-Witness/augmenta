from duckduckgo_search import DDGS
from brave import Brave
from typing import List

def search_web(query: str, results: int = 5, engine: str = "brave") -> List[str]:
    """
    Search the web for a query and return valid URLs.
    
    Args:
        query (str): Search query.
        results (int): Number of results to return per page.
        engine (str): Either "duckduckgo" or "brave".

    Returns:
        List[str]: List of valid URLs from the search results.
    """

    if engine == "duckduckgo":
        results = DDGS().text(query, max_results=results)
        results_href = [result['href'] for result in results if 'href' in result]
        
    elif engine == "brave":
        brave = Brave()
        results = brave.search(q=query, count=results)
        results_href = [str(item['url']) for item in results.web_results]

    return results_href
