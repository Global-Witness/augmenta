from typing import List, Tuple, Optional, Any, Union, Dict
import yaml
from pydantic_ai import format_as_xml

def format_xml(obj: Any, *, root_tag: str = "data", item_tag: str = "item", prefix: str = "") -> str:
    """Format data as XML using pydantic_ai's format_as_xml.
    
    This function provides a unified interface for XML formatting, supporting various Python objects
    including dictionaries, lists, tuples, and YAML strings.
    
    Args:
        obj: Object to format as XML. Can be:
            - List of tuples for docs (url, content)
            - YAML string or list for examples
            - Any other Python object supported by format_as_xml
        root_tag: Tag to use for the root element
        item_tag: Tag to use for list items
        prefix: Optional string to prefix the XML output (e.g. "## Examples")
    
    Returns:
        XML formatted string, optionally with prefix
    
    Examples:
        >>> # Format docs
        >>> docs = [("https://example.com", "content")]
        >>> print(format_xml(
        ...     [{"url": u, "content": c or "No content"} for u, c in docs],
        ...     root_tag="sources",
        ...     item_tag="source"
        ... ))
        <sources>
          <source>
            <url>https://example.com</url>
            <content>content</content>
          </source>
        </sources>
        
        >>> # Format examples
        >>> yaml_str = '''
        ... examples:
        ...   - input: test
        ...     output: result
        ... '''
        >>> print(format_xml(yaml.safe_load(yaml_str), prefix="## Examples"))
        ## Examples
        <examples>
          <example>
            <input>test</input>
            <output>result</output>
          </example>
        </examples>
    """
    if isinstance(obj, str):
        # Handle YAML strings
        try:
            obj = yaml.safe_load(obj)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
    
    # Generate the XML
    xml = format_as_xml(
        obj,
        root_tag=root_tag,
        item_tag=item_tag,
        indent="  ",
        include_root_tag=False
    )
    
    return f"{prefix}\n{xml}" if prefix else xml

def format_docs(scraped_content: List[Dict[str, str]]) -> str:
    """Format scraped content as XML."""
    sources = [
        {"url": item["url"], "content": item["content"].strip() or "No content extracted"}
        for item in scraped_content
    ]
    return format_xml(
        sources or [{"url": "none", "content": "No content extracted"}],
        root_tag="sources",
        item_tag="source"
    )

def format_examples(examples_yaml: Union[str, list]) -> str:
    """Format examples as XML with header."""
    if isinstance(examples_yaml, list):
        data = {"examples": examples_yaml}
    else:
        data = yaml.safe_load(examples_yaml)
    
    if not data or "examples" not in data:
        return ""
        
    # Validate examples structure
    for example in data["examples"]:
        if not isinstance(example, dict) or "input" not in example or "output" not in example:
            raise ValueError("Each example must contain 'input' and 'output' fields")
    
    return format_xml(data, prefix="## Examples")

def format_prompt(prompt_template: str, row_data: Dict[str, Any]) -> str:
    """Format a prompt template by replacing placeholders with row data.
    
    Args:
        prompt_template: Prompt template with {{placeholder}} syntax
        row_data: Dictionary containing values to replace placeholders
        
    Returns:
        Formatted prompt string
    """
    formatted = prompt_template
    for column, value in row_data.items():
        formatted = formatted.replace(f"{{{{{column}}}}}", str(value))
    return formatted