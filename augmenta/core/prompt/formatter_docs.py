"""Document formatting utilities for prompt creation."""

from typing import List, Tuple, Optional
from xml.sax.saxutils import escape

class DocumentFormatter:
    """Formats documents for prompt creation using XML structure."""
    
    @staticmethod
    def format_docs(scraped_content: List[Tuple[str, Optional[str]]]) -> str:
        """
        Format scraped content into XML structure.
        
        Args:
            scraped_content: List of tuples containing (url, content) pairs
            
        Returns:
            str: Formatted XML string containing documents
            
        Example:
            >>> content = [("http://example.com", "Some text")]
            >>> DocumentFormatter.format_docs(content)
            '<documents>
                <document index="1">
                    <source>http://example.com</source>
                    <document_content>Some text</document_content>
                </document>
            </documents>'
        """
        if not scraped_content:
            return "<documents></documents>"

        # Filter out entries with None content and format as XML
        documents = [
            f'<document index="{i}">'
            f'<source>{escape(url)}</source>'
            f'<document_content>{escape(text)}</document_content>'
            f'</document>'
            for i, (url, text) in enumerate(
                ((url, text) for url, text in scraped_content if text),
                start=1
            )
        ]

        return f"<documents>{''.join(documents)}</documents>"