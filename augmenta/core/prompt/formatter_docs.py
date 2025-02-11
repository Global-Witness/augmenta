from typing import List, Tuple, Optional
from xml.sax.saxutils import escape

class DocumentFormatter:
    """Formats documents for prompt creation"""
    
    @staticmethod
    def format_docs(scraped_content: List[Tuple[str, Optional[str]]]) -> str:
        """Format scraped content into XML structure"""
        if not scraped_content:
            return "<documents>\n</documents>"

        # Filter out entries with None content
        valid_content = [(url, text) for url, text in scraped_content if text]

        # Build XML using list comprehension
        documents = [
            f'<document index="{i}">\n'
            f'<source>{escape(url)}</source>\n'
            f'<document_content>\n{escape(text)}\n</document_content>\n'
            f'</document>'
            for i, (url, text) in enumerate(valid_content, start=1)
        ]

        return f"<documents>\n{''.join(documents)}\n</documents>"