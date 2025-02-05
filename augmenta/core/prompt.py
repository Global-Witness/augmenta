from typing import List, Tuple, Optional
from xml.sax.saxutils import escape

DocumentContent = List[Tuple[str, Optional[str]]]  # Type alias for better readability

def prepare_docs(scraped_content: DocumentContent) -> str:
    """
    Prepares scraped content by converting it into a structured XML format.
    Filters out entries with None content and escapes special characters.

    Args:
        scraped_content: List of tuples containing (URL, content) pairs.
                        Content may be None for failed scrapes.

    Returns:
        A formatted XML string containing the documents with their sources.

    Example:
        >>> content = [("http://example.com", "Some text"), ("http://test.com", None)]
        >>> prepare_docs(content)
        '<documents>
           <document index="1">
             <source>http://example.com</source>
             <document_content>Some text</document_content>
           </document>
         </documents>'
    """
    if not scraped_content:
        return "<documents></documents>"

    # Filter out entries with None content
    valid_content = [(url, text) for url, text in scraped_content if text]

    # Build XML using list comprehension for better performance
    documents = [
        f'<document index="{i}">\n'
        f'<source>{escape(url)}</source>\n'
        f'<document_content>\n{escape(text)}\n</document_content>\n'
        f'</document>'
        for i, (url, text) in enumerate(valid_content, start=1)
    ]

    return f"<documents>\n{''.join(documents)}\n</documents>"