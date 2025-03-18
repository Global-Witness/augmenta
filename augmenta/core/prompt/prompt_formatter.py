from typing import List, Tuple, Optional, Any
import yaml
from pydantic_ai.format_as_xml import format_as_xml

def format_docs(scraped_content: List[Tuple[str, Optional[str]]]) -> str:
    """Formats scraped content as markdown with headers and separators between sources.
    
    Args:
        scraped_content: A list of tuples containing (url, content)
        
    Returns:
        A markdown formatted string containing the content from each source,
        with headers and separators between different sources.
        
    Example:
        >>> content = [
        ...     ("https://example.com", "Some content here..."),
        ...     ("https://example.org", None)
        ... ]
        >>> print(format_docs(content))
        # Content from https://example.com
        
        Some content here...
        
        ---
        # Content from https://example.org
        
        No content extracted
    """
    formatted_sections = []
    for url, content in scraped_content:
        formatted_sections.extend([
            f"# Content from {url}",
            ""
        ])
        
        if content:
            formatted_sections.extend([
                content.strip(),
                "",
                "---"
            ])
        else:
            formatted_sections.extend([
                "No content extracted",
                "",
                "---"
            ])
    
    return "\n".join(formatted_sections[:-1] if formatted_sections else ["No content extracted"])

def format_examples(examples_yaml: str | list) -> str:
    """Formats YAML examples or list into XML structure"""
    try:
        if isinstance(examples_yaml, str):
            data = yaml.safe_load(examples_yaml)
        else:
            data = {'examples': examples_yaml}  # Wrap list in expected structure
            
        if not data or 'examples' not in data:
            return ""
        
        examples = []
        for example in data['examples']:
            if not isinstance(example, dict) or 'input' not in example or 'output' not in example:
                raise ValueError("Each example must contain 'input' and 'output' fields")
            
            # Format each example as its own XML structure
            examples.append({
                'input': str(example['input']),
                'ideal_output': example['output']
            })
        
        # Use format_as_xml to create the final XML structure
        xml = format_as_xml(
            examples,
            root_tag='examples',
            item_tag='example',
            indent='  '
        )
        
        return f"## Examples\n{xml}"
        
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML format: {e}")