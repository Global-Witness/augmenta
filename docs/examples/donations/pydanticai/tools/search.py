def web_search_ddg(query: str) -> str:
    """
    Performs a duckduckgo web search based on your query (think a Google search) then returns the top search results.
    
    Args:
        query: The search query to perform.
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError as e:
        raise ImportError(
            "You must install package `duckduckgo_search` to run this tool: for instance run `pip install duckduckgo-search`."
        ) from e
    
    max_results = 10
    ddgs = DDGS()
    
    results = ddgs.text(query, max_results=max_results)
    if len(results) == 0:
        raise Exception("No results found! Try a less restrictive/shorter query.")
    
    postprocessed_results = [f"[{result['title']}]({result['href']})\n{result['body']}" for result in results]
    return "## Search Results\n\n" + "\n\n".join(postprocessed_results)