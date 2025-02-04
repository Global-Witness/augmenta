from typing import List, Tuple, Optional
from xml.sax.saxutils import escape


def prepare_docs(scraped_content: List[Tuple[str, Optional[str]]]) -> str:
    """
    Prepare and trim the scraped content for processing.

    Args:
        scraped_content (List[Tuple[str, Optional[str]]]): List of tuples containing URL and text content.

    Returns:
        str: The prepared and trimmed content in XML format.

    Raises:
        ValueError: If an unsupported model is provided.
    """
    
    scraped_content = [(url, text) for url, text in scraped_content if text is not None]
    
    xml_content = "<documents>\n"
    for index, (url, text) in enumerate(scraped_content, start=1):
        if text is not None:
            xml_content += f"<document index=\"{index}\">\n"
            xml_content += f"<source>{escape(url)}</source>\n"
            xml_content += "<document_content>\n"
            xml_content += escape(text)
            xml_content += "\n</document_content>\n"
            xml_content += "</document>\n"
    xml_content += "</documents>"
    return xml_content

